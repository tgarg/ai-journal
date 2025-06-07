"""
Entry segmentation utilities for experimental prompt testing.
"""

from typing import List


class EntrySegmenter:
    """Handles segmentation strategies for journal entries"""
    
    @staticmethod
    def segment_by_paragraph_groups(content: str, target_words: int = 200, min_words: int = 30) -> List[str]:
        """
        Group paragraphs to hit ~200 word target while respecting paragraph boundaries.
        
        Strategy:
        - Large paragraphs (>=target_words) become their own segment
        - Small paragraphs are combined forward until target is reached
        - Never break paragraph boundaries
        - Respects natural writing flow
        
        Args:
            content: The journal entry content
            target_words: Target word count per segment (default 200)
            min_words: Minimum words for a segment to be meaningful (default 30)
            
        Returns:
            List of paragraph-grouped segments
        """
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return []
        
        # If very short entry, return as single segment
        total_words = len(content.split())
        if total_words < min_words:
            return []  # Too short to be meaningful
        
        segments = []
        current_group = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            para_words = len(paragraph.split())
            
            # Large paragraphs (>=target) become their own segment
            if para_words >= target_words:
                # Close current group first
                if current_group:
                    segments.append('\n\n'.join(current_group))
                    current_group = []
                    current_word_count = 0
                
                # Add large paragraph as standalone segment
                segments.append(paragraph)
            
            # Check if adding this paragraph would exceed reasonable limit
            elif current_word_count + para_words > target_words * 1.5:  # 300 words max
                # Close current group and start new one
                if current_group:
                    segments.append('\n\n'.join(current_group))
                current_group = [paragraph]
                current_word_count = para_words
            
            # Add to current group
            else:
                current_group.append(paragraph)
                current_word_count += para_words
        
        # Handle final group
        if current_group:
            final_segment = '\n\n'.join(current_group)
            final_word_count = len(final_segment.split())
            
            # Only add if it meets minimum word requirement
            if final_word_count >= min_words:
                segments.append(final_segment)
        
        return segments
    
    @staticmethod
    def is_meaningful_segment(text: str, min_words: int = 30) -> bool:
        """
        Check if segment has enough content to be worth processing.
        
        Args:
            text: The segment text to evaluate
            min_words: Minimum word count for meaningful segment
            
        Returns:
            True if segment is meaningful for reflection prompt generation
        """
        text = text.strip()
        
        # Check word count
        word_count = len(text.split())
        if word_count < min_words:
            return False
        
        # Check for complete thoughts (has sentence-ending punctuation)
        has_complete_thought = any(punct in text for punct in '.!?')
        if not has_complete_thought:
            return False
        
        # Avoid segments that are mostly numbers/dates/metadata
        alpha_chars = sum(1 for c in text if c.isalpha())
        if len(text) > 0 and alpha_chars / len(text) < 0.5:  # Less than 50% letters
            return False
        
        return True
    
    @staticmethod
    def get_segment_stats(segments: List[str]) -> dict:
        """
        Get statistics about the segmentation for display purposes.
        
        Args:
            segments: List of segment strings
            
        Returns:
            Dictionary with segmentation statistics
        """
        if not segments:
            return {"count": 0, "total_words": 0, "avg_words": 0, "word_counts": []}
        
        word_counts = [len(segment.split()) for segment in segments]
        total_words = sum(word_counts)
        
        return {
            "count": len(segments),
            "total_words": total_words,
            "avg_words": total_words // len(segments),
            "word_counts": word_counts,
            "min_words": min(word_counts),
            "max_words": max(word_counts)
        }