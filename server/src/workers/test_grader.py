#!/usr/bin/env python3
"""
Test script for the Grader worker.

This script tests the Docker runner and grader independently,
without requiring the full server/client setup.

Run: python test_grader.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from schemas import (
    FileSubmission,
    WorkerJob,
    ExerciseMeta,
    TechStack,
    ExerciseStatus,
)
from workers.docker_runner import DockerRunner, create_temp_student_dir
from workers.grader import Grader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_docker_connection():
    """Test 1: Verify Docker daemon is accessible."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Docker Connection")
    logger.info("="*60)

    try:
        runner = DockerRunner()
        if runner.health_check():
            logger.info("✅ Docker daemon is healthy")
            return True
        else:
            logger.error("❌ Docker health check failed")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Docker: {e}")
        logger.info("   Make sure Docker daemon is running: `docker daemon` or `systemctl start docker`")
        return False


def test_simple_container():
    """Test 2: Run a simple alpine container."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Simple Container Execution")
    logger.info("="*60)

    try:
        runner = DockerRunner()
        
        logger.info("📦 Running: alpine echo 'Hello from Docker'")
        output, exit_code = runner.run_container(
            image="alpine:latest",
            command=["echo", "Hello from Docker"],
            mount_source="/tmp",
            mount_target="/tmp",
            timeout_seconds=5,
        )

        logger.info(f"Output: {output.strip()}")
        logger.info(f"Exit code: {exit_code}")

        if exit_code == 0 and "Hello from Docker" in output:
            logger.info("✅ Simple container test passed")
            return True
        else:
            logger.error("❌ Simple container test failed")
            return False

    except Exception as e:
        logger.error(f"❌ Container test failed: {e}")
        return False


def test_python_container():
    """Test 3: Run a Python container with mounted code."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Python Container with Code Mount")
    logger.info("="*60)

    try:
        runner = DockerRunner()

        # Create a simple Python file
        python_code = """
print("✅ Python code executed!")
print(f"1 + 1 = {1 + 1}")
"""
        files = {"test.py": python_code}
        temp_dir = create_temp_student_dir(files)

        logger.info(f"📝 Created temp dir: {temp_dir}")
        logger.info("📦 Running: python /student/test.py")

        output, exit_code = runner.run_container(
            image="python:3.11-alpine",
            command=["python", "/student/test.py"],
            mount_source=temp_dir,
            mount_target="/student",
            timeout_seconds=10,
        )

        logger.info(f"Output:\n{output}")
        logger.info(f"Exit code: {exit_code}")

        if exit_code == 0:
            logger.info("✅ Python container test passed")
            return True
        else:
            logger.error("❌ Python container test failed")
            return False

    except Exception as e:
        logger.error(f"❌ Python container test failed: {e}")
        return False


def test_grader_with_python():
    """Test 4: Full grading pipeline with a Python exercise."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Full Grader Pipeline (Python)")
    logger.info("="*60)

    try:
        # Create a fake exercise metadata
        exercise = ExerciseMeta(
            id="test_python",
            slug="test-python",
            title="Test Python Exercise",
            points=100,
            stack=TechStack.PYTHON,
            allowed_files=["main.py"],
            docker_image="python:3.11-alpine",
            grader_script_path="test.py",  # Dummy path
            mount_path="/student",
            timeout_seconds=10,
        )

        # Create a simple grader script (returns JSON)
        grader_script = """
import json
result = {"status": "success", "score": 100}
print(json.dumps(result))
"""

        # Create a simple student file
        student_code = """
def add(a, b):
    return a + b

print("Code submitted!")
"""

        # Create file submissions
        files = [
            FileSubmission(filename="main.py", content=student_code),
            FileSubmission(filename="grader/test.py", content=grader_script),
        ]

        # Create a WorkerJob
        job = WorkerJob(
            job_id="test-job-001",
            user_id="test_user",
            exercise=exercise,
            files=files,
            docker_image="python:3.11-alpine",
            grader_script_path="test.py",
            mount_path="/student",
            timeout_seconds=10,
        )

        logger.info(f"📋 Created WorkerJob: {job.job_id}")
        logger.info(f"   Exercise: {job.exercise.slug}")
        logger.info(f"   Files: {[f.filename for f in files]}")

        # Run grader
        grader = Grader()
        logger.info("🎯 Starting grader...")
        result = grader.grade_submission(job)

        logger.info(f"\n📊 Grading Result:")
        logger.info(f"   Status: {result.status.value}")
        logger.info(f"   Score: {result.score}")
        logger.info(f"   Exit Code: {result.exit_code}")
        logger.info(f"   Output:\n{result.output_log}")

        if result.status == ExerciseStatus.SUCCESS and result.score == 100:
            logger.info("✅ Full grader test passed")
            return True
        else:
            logger.warning("⚠️ Grader returned unexpected result")
            return False

    except Exception as e:
        logger.error(f"❌ Grader test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    logger.info("\n\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + " ZEROCTL WORKER GRADER TEST SUITE ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")

    tests = [
        ("Docker Connection", test_docker_connection),
        ("Simple Container", test_simple_container),
        ("Python Container", test_python_container),
        ("Full Grader Pipeline", test_grader_with_python),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {name}: {e}", exc_info=True)
            results[name] = False

    # Summary
    logger.info("\n\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + " TEST SUMMARY ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
