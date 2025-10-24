#!/usr/bin/env python3
"""
Test script for Gemini video analysis with real UGC clip

This script tests the complete metadata generation pipeline:
1. Initialize TR authentication
2. Initialize Gemini enhancer
3. Analyze a real UGC video
4. Generate complete Reuters-style metadata
5. Display structured results

Usage:
    python scripts/test_video_analysis.py
"""

import sys
import os
import json

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.auth import initialize_auth
from modules.gemini_enhancer import GeminiEnhancer


def print_section(title: str):
    """Print a formatted section header"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_metadata(metadata: dict):
    """Print metadata in a formatted way"""
    
    print_section("GENERATED METADATA")
    
    # SLUG
    print("SLUG:")
    print(f"  {metadata.get('slug', 'N/A')}")
    print()
    
    # HEADLINE
    print("HEADLINE:")
    print(f"  {metadata.get('headline', 'N/A')}")
    print()
    
    # VIDEO SHOWS
    print("VIDEO SHOWS:")
    print(f"  {metadata.get('video_shows', 'N/A')}")
    print()
    
    # SHOTLIST
    print("SHOTLIST:")
    shotlist = metadata.get('shotlist', {})
    if shotlist:
        print(f"  {shotlist.get('dateline', 'N/A')}")
        print()
        for shot in shotlist.get('shots', []):
            print(f"  {shot.get('number')}. {shot.get('description')}")
    print()
    
    # STORY
    print("STORY:")
    story = metadata.get('story', 'N/A')
    if story:
        paragraphs = story.split('\\n\\n')
        for para in paragraphs:
            print(f"  {para}")
            print()
    
    # VERIFICATION
    print("VERIFICATION:")
    verification = metadata.get('verification', {})
    if verification:
        print(f"  Location: {verification.get('location_method', 'N/A')}")
        print(f"  Date: {verification.get('date_method', 'N/A')}")
        print(f"  Confidence: {verification.get('confidence', 'N/A')}")
    print()
    
    # TECHNICAL DETAILS
    print("TECHNICAL DETAILS:")
    print(f"  Duration: {metadata.get('duration_seconds', 'N/A')} seconds")
    print(f"  Quality: {metadata.get('quality', 'N/A')}")
    print(f"  Confidence Score: {metadata.get('confidence_score', 'N/A')}")
    print()
    
    # VISUAL ANALYSIS
    if 'visual_analysis' in metadata:
        print("VISUAL ANALYSIS:")
        print(f"  {metadata.get('visual_analysis', 'N/A')}")
        print()
    
    # AUDIO ANALYSIS
    if 'audio_analysis' in metadata:
        print("AUDIO ANALYSIS:")
        print(f"  {metadata.get('audio_analysis', 'N/A')}")
        print()


def main():
    """Main test function"""
    print_section("GEMINI VIDEO ANALYSIS TEST")
    
    # Configuration
    video_path = "test clips/026ad20256444e7d854a4e5b079b4b60_Bureij Oct 19 Normalised 50.mp4"
    event_context = "UGC showing smoke rising out of Gaza neighbourhood after Israeli airstrike"
    location = "Gaza"
    date = "October 19, 2024"
    source = "Video obtained by Reuters"
    restrictions = "Access all"
    
    print("Test Configuration:")
    print(f"  Video: {video_path}")
    print(f"  Context: {event_context}")
    print(f"  Location: {location}")
    print(f"  Date: {date}")
    print(f"  Source: {source}")
    print()
    
    try:
        # Step 1: Initialize authentication
        print("Step 1: Initializing TR authentication...")
        workspace_id, model_name = initialize_auth()
        print(f"✓ Authentication successful")
        print(f"  Workspace: {workspace_id}")
        print(f"  Model: {model_name}")
        print()
        
        # Step 2: Initialize Gemini enhancer
        print("Step 2: Initializing Gemini enhancer...")
        enhancer = GeminiEnhancer()
        print(f"✓ Gemini enhancer initialized")
        print()
        
        # Step 3: Generate metadata
        print("Step 3: Analyzing video and generating metadata...")
        print("  (This may take 30-60 seconds...)")
        print()
        
        metadata = enhancer.generate_metadata(
            video_path=video_path,
            event_context=event_context,
            location=location,
            date=date,
            source=source,
            restrictions=restrictions
        )
        
        print("✓ Metadata generated successfully!")
        
        # Step 4: Display results
        print_metadata(metadata)
        
        # Step 5: Save to file
        output_file = "test_output_metadata.json"
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print_section("SUCCESS")
        print(f"✓ Complete metadata generated and saved to: {output_file}")
        print()
        print("The Gemini video analysis pipeline is working correctly!")
        print()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ File Error: {e}")
        print("\nPlease ensure the video file exists in the 'test clips' folder.")
        return 1
        
    except Exception as e:
        print(f"\n✗ Analysis Failed: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
