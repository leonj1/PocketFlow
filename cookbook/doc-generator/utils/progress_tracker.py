"""Progress tracking utilities for document generation iterations"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks progress across document generation iterations"""
    
    def __init__(self):
        self.iteration_history: List[Dict] = []
        
    def record_iteration_results(self, iteration_num: int, committee_votes: Dict, 
                               section_statuses: Dict, completeness_score: Optional[float] = None):
        """Record the results of a single iteration
        
        Args:
            iteration_num: The current iteration number
            committee_votes: Dict with 'in_favor', 'against', 'abstain' counts
            section_statuses: Dict mapping section names to their approval status
            completeness_score: Optional completeness score (0-100)
        """
        result = {
            'iteration': iteration_num,
            'committee_votes': committee_votes.copy(),
            'section_approvals': self._count_section_approvals(section_statuses),
            'completeness_score': completeness_score,
            'approved_sections': [name for name, data in section_statuses.items() 
                                if data.get('status') == 'approved']
        }
        
        self.iteration_history.append(result)
        logger.info(f"Recorded iteration {iteration_num}: {committee_votes}, "
                   f"{result['section_approvals']['approved']}/{result['section_approvals']['total']} sections approved")
    
    def _count_section_approvals(self, section_statuses: Dict) -> Dict:
        """Count approved vs total sections"""
        if not section_statuses:
            return {'approved': 0, 'total': 0}
            
        approved = sum(1 for data in section_statuses.values() 
                      if data.get('status') == 'approved')
        return {
            'approved': approved,
            'total': len(section_statuses)
        }
    
    def has_progress_in_window(self, window_size: int = 3) -> Tuple[bool, str]:
        """Check if there's been progress in the last N iterations
        
        Returns:
            Tuple of (has_progress: bool, reason: str)
        """
        if len(self.iteration_history) < 2:
            return True, "Not enough iterations to determine progress"
        
        # Get the last window_size iterations
        window = self.iteration_history[-window_size:] if len(self.iteration_history) >= window_size else self.iteration_history
        
        if len(window) < 2:
            return True, "Window too small to determine progress"
        
        # Check various progress indicators
        progress_indicators = []
        
        # 1. Check if committee approvals are increasing
        first_votes = window[0]['committee_votes']
        last_votes = window[-1]['committee_votes']
        
        if last_votes['in_favor'] > first_votes['in_favor']:
            progress_indicators.append(f"Committee approvals increased from {first_votes['in_favor']} to {last_votes['in_favor']}")
        
        if last_votes['against'] < first_votes['against']:
            progress_indicators.append(f"Committee rejections decreased from {first_votes['against']} to {last_votes['against']}")
        
        # 2. Check if more sections are being approved
        first_sections = window[0]['section_approvals']
        last_sections = window[-1]['section_approvals']
        
        if last_sections['approved'] > first_sections['approved']:
            progress_indicators.append(f"Approved sections increased from {first_sections['approved']} to {last_sections['approved']}")
        
        # 3. Check if completeness score is improving
        first_score = window[0].get('completeness_score')
        last_score = window[-1].get('completeness_score')
        
        if first_score is not None and last_score is not None and last_score > first_score:
            progress_indicators.append(f"Completeness score improved from {first_score} to {last_score}")
        
        # 4. Check if any new sections were approved in the window
        all_approved_sections = set()
        for i, iteration in enumerate(window):
            if i > 0:  # Skip first iteration
                new_approvals = set(iteration['approved_sections']) - all_approved_sections
                if new_approvals:
                    progress_indicators.append(f"New sections approved in iteration {iteration['iteration']}: {', '.join(new_approvals)}")
            all_approved_sections.update(iteration['approved_sections'])
        
        has_progress = len(progress_indicators) > 0
        
        if has_progress:
            reason = f"Progress detected: {'; '.join(progress_indicators)}"
        else:
            reason = f"No progress detected in last {len(window)} iterations"
        
        return has_progress, reason
    
    def get_progress_summary(self) -> str:
        """Generate a comprehensive progress summary"""
        if not self.iteration_history:
            return "No iterations recorded yet"
        
        lines = ["Progress Summary:"]
        lines.append(f"Total iterations: {len(self.iteration_history)}")
        
        for iteration in self.iteration_history:
            votes = iteration['committee_votes']
            sections = iteration['section_approvals']
            score = iteration.get('completeness_score', 'N/A')
            
            lines.append(f"\nIteration {iteration['iteration']}:")
            lines.append(f"  Committee: {votes['in_favor']} in favor, {votes['against']} against, {votes['abstain']} abstain")
            lines.append(f"  Sections: {sections['approved']}/{sections['total']} approved")
            lines.append(f"  Completeness: {score}")
        
        # Add rolling window analysis
        has_recent_progress, reason = self.has_progress_in_window()
        lines.append(f"\nRecent progress (last 3 iterations): {reason}")
        
        return "\n".join(lines)