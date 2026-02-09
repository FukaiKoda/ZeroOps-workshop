import docker
import os
import tarfile
from io import BytesIO
from pathlib import Path

class Grader:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Error connecting to Docker: {e}")
            self.client = None
        
        self.runner_path = Path(__file__).parent.parent.parent.parent / "docker" / "python-runner"

    def ensure_image_exists(self, tag: str, path: Path):
        """Ensures the runner image is built."""
        if not self.client:
            return False
            
        try:
            self.client.images.get(tag)
            return True
        except docker.errors.ImageNotFound:
            print(f"Building image {tag} from {path}...")
            try:
                self.client.images.build(path=str(path), tag=tag, rm=True)
                return True
            except Exception as e:
                print(f"Failed to build image {tag}: {e}")
                return False

    def run_python(self, code: str) -> tuple[int, str]:
        """
        Runs python code in a container and returns (exit_code, output).
        Does NOT judge correctness.
        """
        if not self.client:
            return -1, "Docker client not available. Is Docker running?"

        image_tag = "zeroops-python-runner"
        if not self.ensure_image_exists(image_tag, self.runner_path):
            return -1, "Failed to build runner image."

        try:
            container = self.client.containers.create(
                image_tag,
                command="python main.py",
                network_mode="none", # Internet isolation
                mem_limit="128m",
                cpu_period=100000,
                cpu_quota=50000, # 0.5 CPU
            )
            
            # Prepare tar archive for copy
            pw_tar_stream = BytesIO()
            with tarfile.open(fileobj=pw_tar_stream, mode='w') as tar:
                # Add file
                info = tarfile.TarInfo(name='main.py')
                info.size = len(code.encode('utf-8'))
                tar.addfile(info, BytesIO(code.encode('utf-8')))
            
            pw_tar_stream.seek(0)
            
            # Copy file to container
            container.put_archive('/app', pw_tar_stream)
            
            # Start
            container.start()
            
            # Wait for finish
            result = container.wait(timeout=5) # 5s timeout
            
            logs = container.logs().decode('utf-8').strip()
            container.remove()
            
            return result['StatusCode'], logs

        except Exception as e:
            return -1, f"Sandbox Error: {e}"

    def build_dockerfile(self, dockerfile_content: str) -> tuple[bool, str]:
        """Attempts to build a Dockerfile to verify its validity."""
        if not self.client:
            return False, "Docker client not available."

        # Create a file-like object for the build context
        f = BytesIO(dockerfile_content.encode('utf-8'))
        
        try:
            self.client.images.build(fileobj=f, rm=True, tag="zeroops-test-build")
            return True, "Dockerfile is valid and built successfully."
        except docker.errors.BuildError as e:
            # Extract build log error if possible
            error_log = ""
            for line in e.build_log:
                if 'stream' in line:
                    error_log += line['stream']
                if 'error' in line:
                    error_log += line['error']
            return False, f"Build Failed: {error_log.strip()}"
        except Exception as e:
            return False, f"Validation Error: {str(e)}"

    def get_expected_output(self, exercise_path: Path) -> str:
        """
        Gets expected output for an exercise.
        Checks for 'expected_output.txt' in the exercise dir.
        If missing, looks for 'solution.py', runs it, and saves the output.
        """
        output_file = exercise_path / "expected_output.txt"
        solution_file = exercise_path / "solution.py"
        
        # Check if cache is valid (exists and is newer than solution)
        if output_file.exists():
            try:
                if solution_file.exists() and solution_file.stat().st_mtime > output_file.stat().st_mtime:
                    # Solution changed, invalidate cache
                    pass
                else:
                    with open(output_file, "r") as f:
                        return f.read().strip()
            except Exception as e:
                print(f"Error reading/validating cache {output_file}: {e}")
        
        # Generate cache
        if not solution_file.exists():
             return "" # No solution defined
        
        try:
            with open(solution_file, "r") as f:
                code = f.read()
            
            # Run solution (trusting our own code)
            exit_code, output = self.run_python(code) 
            
            if exit_code == 0:
                 # Success, cache the output
                 with open(output_file, "w") as f:
                     f.write(output)
                 return output
                 
            return "" # Execution failed
            
        except Exception as e:
            print(f"Error generating solution: {e}")
            return ""
