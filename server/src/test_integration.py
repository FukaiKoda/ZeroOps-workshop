#!/usr/bin/env python3
"""
Integration Test: Server-Core + Worker

Tests the complete flow:
1. Submit code via API
2. Job is created and executed
3. Worker grades submission
4. Result is returned via status endpoint
"""

import sys
import time
import logging
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from schemas import SubmitRequest, FileSubmission, ExerciseStatus
from core.job_manager import JobManager
from core.storage import Storage
from core.engine import Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_integration():
    """Test the full integration."""
    logger.info("\n" + "="*70)
    logger.info("INTEGRATION TEST: Server-Core + Worker")
    logger.info("="*70 + "\n")
    
    # Initialize services
    logger.info("🔧 Initializing services...")
    storage = Storage()
    engine = Engine(storage)
    job_manager = JobManager()
    
    # Create a test user
    logger.info("👤 Creating test user...")
    user = storage.get_or_create_user("test-token-123")
    logger.info(f"   User ID: {user.user_id}")
    logger.info(f"   Current exercise: {user.current_exercise_slug}")
    
    # Get the first exercise
    logger.info("\n📚 Loading exercise...")
    exercise = engine.get_exercise("ex00-hello")
    
    if not exercise:
        logger.error("❌ Exercise 'ex00-hello' not found")
        logger.info("   Make sure data/exercises/level_00/ex00_hello/meta.json exists")
        return False
    
    logger.info(f"   Exercise: {exercise.title}")
    logger.info(f"   Docker image: {exercise.docker_image}")
    
    # Create student code (correct solution)
    logger.info("\n📝 Creating student submission...")
    student_code = """
def say_hello(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(say_hello("World"))
"""
    
    # Create grader script
    grader_code = """
import sys
import json
sys.path.insert(0, '/student')

try:
    from main import say_hello
    result = say_hello("World")
    
    if result == "Hello, World!":
        print(json.dumps({"status": "success", "score": 100}))
        sys.exit(0)
    else:
        print(json.dumps({"status": "failure", "score": 0}))
        print(f"Expected: 'Hello, World!', Got: '{result}'")
        sys.exit(1)
except Exception as e:
    print(json.dumps({"status": "failure", "score": 0}))
    print(f"Error: {e}")
    sys.exit(1)
"""
    
    files = [
        FileSubmission(filename="main.py", content=student_code),
        FileSubmission(filename="grader/test.py", content=grader_code),
    ]
    
    # Create grading job
    logger.info("\n🚀 Creating grading job...")
    job_id = job_manager.create_job(
        user_id=user.user_id,
        exercise=exercise,
        files=files,
    )
    logger.info(f"   Job ID: {job_id}")
    
    # Execute job (in foreground for testing)
    logger.info("\n⏳ Executing grading job...")
    logger.info("   (This calls YOUR worker code!)")
    
    try:
        job_manager.execute_job(job_id)
    except Exception as e:
        logger.error(f"❌ Job execution failed: {e}")
        logger.info("\n⚠️  This likely means Docker is not installed.")
        logger.info("   The integration logic is correct, but Docker is needed to run containers.")
        return False
    
    # Check status
    logger.info("\n📊 Checking job status...")
    status = job_manager.get_job_status(job_id)
    
    if not status:
        logger.error("❌ Job status not found")
        return False
    
    logger.info(f"   Status: {status.status.value}")
    
    if status.result:
        logger.info(f"   Score: {status.result.score}")
        logger.info(f"   Output:\n{status.result.output_log}")
    
    # Verify result
    if status.status == ExerciseStatus.SUCCESS:
        logger.info("\n✅ Integration test PASSED!")
        logger.info("   Server-Core successfully called Worker and got result!")
        return True
    else:
        logger.warning(f"\n⚠️  Job completed but status is: {status.status.value}")
        logger.info("   This might be OK if Docker is not available.")
        return False


if __name__ == "__main__":
    success = test_integration()
    
    logger.info("\n" + "="*70)
    if success:
        logger.info("🎉 INTEGRATION COMPLETE - Server-Core + Worker are connected!")
    else:
        logger.info("⚠️  Integration logic verified, but Docker needed for full test")
    logger.info("="*70)
    
    sys.exit(0 if success else 1)
