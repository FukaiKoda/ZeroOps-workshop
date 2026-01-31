"""
Engine: State machine for exercise progression.

Handles:
- Exercise loading from data/exercises/
- Prerequisites checking
- User progression logic
"""

import json
import logging
from pathlib import Path
from typing import Optional, List
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from schemas import ExerciseMeta, UserProfile, ExerciseStatus
from core.storage import Storage

logger = logging.getLogger(__name__)


class Engine:
    """
    State machine for exercise progression.
    
    Reads exercises from data/exercises/ directory structure:
    data/exercises/level_00/ex00_hello/meta.json
    """

    def __init__(self, storage: Storage):
        """Initialize engine."""
        self.storage = storage
        self.exercises_dir = Path(__file__).parent.parent.parent.parent / "data" / "exercises"
        self.exercises_cache: dict[str, ExerciseMeta] = {}
        
        # Load all exercises
        self._load_exercises()
        logger.info(f"✅ Engine initialized with {len(self.exercises_cache)} exercises")

    def _load_exercises(self):
        """Load all exercises from data/exercises/."""
        if not self.exercises_dir.exists():
            logger.warning(f"⚠️ Exercises directory not found: {self.exercises_dir}")
            return
        
        # Scan for meta.json files
        for meta_file in self.exercises_dir.rglob("meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    data = json.load(f)
                
                # Create ExerciseMeta
                exercise = ExerciseMeta(**data)
                self.exercises_cache[exercise.slug] = exercise
                
                logger.debug(f"📚 Loaded exercise: {exercise.slug}")
            except Exception as e:
                logger.error(f"❌ Failed to load {meta_file}: {e}")

    def get_exercise(self, slug: str) -> Optional[ExerciseMeta]:
        """
        Get exercise by slug.
        
        Args:
            slug: Exercise slug (e.g., "ex00-hello")
            
        Returns:
            ExerciseMeta or None
        """
        return self.exercises_cache.get(slug)

    def list_all_exercises(self) -> List[ExerciseMeta]:
        """
        List all available exercises.
        
        Returns:
            List of ExerciseMeta objects
        """
        return list(self.exercises_cache.values())

    def can_access_exercise(self, user: UserProfile, exercise: ExerciseMeta) -> bool:
        """
        Check if user can access this exercise (prerequisites met).
        
        Args:
            user: User profile
            exercise: Exercise to check
            
        Returns:
            True if user can access, False otherwise
        """
        # No prerequisites? Always allowed
        if not exercise.requirements:
            return True
        
        # Check if user has completed all prerequisites
        completed_slugs = {
            attempt.exercise_slug
            for attempt in user.history
            if attempt.status == ExerciseStatus.SUCCESS
        }
        
        for required_slug in exercise.requirements:
            if required_slug not in completed_slugs:
                logger.info(
                    f"❌ User {user.user_id} cannot access {exercise.slug}: "
                    f"missing prerequisite {required_slug}"
                )
                return False
        
        return True

    def get_next_exercise(self, user: UserProfile) -> Optional[ExerciseMeta]:
        """
        Get the next available exercise for user.
        
        Logic:
        1. If current_exercise_slug not completed, return it
        2. Otherwise, find first exercise with met prerequisites
        
        Args:
            user: User profile
            
        Returns:
            ExerciseMeta or None if all completed
        """
        # Get completed exercises
        completed_slugs = {
            attempt.exercise_slug
            for attempt in user.history
            if attempt.status == ExerciseStatus.SUCCESS
        }
        
        # Find first exercise that:
        # 1. Not completed
        # 2. Prerequisites met
        for exercise in sorted(self.exercises_cache.values(), key=lambda e: e.id):
            if exercise.slug in completed_slugs:
                continue  # Already completed
            
            if self.can_access_exercise(user, exercise):
                return exercise
        
        # All exercises completed!
        return None

    def update_user_progress(self, user: UserProfile, exercise_slug: str, success: bool):
        """
        Update user progress after completing an exercise.
        
        Args:
            user: User profile
            exercise_slug: Completed exercise slug
            success: True if passed, False if failed
        """
        if success:
            # Update current exercise to next available
            next_exercise = self.get_next_exercise(user)
            if next_exercise:
                user.current_exercise_slug = next_exercise.slug
                user.current_level += 1
            else:
                # All completed!
                user.current_exercise_slug = "completed"
            
            logger.info(f"📈 User {user.user_id} progressed to: {user.current_exercise_slug}")
        
        # Save updated user
        self.storage.save_user(user)
