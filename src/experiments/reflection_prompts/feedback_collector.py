"""
Interactive feedback collection for prompt experimentation.
"""

from datetime import datetime
from typing import Dict, List, Any


class FeedbackCollector:
    """Handles interactive user feedback collection during experiments"""
    
    def collect_segment_feedback(self, variants: List[Dict], segment_text: str) -> Dict[str, Any]:
        """
        Collect user feedback on prompt variants for a segment.
        
        Args:
            variants: List of prompt variants with 'name' and 'prompt' keys
            segment_text: The segment text that prompts were generated for
            
        Returns:
            Dictionary containing user feedback and metadata
        """
        # Get user choice
        feedback = self._collect_choice(variants)
        
        # If they chose a variant (not skip), get explanation
        if feedback["choice"].isdigit() and 1 <= int(feedback["choice"]) <= len(variants):
            chosen_index = int(feedback["choice"]) - 1
            chosen_prompt = variants[chosen_index]["prompt"]
            
            print(f'\nYour feedback on this prompt:')
            print(f'   "{chosen_prompt}"')
            print("(Share what worked well, what could be improved, or any other thoughts)")
            explanation = input("> ").strip()
            
            if explanation:
                feedback["feedback_text"] = explanation
            
            feedback["chosen_variant"] = variants[chosen_index]
        
        # Add metadata
        feedback["timestamp"] = datetime.now().isoformat()
        feedback["segment_word_count"] = len(segment_text.split())
        
        return feedback
    
    def _collect_choice(self, variants: List[Dict]) -> Dict[str, str]:
        """Collect user's choice of preferred variant"""
        # Build choice options
        choices = [str(i) for i in range(1, len(variants) + 1)] + ['s']
        choice_text = " ".join([f"[{i}]" for i in range(1, len(variants) + 1)]) + " [s] skip"
        
        print(f"\nWhich prompt would make you want to reflect most? {choice_text}")
        
        while True:
            choice = input("Choice: ").strip().lower()
            if choice in choices:
                break
            print(f"Please choose from: {', '.join(choices)}")
        
        return {"choice": choice}
    
    def should_continue_to_next_entry(self) -> bool:
        """Ask if user wants to continue to next entry"""
        print("\n" + "=" * 50)
        response = input("Continue to next entry? [Y/n]: ").strip().lower()
        return response != "n"
    
    def should_process_all_segments(self, segments: List[str]) -> List[int]:
        """
        Ask user which segments to process and return selected indices.
        
        Args:
            segments: List of segment texts
            
        Returns:
            List of segment indices (0-based) that user wants to process
        """
        if len(segments) == 1:
            return [0]  # Only one segment, process it
        
        print(f"\nEntry segmented into {len(segments)} parts:")
        
        for i, segment in enumerate(segments, 1):
            word_count = len(segment.split())
            print(f"\n[{i}] ({word_count} words)")
            safe_segment = self._safe_console_text(segment)
            print(f"    {safe_segment}")
        
        print(f"\nProcess: [a] All segments  [1,2,3...] Choose segments  [s] Skip entry")
        choice = input("Choice [a]: ").strip().lower() or "a"
        
        if choice == "s":
            return []
        elif choice == "a":
            return list(range(len(segments)))
        else:
            # Parse segment numbers
            try:
                indices = []
                for num_str in choice.split(","):
                    num = int(num_str.strip()) - 1  # Convert to 0-based
                    if 0 <= num < len(segments):
                        indices.append(num)
                return indices
            except ValueError:
                print("Warning: Invalid selection, processing all segments")
                return list(range(len(segments)))
    
    def confirm_segment_processing(self, segment_text: str) -> bool:
        """
        Ask user if they want to process a specific segment that might be too short.
        
        Args:
            segment_text: The segment to potentially process
            
        Returns:
            True if user wants to process this segment
        """
        word_count = len(segment_text.split())
        
        if word_count < 50:
            safe_segment = self._safe_console_text(segment_text)
            print(f"\nSegment ({word_count} words): {safe_segment}")
            response = input("This segment seems short. Process anyway? [y/N]: ").strip().lower()
            return response == "y"
        
        return True
    
    def _safe_console_text(self, text: str) -> str:
        """Convert text to console-safe encoding, replacing problematic characters."""
        if not text:
            return text
        return text.encode('ascii', errors='replace').decode('ascii')