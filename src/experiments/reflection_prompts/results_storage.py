"""
Storage and management of experimental results.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class ExperimentResultsStorage:
    """Handles saving experimental results"""
    
    def __init__(self, base_dir: str = "data/experiments"):
        """
        Initialize results storage.
        
        Args:
            base_dir: Directory to store experimental results
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_experiment_results(self, experiment_config: Dict, results: List[Dict]) -> str:
        """
        Save complete experiment results to a JSON file.
        
        Args:
            experiment_config: Configuration used for the experiment
            results: List of entry results from the experiment
            
        Returns:
            Path to the saved results file
        """
        experiment_data = {
            "experiment_metadata": {
                "experiment_id": experiment_config.get("id", f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "timestamp": datetime.now().isoformat(),
                "total_entries_processed": len(results),
                "total_segments_processed": sum(len(entry.get("segment_results", [])) for entry in results),
                "config": experiment_config
            },
            "results": results,
            "summary": self._generate_summary(results)
        }
        
        # Save to file
        experiment_id = experiment_data["experiment_metadata"]["experiment_id"]
        filename = f"{experiment_id}.json"
        filepath = self.base_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(experiment_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def _generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from experiment results"""
        if not results:
            return {"total_segments": 0, "total_feedback": 0}
        
        total_segments = 0
        feedback_counts = {}
        chosen_variants = []
        explanations = []
        
        for entry_result in results:
            segment_results = entry_result.get("segment_results", [])
            total_segments += len(segment_results)
            
            for segment_result in segment_results:
                feedback = segment_result.get("feedback", {})
                choice = feedback.get("choice")
                
                if choice and choice != "s":
                    # Count variant choices
                    if "chosen_variant" in feedback:
                        variant_name = feedback["chosen_variant"].get("name", "unknown")
                        feedback_counts[variant_name] = feedback_counts.get(variant_name, 0) + 1
                        chosen_variants.append(variant_name)
                    
                    # Collect feedback text
                    if "feedback_text" in feedback:
                        explanations.append(feedback["feedback_text"])
        
        # Calculate preference percentages
        total_choices = len(chosen_variants)
        variant_preferences = {}
        if total_choices > 0:
            for variant, count in feedback_counts.items():
                variant_preferences[variant] = {
                    "count": count,
                    "percentage": round((count / total_choices) * 100, 1)
                }
        
        return {
            "total_segments": total_segments,
            "total_feedback_collected": total_choices,
            "variant_preferences": variant_preferences,
            "sample_explanations": explanations[:5] if explanations else [],  # First 5 explanations as examples
            "most_preferred_variant": max(feedback_counts.items(), key=lambda x: x[1])[0] if feedback_counts else None
        }