
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Tuple, Optional

class LocalGrader:
    @staticmethod
    def execute_script(script_content: str, nonce: str, target_dir: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Executes the provided python script content in a separate process.
        The script is expected to print the result to stdout or exit with a specific code.
        If target_dir is provided, the script runs in that directory.
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Write the grader script
            check_file = tmp_path / "check.py"
            check_file.write_text(script_content)
            
            # Create a runner script
            # We need to pass the 'code' to it? 
            # In the new design, the client runs the check against the LOCAL SYSTEM.
            # So `code` might be the path to the files or just empty if checking system state.
            
            runner_content = """
import sys
import check
from pathlib import Path

# All exercises now use the standard signature: grade(code: str, exercise_path: Path)
cwd = Path.cwd()

# Collect all YAML content from current directory
code = ""
yaml_files = sorted([f for f in cwd.glob("*.yaml")] + [f for f in cwd.glob("*.yml")])
if yaml_files:
    content_list = []
    for f in yaml_files:
        try:
            content_list.append(f.read_text())
        except Exception:
            pass
    code = "\\n---\\n".join(content_list)

try:
    success, message = check.grade(code, cwd)

    if success:
        print("SUCCESS")
        print(message)
        sys.exit(0)
    else:
        print("FAILURE")
        print(message)
        sys.exit(1)
except Exception as e:
    print("ERROR")
    print(str(e))
    sys.exit(1)
"""
            runner_file = tmp_path / "runner.py"
            runner_file.write_text(runner_content)
            
            # Execute
            try:
                # We run via subprocess to capture output and exit code
                result = subprocess.run(
                    [sys.executable, str(runner_file)],
                    cwd=str(target_dir) if target_dir else os.getcwd(), # Run in user's exercise directory so it can find files/pods
                    capture_output=True,
                    text=True,
                    timeout=30 # 30 seconds timeout
                )
                
                output = result.stdout + result.stderr
                success = result.returncode == 0
                
                # Filter 'SUCCESS' / 'FAILURE' lines if needed, or just return the output
                # The runner prints SUCCESS/FAILURE then the message.
                
                lines = output.strip().splitlines()
                if not lines:
                     return False, "No output from grader."

                # Simple parsing based on our runner
                if lines[0] == "SUCCESS":
                    return True, "\n".join(lines[1:])
                elif lines[0] == "FAILURE":
                    return False, "\n".join(lines[1:])
                else:
                    return False, output
                    
            except subprocess.TimeoutExpired:
                return False, "Grading timed out."
            except Exception as e:
                return False, f"Execution error: {e}"
