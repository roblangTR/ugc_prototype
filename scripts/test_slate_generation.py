#!/usr/bin/env python3
"""
Test slate generation with real Gaza video

This script tests the complete slate workflow:
1. Load existing metadata
2. Generate slate image
3. Convert slate to video
4. Stitch slate + original video
5. Verify output
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.slate_workflow import SlateWorkflow


def main():
    """Test slate generation"""
    print("=" * 70)
    print("SLATE GENERATION TEST")
    print("=" * 70)
    print()
    
    # Configuration
    guid = "F29000"
    metadata_file = "test_output_metadata.json"
    video_file = "test clips/Bureij Oct 19 Normalised 50.mp4"
    output_file = "final_videos/test_final_with_slate.mp4"
    background_image = "app/assets/reuters_slate_background.jpg"
    
    print(f"Configuration:")
    print(f"  GUID: {guid}")
    print(f"  Metadata: {metadata_file}")
    print(f"  Video: {video_file}")
    print(f"  Output: {output_file}")
    print(f"  Background: {background_image}")
    print()
    
    try:
        # Step 1: Verify files exist
        print("Step 1: Verifying files...")
        
        if not os.path.exists(metadata_file):
            print(f"  ✗ Metadata file not found: {metadata_file}")
            return 1
        print(f"  ✓ Metadata file exists")
        
        if not os.path.exists(video_file):
            print(f"  ✗ Video file not found: {video_file}")
            return 1
        print(f"  ✓ Video file exists")
        
        if not os.path.exists(background_image):
            print(f"  ✗ Background image not found: {background_image}")
            return 1
        print(f"  ✓ Background image exists")
        print()
        
        # Step 2: Load metadata
        print("Step 2: Loading metadata...")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        print(f"  ✓ Metadata loaded")
        print(f"    SLUG: {metadata.get('slug', 'N/A')}")
        print(f"    Duration: {metadata.get('duration_seconds', 'N/A')}s")
        print()
        
        # Step 3: Initialize slate workflow
        print("Step 3: Initializing slate workflow...")
        workflow = SlateWorkflow(
            background_image_path=background_image,
            work_dir="temp/test_slate"
        )
        print(f"  ✓ Slate workflow initialized")
        print()
        
        # Step 4: Validate GUID
        print("Step 4: Validating GUID...")
        is_valid = workflow.validate_guid(guid)
        if not is_valid:
            print(f"  ✗ Invalid GUID: {guid}")
            return 1
        
        edit_number = workflow.extract_edit_number(guid)
        print(f"  ✓ GUID valid")
        print(f"    Edit Number: {edit_number}")
        print()
        
        # Step 5: Generate slate and stitch video
        print("Step 5: Generating slate and stitching video...")
        print("  (This may take 30-60 seconds...)")
        print()
        
        result = workflow.generate_final_video(
            guid=guid,
            metadata=metadata,
            original_video_path=video_file,
            output_video_path=output_file,
            cleanup=False  # Keep intermediate files for debugging
        )
        
        print(f"  ✓ Slate generation complete!")
        print()
        
        # Step 6: Display results
        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print()
        print(f"Edit Number: {result['edit_number']}")
        print(f"Resolution: {result['resolution']}")
        print(f"Original Duration: {result['original_duration']}")
        print(f"Duration with Slate: {result['duration_with_slate']}")
        print(f"Final Video: {result['final_video']}")
        print()
        print(f"Intermediate files (for debugging):")
        print(f"  - temp/test_slate/slate_{edit_number}.png")
        print(f"  - temp/test_slate/slate_{edit_number}.mp4")
        print()
        print(f"To view the final video:")
        print(f"  open '{output_file}'")
        print()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ File Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
