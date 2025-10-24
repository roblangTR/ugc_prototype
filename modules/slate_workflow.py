"""
Slate Workflow Module

Complete workflow for slate generation and video stitching.
Orchestrates SlateGenerator and VideoStitcher.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

from modules.slate_generator import SlateGenerator
from modules.video_stitcher import VideoStitcher

logger = logging.getLogger(__name__)


class SlateWorkflow:
    """Complete workflow for slate generation and video stitching"""
    
    def __init__(
        self, 
        background_image_path: str,
        work_dir: str = "temp/slate_work"
    ):
        """
        Initialize slate workflow
        
        Args:
            background_image_path: Path to Reuters slate background JPEG
            work_dir: Working directory for temporary files
        """
        self.background_image_path = background_image_path
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify background image exists
        if not os.path.exists(background_image_path):
            raise FileNotFoundError(
                f"Slate background image not found: {background_image_path}\n"
                f"Please ensure reuters_slate_background.jpg exists in app/assets/"
            )
        
        self.video_stitcher = VideoStitcher()
        
        logger.info(f"SlateWorkflow initialized")
        logger.info(f"  Background: {background_image_path}")
        logger.info(f"  Work dir: {work_dir}")
    
    def validate_guid(self, guid: str) -> bool:
        """
        Validate GUID format
        
        Args:
            guid: GUID string to validate
            
        Returns:
            True if valid (at least 4 hex characters), False otherwise
        """
        # Remove hyphens and spaces
        guid_clean = guid.replace('-', '').replace(' ', '')
        
        # Check length
        if len(guid_clean) < 4:
            return False
        
        # Check first 4 chars are hex
        try:
            int(guid_clean[:4], 16)
            return True
        except ValueError:
            return False
    
    def extract_edit_number(self, guid: str) -> str:
        """
        Extract 4-digit edit number from GUID
        
        Args:
            guid: GUID string (e.g., "1234-5678-9ABC-DEF0")
            
        Returns:
            4-character edit number (e.g., "1234")
        """
        guid_clean = guid.replace('-', '').replace(' ', '').upper()
        return guid_clean[:4]
    
    def generate_final_video(
        self,
        guid: str,
        metadata: Dict[str, Any],
        original_video_path: str,
        output_video_path: str,
        cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Complete workflow: Generate slate and stitch to video
        
        Args:
            guid: GUID for edit number
            metadata: Complete metadata dictionary
            original_video_path: Path to original UGC video
            output_video_path: Where to save final video
            cleanup: Whether to delete intermediate files
            
        Returns:
            Dictionary with results and file paths
        """
        logger.info(f"Starting slate workflow for GUID: {guid}")
        
        # Validate GUID
        if not self.validate_guid(guid):
            raise ValueError(f"Invalid GUID format: {guid}")
        
        # Extract edit number
        edit_number = self.extract_edit_number(guid)
        logger.info(f"Edit number: {edit_number}")
        
        # Get video properties
        video_info = self.video_stitcher.get_video_info(original_video_path)
        resolution = (video_info['width'], video_info['height'])
        fps = video_info['fps']
        
        logger.info(f"Video info: {resolution[0]}x{resolution[1]} @ {fps}fps")
        
        # Create slate generator with correct resolution
        slate_gen = SlateGenerator(
            background_image_path=self.background_image_path,
            resolution=resolution
        )
        
        # Generate slate image
        slate_image_path = self.work_dir / f"slate_{edit_number}.png"
        
        # Extract metadata for slate
        slug = metadata.get('slug', 'UNKNOWN-SLUG')
        location = metadata.get('input_metadata', {}).get('location', 'UNKNOWN')
        
        # Get duration from metadata or calculate
        duration = metadata.get('duration_seconds', 0)
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "0:00"
        
        date_shot = metadata.get('input_metadata', {}).get('date', 'UNKNOWN DATE').upper()
        
        # Determine audio format: Mute, Natural, or Natural/Language
        audio_analysis = metadata.get('audio_analysis', '')
        languages = metadata.get('languages_detected', [])
        
        if 'mute' in audio_analysis.lower() or not audio_analysis:
            sound = 'MUTE'
        elif languages and len(languages) > 0:
            # Has speech - list languages
            lang_str = ' AND '.join([lang.upper() for lang in languages])
            sound = f'NATURAL WITH {lang_str} SPEECH'
        else:
            # Natural sound, no speech
            sound = 'NATURAL'
        
        restrictions = metadata.get('input_metadata', {}).get('restrictions', 'Access all')
        
        slate_gen.generate_slate(
            edit_number=edit_number,
            slug=slug,
            location=location.upper(),
            duration=duration_str,
            date_shot=date_shot,
            sound=sound,
            restrictions_broadcast=restrictions,
            restrictions_digital=restrictions,
            output_path=str(slate_image_path)
        )
        
        logger.info(f"Slate image generated: {slate_image_path}")
        
        # Convert slate to video
        slate_video_path = self.work_dir / f"slate_{edit_number}.mp4"
        self.video_stitcher.image_to_video(
            image_path=str(slate_image_path),
            output_path=str(slate_video_path),
            duration=5.0,
            fps=fps,
            resolution=resolution
        )
        
        logger.info(f"Slate video created: {slate_video_path}")
        
        # Concatenate videos
        final_video = self.video_stitcher.concatenate_videos(
            slate_video_path=str(slate_video_path),
            original_video_path=original_video_path,
            output_path=output_video_path
        )
        
        logger.info(f"Final video created: {final_video}")
        
        # Calculate new duration
        new_duration = duration + 5
        new_minutes = int(new_duration // 60)
        new_seconds = int(new_duration % 60)
        duration_with_slate = f"{new_minutes}:{new_seconds:02d}"
        
        # Cleanup intermediate files
        if cleanup:
            try:
                if slate_image_path.exists():
                    slate_image_path.unlink()
                if slate_video_path.exists():
                    slate_video_path.unlink()
                logger.info("Cleaned up intermediate files")
            except Exception as e:
                logger.warning(f"Failed to cleanup: {e}")
        
        return {
            'success': True,
            'edit_number': edit_number,
            'final_video': final_video,
            'resolution': resolution,
            'duration_with_slate': duration_with_slate,
            'original_duration': duration_str
        }
