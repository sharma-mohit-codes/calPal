from typing import List, Dict, Optional
from difflib import SequenceMatcher

class EventMatcher:
    """Smart event matching"""
    
    @staticmethod
    def similarity(s1: str, s2: str) -> float:
        """Calculate similarity score (0-1)"""
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    
    @staticmethod
    def find_match(term: str, events: List[Dict], threshold: float = 0.4) -> Optional[Dict]:
        """Find best matching event"""
        if not events:
            return None
        
        best, score = None, threshold
        tl = term.lower()
        
        for e in events:
            et = e.get('summary', '').lower()
            s = EventMatcher.similarity(tl, et)
            
            # Bonus for substring match
            if tl in et or et in tl:
                s += 0.3
            
            if s > score:
                score, best = s, e
        
        return best
    
    @staticmethod
    def find_all(term: str, events: List[Dict], threshold: float = 0.4, limit: int = 5) -> List[Dict]:
        """Find all matches above threshold"""
        matches = []
        
        for e in events:
            s = EventMatcher.similarity(term, e.get('summary', ''))
            if term.lower() in e.get('summary', '').lower():
                s += 0.3
            if s >= threshold:
                matches.append({'event': e, 'score': s})
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return [m['event'] for m in matches[:limit]]