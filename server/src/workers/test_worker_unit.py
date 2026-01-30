#!/usr/bin/env python3
"""
Unit tests for Worker components (without requiring Docker).

This validates the grader logic, sandbox config, and argument parsing.
Run: python3 test_worker_unit.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add paths
workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "shared"))
sys.path.insert(0, str(workspace_root / "server"))

from schemas import (
    FileSubmission,
    WorkerJob,
    ExerciseMeta,
    TechStack,
    ExerciseStatus,
    WorkerJobResult,
)
from workers.sandbox import SandboxPresets, sandbox_config_to_docker_kwargs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_sandbox_python_config():
    """Test 1: Python sandbox configuration."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Python Sandbox Config")
    logger.info("="*60)

    try:
        config = SandboxPresets.python_safe()
        
        logger.info(f"Network mode: {config.network_mode}")
        logger.info(f"Memory limit: {config.memory_limit}")
        logger.info(f"CPU limit: {config.cpu_limit}")
        logger.info(f"PIDs limit: {config.pids_limit}")
        logger.info(f"User: {config.user}")

        assert config.network_mode == "none", "Network should be isolated"
        assert config.memory_limit == "256m", "Memory should be limited"
        assert config.cpu_limit == 1.0, "CPU should be limited"
        assert config.pids_limit == 50, "PIDs should be limited"
        assert config.user == "1000:1000", "Should run as non-root"

        logger.info("✅ Python sandbox config is correct")
        return True

    except AssertionError as e:
        logger.error(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_sandbox_c_config():
    """Test 2: C sandbox configuration."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: C Sandbox Config")
    logger.info("="*60)

    try:
        config = SandboxPresets.c_safe()
        
        logger.info(f"Network mode: {config.network_mode}")
        logger.info(f"Memory limit: {config.memory_limit}")
        logger.info(f"CPU limit: {config.cpu_limit}")

        assert config.network_mode == "none", "Network should be isolated"
        assert config.memory_limit == "512m", "Memory should be 512MB for C compilation"
        assert config.cpu_limit == 2.0, "CPU should allow 2 cores"

        logger.info("✅ C sandbox config is correct")
        return True

    except AssertionError as e:
        logger.error(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_sandbox_strict_config():
    """Test 3: Strict sandbox configuration."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Strict Sandbox Config")
    logger.info("="*60)

    try:
        config = SandboxPresets.strict()
        
        logger.info(f"Network mode: {config.network_mode}")
        logger.info(f"Memory limit: {config.memory_limit}")
        logger.info(f"CPU limit: {config.cpu_limit}")
        logger.info(f"PIDs limit: {config.pids_limit}")
        logger.info(f"Read-only FS: {config.read_only_rootfs}")

        assert config.network_mode == "none"
        assert config.memory_limit == "128m", "Should be minimal"
        assert config.cpu_limit == 0.5, "Should be minimal"
        assert config.pids_limit == 20, "Should be minimal"
        assert config.read_only_rootfs == True, "FS should be read-only"

        logger.info("✅ Strict sandbox config is correct")
        return True

    except AssertionError as e:
        logger.error(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_docker_kwargs_conversion():
    """Test 4: Sandbox config to Docker kwargs conversion."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Docker Kwargs Conversion")
    logger.info("="*60)

    try:
        config = SandboxPresets.python_safe()
        kwargs = sandbox_config_to_docker_kwargs(config)

        logger.info("Generated Docker kwargs:")
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")

        assert "network_mode" in kwargs
        assert "mem_limit" in kwargs
        assert "memswap_limit" in kwargs
        assert "cpus" in kwargs
        assert "pids_limit" in kwargs
        assert "user" in kwargs
        assert "cap_drop" in kwargs

        logger.info("✅ Docker kwargs conversion is correct")
        return True

    except AssertionError as e:
        logger.error(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_worker_job_creation():
    """Test 5: Create a WorkerJob object."""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: WorkerJob Creation")
    logger.info("="*60)

    try:
        exercise = ExerciseMeta(
            id="ex01_test",
            slug="test-01",
            title="Test Exercise",
            points=50,
            stack=TechStack.PYTHON,
            allowed_files=["main.py"],
            docker_image="python:3.11-alpine",
            grader_script_path="/data/exercises/level_00/ex01_test/grader/test.py",
            mount_path="/student",
            timeout_seconds=10,
        )

        files = [
            FileSubmission(filename="main.py", content="print('Hello')"),
        ]

        job = WorkerJob(
            job_id="job-001",
            user_id="user_42",
            exercise=exercise,
            files=files,
            docker_image="python:3.11-alpine",
            grader_script_path="/data/exercises/level_00/ex01_test/grader/test.py",
            mount_path="/student",
            timeout_seconds=10,
        )

        logger.info(f"Job ID: {job.job_id}")
        logger.info(f"User ID: {job.user_id}")
        logger.info(f"Exercise: {job.exercise.slug}")
        logger.info(f"Files: {[f.filename for f in job.files]}")
        logger.info(f"Docker Image: {job.docker_image}")
        logger.info(f"Timeout: {job.timeout_seconds}s")

        assert job.job_id == "job-001"
        assert job.user_id == "user_42"
        assert len(job.files) == 1
        assert job.exercise.stack == TechStack.PYTHON

        logger.info("✅ WorkerJob creation is correct")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_worker_job_result():
    """Test 6: Create a WorkerJobResult."""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: WorkerJobResult Creation")
    logger.info("="*60)

    try:
        result = WorkerJobResult(
            job_id="job-001",
            user_id="user_42",
            exercise_slug="test-01",
            status=ExerciseStatus.SUCCESS,
            output_log="Test output\nAll tests passed!",
            exit_code=0,
            score=100,
            timestamp=datetime.utcnow(),
        )

        logger.info(f"Job ID: {result.job_id}")
        logger.info(f"User ID: {result.user_id}")
        logger.info(f"Status: {result.status.value}")
        logger.info(f"Score: {result.score}")
        logger.info(f"Exit Code: {result.exit_code}")

        assert result.status == ExerciseStatus.SUCCESS
        assert result.score == 100
        assert result.exit_code == 0

        logger.info("✅ WorkerJobResult creation is correct")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_exercise_meta_with_all_fields():
    """Test 7: ExerciseMeta with all required fields."""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: ExerciseMeta Validation")
    logger.info("="*60)

    try:
        exercise = ExerciseMeta(
            id="docker-02",
            slug="docker-02",
            title="Docker Basics",
            points=100,
            stack=TechStack.DOCKER,
            allowed_files=["Dockerfile", "main.py"],
            forbidden_functions=["system()"],
            requirements=["docker-01"],
            docker_image="c-runner:latest",
            grader_script_path="/data/exercises/level_01/docker-02/grader/test.py",
            mount_path="/student",
            timeout_seconds=15,
            subject_md_path="subject.md",
        )

        logger.info(f"Exercise ID: {exercise.id}")
        logger.info(f"Title: {exercise.title}")
        logger.info(f"Stack: {exercise.stack.value}")
        logger.info(f"Points: {exercise.points}")
        logger.info(f"Requirements: {exercise.requirements}")
        logger.info(f"Docker Image: {exercise.docker_image}")
        logger.info(f"Timeout: {exercise.timeout_seconds}s")

        assert exercise.id == "docker-02"
        assert len(exercise.requirements) > 0
        assert exercise.docker_image == "c-runner:latest"

        logger.info("✅ ExerciseMeta validation is correct")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_file_submission():
    """Test 8: FileSubmission parsing."""
    logger.info("\n" + "="*60)
    logger.info("TEST 8: FileSubmission Parsing")
    logger.info("="*60)

    try:
        code = """
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(2, 3))
"""
        file = FileSubmission(filename="main.py", content=code)

        logger.info(f"Filename: {file.filename}")
        logger.info(f"Content length: {len(file.content)} chars")
        logger.info(f"Content preview: {file.content[:50]}...")

        assert file.filename == "main.py"
        assert len(file.content) > 0
        assert "def add" in file.content

        logger.info("✅ FileSubmission parsing is correct")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def main():
    """Run all unit tests."""
    logger.info("\n\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + " WORKER UNIT TESTS ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")

    tests = [
        ("Sandbox Python Config", test_sandbox_python_config),
        ("Sandbox C Config", test_sandbox_c_config),
        ("Sandbox Strict Config", test_sandbox_strict_config),
        ("Docker Kwargs Conversion", test_docker_kwargs_conversion),
        ("WorkerJob Creation", test_worker_job_creation),
        ("WorkerJobResult Creation", test_worker_job_result),
        ("ExerciseMeta Validation", test_exercise_meta_with_all_fields),
        ("FileSubmission Parsing", test_file_submission),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"❌ Unexpected error in {name}: {e}", exc_info=True)
            results[name] = False

    # Summary
    logger.info("\n\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + " UNIT TEST SUMMARY ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All unit tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
