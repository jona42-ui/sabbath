"""Core functionality for spiritual growth tracking and analysis."""

from typing import Dict, List, Optional
from datetime import datetime
from app.models import User, SpiritualProgress

class SpiritualGrowthManager:
    """Manages spiritual growth tracking and analysis."""
    
    CATEGORIES = {
        'bible_study': {
            'name': 'Bible Study',
            'description': 'Track your Bible study progress and understanding'
        },
        'prayer': {
            'name': 'Prayer Life',
            'description': 'Monitor your prayer habits and spiritual connection'
        },
        'service': {
            'name': 'Christian Service',
            'description': 'Track your service to others and community involvement'
        },
        'health': {
            'name': 'Health Practices',
            'description': 'Monitor adherence to health principles'
        }
    }
    
    @staticmethod
    def get_user_stats(user: User) -> Dict[str, Dict]:
        """Get spiritual growth statistics for a user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary containing stats for each spiritual category
        """
        stats = {}
        for category in SpiritualGrowthManager.CATEGORIES:
            progress = SpiritualProgress.query.filter_by(
                user_id=user.id,
                category=category
            ).order_by(SpiritualProgress.created_at.desc()).first()
            
            stats[category] = {
                'name': SpiritualGrowthManager.CATEGORIES[category]['name'],
                'description': SpiritualGrowthManager.CATEGORIES[category]['description'],
                'progress': progress.progress if progress else 0,
                'last_updated': progress.created_at if progress else None
            }
        
        return stats
    
    @staticmethod
    def record_progress(user: User, category: str, progress: int, notes: Optional[str] = None) -> SpiritualProgress:
        """Record spiritual progress for a user.
        
        Args:
            user: User object
            category: Category of spiritual growth
            progress: Progress value (0-100)
            notes: Optional notes about the progress
            
        Returns:
            Created SpiritualProgress object
        """
        if category not in SpiritualGrowthManager.CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        
        record = SpiritualProgress(
            user_id=user.id,
            category=category,
            progress=progress,
            notes=notes
        )
        
        return record
