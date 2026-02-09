from typing import List, Optional, Dict
from difflib import SequenceMatcher

class EventMatcher:
    """
    Smart event matching utility for finding calendar events
    """
    
    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings (0-1)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def find_best_match(
        search_term: str, 
        events: List[Dict],
        threshold: float = 0.4
    ) -> Optional[Dict]:
        """
        Find the best matching event from a list
        
        Args:
            search_term: The term to search for
            events: List of calendar events
            threshold: Minimum similarity score (0-1)
        
        Returns:
            Best matching event or None
        """
        if not events:
            return None
        
        best_match = None
        best_score = 0
        
        for event in events:
            event_title = event.get('summary', '')
            score = EventMatcher.similarity_score(search_term, event_title)
            
            # Exact substring match gets bonus
            if search_term.lower() in event_title.lower() or event_title.lower() in search_term.lower():
                score += 0.3
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = event
        
        return best_match
    
    @staticmethod
    def find_all_matches(
        search_term: str,
        events: List[Dict],
        threshold: float = 0.4,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Find all matching events above threshold
        """
        matches = []
        
        for event in events:
            event_title = event.get('summary', '')
            score = EventMatcher.similarity_score(search_term, event_title)
            
            if search_term.lower() in event_title.lower():
                score += 0.3
            
            if score >= threshold:
                matches.append({
                    'event': event,
                    'score': score
                })
        
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top matches
        return [m['event'] for m in matches[:max_results]]
    
    @staticmethod
    def filter_by_date_range(
        events: List[Dict],
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        Filter events by date range
        """
        # This is a placeholder - you can enhance with actual date filtering
        return events