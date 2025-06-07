"""
Main experimental tool for testing reflection prompt variants.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

from .segmentation import EntrySegmenter
from .feedback_collector import FeedbackCollector
from .results_storage import ExperimentResultsStorage
from .experimental_prompts import EXPERIMENTAL_TEMPLATES


class PromptExperimenter:
    """Experimental tool for testing reflection prompt variants"""
    
    def __init__(self, journal_service, reflection_service):
        """
        Initialize the prompt experimenter.
        
        Args:
            journal_service: Service for accessing journal entries
            reflection_service: Service for generating reflection prompts
        """
        self.journal_service = journal_service
        self.reflection_service = reflection_service
        self.feedback_collector = FeedbackCollector()
        self.results_storage = ExperimentResultsStorage()
        self.segmenter = EntrySegmenter()
    
    def run_experiment(self, args):
        """Main experiment flow"""
        print("AI Reflection Prompt Experimentation")
        print("=" * 50)
        
        # Get entry IDs to experiment with
        entry_ids = self._get_entry_ids(args)
        if not entry_ids:
            print("Error: No entries specified")
            print("Usage:")
            print("  python journal.py reflect-experiment --entries entry1,entry2,entry3")
            print("  python journal.py reflect-experiment --all")
            print("  python journal.py reflect-experiment --recent 5")
            return
        
        # Load entries
        entries = self._load_entries(entry_ids)
        if not entries:
            print("Error: No valid entries found")
            return
        
        # Set up experiment config
        config = self._setup_experiment_config(entries)
        
        # Generate all prompts upfront for all entries
        print(f"\nGenerating prompts for all {len(entries)} entries...")
        print("(This may take a while - good time for coffee!)")
        all_entry_data = self._generate_all_prompts(entries, config)
        
        print(f"\nAll prompts generated! Starting evaluation phase...")
        
        # Now evaluate all entries interactively
        experiment_results = []
        for i, entry_data in enumerate(all_entry_data, 1):
            print(f"\nEntry {i}/{len(all_entry_data)} (ID: {entry_data['entry_id'][:8]})")
            print("=" * 30)
            
            result = self._evaluate_single_entry(entry_data)
            if result:  # User didn't skip entire entry
                experiment_results.append(result)
            
            # Continue prompt
            if i < len(all_entry_data) and not self.feedback_collector.should_continue_to_next_entry():
                break
        
        # Save and summarize results
        if experiment_results:
            self._save_and_summarize_results(config, experiment_results)
        else:
            print("\nNo results to save (all entries were skipped)")
    
    def _get_entry_ids(self, args) -> List[str]:
        """Extract entry IDs from command line arguments"""
        if hasattr(args, 'entries') and args.entries:
            # Handle comma-separated entry IDs
            return [entry_id.strip() for entry_id in args.entries.split(',')]
        elif hasattr(args, 'all') and args.all:
            # Get all entries
            all_entries = self.journal_service.list_entries(limit=None)
            return [entry.id for entry in all_entries]
        elif hasattr(args, 'recent') and args.recent:
            # Get N most recent entries
            recent_entries = self.journal_service.list_entries(limit=args.recent)
            return [entry.id for entry in recent_entries]
        else:
            return []
    
    def _load_entries(self, entry_ids: List[str]):
        """Load journal entries by ID"""
        entries = []
        for entry_id in entry_ids:
            try:
                # Resolve short ID to full ID
                full_id = self._resolve_short_id(entry_id)
                entry = self.journal_service.get_entry(full_id)
                
                if entry and len(entry.content.split()) >= 30:  # Minimum meaningful length
                    entries.append(entry)
                else:
                    print(f"Warning: Entry {entry_id[:8]} too short or not found, skipping")
            except Exception as e:
                print(f"Warning: Could not load entry {entry_id[:8]}: {e}")
        
        return entries
    
    def _resolve_short_id(self, short_id: str) -> str:
        """Resolve short ID to full UUID."""
        if len(short_id) >= 32:  # Already full ID
            return short_id
        
        # Find matching entry
        entries = self.journal_service.list_entries(limit=None)  # Get all entries
        matches = [entry for entry in entries if entry.id.startswith(short_id)]
        
        if not matches:
            raise Exception(f"No entry found with ID starting with '{short_id}'")
        
        if len(matches) > 1:
            # Multiple matches - show options
            print("Multiple entries match that ID:")
            for entry in matches:
                print(f"  {entry.id[:8]} - {entry.title or '(no title)'}")
            raise Exception(f"Ambiguous ID '{short_id}' - please use more characters")
        
        return matches[0].id
    
    def _setup_experiment_config(self, entries) -> Dict:
        """Set up experiment configuration"""
        config = {
            "id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "entry_ids": [entry.id for entry in entries],
            "segmentation_strategy": "paragraph_groups",
            "target_words_per_segment": 200,
            "variants_to_test": self._get_variants_to_test(),
            "system_prompt": self.reflection_service.SYSTEM_PROMPT,
            "experimental_templates": EXPERIMENTAL_TEMPLATES
        }
        
        print(f"\nExperiment Configuration:")
        print(f"   ID: {config['id']}")
        print(f"   Entries: {len(entries)} entries")
        print(f"   Variants: {', '.join([v['name'] for v in config['variants_to_test']])}")
        print(f"   Segmentation: ~{config['target_words_per_segment']} words per segment")
        
        return config
    
    def _get_variants_to_test(self) -> List[Dict]:
        """Define which prompt variants to test"""
        variants = [
            {
                "name": "emotional_awareness_v1",
                "type": "experimental",
                "template_key": "emotional_awareness_v1"
            },
            {
                "name": "perspective_v1",
                "type": "experimental",
                "template_key": "perspective_v1"
            },
            {
                "name": "assumptions_v1",
                "type": "experimental",
                "template_key": "assumptions_v1"
            }
        ]
        
        return variants
    
    def _generate_all_prompts(self, entries, config) -> List[Dict]:
        """Generate all prompts for all entries upfront"""
        all_entry_data = []
        
        for i, entry in enumerate(entries, 1):
            print(f"   Processing entry {i}/{len(entries)} (ID: {entry.id[:8]})...")
            
            # Segment the entry
            segments = self.segmenter.segment_by_paragraph_groups(
                entry.content, 
                target_words=config["target_words_per_segment"]
            )
            
            if not segments:
                print(f"   Warning: No meaningful segments found for entry {entry.id[:8]}, skipping")
                continue
            
            # Generate variants for all segments
            all_segment_variants = []
            for j, segment in enumerate(segments, 1):
                print(f"      Generating variants for segment {j}/{len(segments)}...")
                variants = self._generate_prompt_variants(segment, config["variants_to_test"])
                
                all_segment_variants.append({
                    "segment_number": j,
                    "segment_text": segment,
                    "segment_word_count": len(segment.split()),
                    "variants": variants
                })
            
            # Store complete entry data
            all_entry_data.append({
                "entry_id": entry.id,
                "entry_content": entry.content,
                "entry_preview": entry.content[:200] + ("..." if len(entry.content) > 200 else ""),
                "total_segments": len(segments),
                "segment_data": all_segment_variants
            })
            
        return all_entry_data
    
    def _evaluate_single_entry(self, entry_data) -> Optional[Dict]:
        """Evaluate a single entry with pre-generated variants"""
        # Show entry preview
        print(f"\nEntry content ({len(entry_data['entry_content'].split())} words):")
        safe_content = self._safe_console_text(entry_data['entry_content'])
        print(f"{safe_content}")
        
        print(f"\nAuto-segmented into {entry_data['total_segments']} parts")
        
        # Evaluate each segment
        segment_results = []
        for segment_data in entry_data['segment_data']:
            result = self._evaluate_single_segment(segment_data)
            if result:  # User didn't skip this segment
                segment_results.append(result)
        
        return {
            "entry_id": entry_data["entry_id"],
            "entry_preview": entry_data["entry_preview"],
            "total_segments": entry_data["total_segments"],
            "evaluated_segments": len(segment_results),
            "segment_results": segment_results
        }
    
    
    def _evaluate_single_segment(self, segment_data: Dict) -> Optional[Dict]:
        """Evaluate a single segment with pre-generated variants"""
        segment_number = segment_data["segment_number"]
        segment_text = segment_data["segment_text"]
        variants = segment_data["variants"]
        word_count = segment_data["segment_word_count"]
        
        print(f"\n--- Segment {segment_number} ({word_count} words) ---")
        safe_segment = self._safe_console_text(segment_text)
        print(f"{safe_segment}")
        
        if not variants:
            print("Error: No variants available for this segment")
            return None
        
        # Display variants
        print(f"\nGenerated {len(variants)} prompt variants:")
        for i, variant in enumerate(variants, 1):
            print(f"\n{i}. {variant['name']}")
            print(f'   "{variant["prompt"]}"')
        
        # Collect feedback
        feedback = self.feedback_collector.collect_segment_feedback(variants, segment_text)
        
        if feedback.get("choice") == "s":
            print("Skipping segment")
            return None
        
        print("Feedback saved")
        
        return {
            "segment_text": segment_text,
            "segment_word_count": word_count,
            "segment_number": segment_number,
            "variants": variants,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_prompt_variants(self, segment_text: str, variant_configs: List[Dict]) -> List[Dict]:
        """Generate different prompt variants for a segment"""
        variants = []
        
        for variant_config in variant_configs:
            try:
                if variant_config["type"] == "existing_strategy":
                    # Use existing reflection service strategy
                    result = self.reflection_service.generate_reflection_prompt(
                        segment_text, 
                        strategy=variant_config["strategy"]
                    )
                    variants.append({
                        "name": variant_config["name"],
                        "type": variant_config["type"],
                        "strategy": variant_config["strategy"],
                        "prompt": result["reflection_prompt"]
                    })
                
                elif variant_config["type"] == "experimental":
                    # Use experimental template
                    template_key = variant_config["template_key"]
                    template = EXPERIMENTAL_TEMPLATES[template_key]
                    generation_prompt = template.format(content=segment_text)
                    
                    # Generate using the same system prompt and client
                    reflection_prompt = self.reflection_service.ollama_client.generate(
                        prompt=generation_prompt,
                        system=self.reflection_service.SYSTEM_PROMPT
                    )
                    
                    variants.append({
                        "name": variant_config["name"],
                        "type": variant_config["type"],
                        "template_key": template_key,
                        "generation_prompt": generation_prompt,
                        "prompt": reflection_prompt.strip()
                    })
                    
            except Exception as e:
                print(f"Warning: Failed to generate variant {variant_config['name']}: {e}")
                continue
        
        return variants
    
    def _safe_console_text(self, text: str) -> str:
        """Convert text to console-safe encoding, replacing problematic characters."""
        if not text:
            return text
        return text.encode('ascii', errors='replace').decode('ascii')
    
    def _save_and_summarize_results(self, config: Dict, results: List[Dict]):
        """Save results and display summary"""
        # Save to file
        filepath = self.results_storage.save_experiment_results(config, results)
        
        print(f"\nExperiment Complete!")
        print("=" * 50)
        print(f"Results saved to: {filepath}")
        
        # Load and display summary
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summary = data.get("summary", {})
                
                print(f"\nSummary:")
                print(f"   Entries processed: {len(results)}")
                print(f"   Segments processed: {summary.get('total_segments', 0)}")
                print(f"   Feedback collected: {summary.get('total_feedback_collected', 0)}")
                
                # Show variant preferences
                preferences = summary.get("variant_preferences", {})
                if preferences:
                    print(f"\nVariant Preferences:")
                    for variant, stats in preferences.items():
                        print(f"   {variant}: {stats['count']} times ({stats['percentage']}%)")
                
                # Show sample explanations
                explanations = summary.get("sample_explanations", [])
                if explanations:
                    print(f"\nSample feedback:")
                    for explanation in explanations[:3]:  # Show first 3
                        print(f"   • \"{explanation}\"")
                        
        except Exception as e:
            print(f"Warning: Could not display summary: {e}")