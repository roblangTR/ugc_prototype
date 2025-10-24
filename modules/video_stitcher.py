"""
Video Stitcher Module

Handles video operations using FFmpeg:
- Convert slate image to 5-second video
- Concatenate slate + original video
- Get video properties
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class VideoStitcher:
    """Stitch slate and video using FFmpeg"""
    
    def __init__(self):
        """Initialize video stitcher"""
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("FFmpeg verified and ready")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg: brew install ffmpeg"
            )
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        Get video properties using ffprobe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with width, height, fps, duration
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-of', 'csv=p=0',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            parts = result.stdout.strip().split(',')
            
            width = int(parts[0])
            height = int(parts[1])
            
            # Parse frame rate (e.g., "25/1" -> 25)
            fps_str = parts[2]
            fps_parts = fps_str.split('/')
            fps = int(fps_parts[0]) // int(fps_parts[1]) if len(fps_parts) == 2 else 25
            
            # Duration
            duration = float(parts[3]) if len(parts) > 3 else 0
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'duration': duration
            }
        except Exception as e:
            logger.warning(f"Could not get video info, using defaults: {e}")
            return {'width': 1920, 'height': 1080, 'fps': 25, 'duration': 0}
    
    def image_to_video(
        self,
        image_path: str,
        output_path: str,
        duration: float = 5.0,
        fps: int = 25,
        resolution: Tuple[int, int] = (1920, 1080)
    ) -> str:
        """
        Convert slate image to 5-second video
        
        Args:
            image_path: Path to slate image
            output_path: Where to save slate video
            duration: Duration in seconds (default 5.0)
            fps: Frame rate (default 25)
            resolution: Resolution tuple (width, height)
            
        Returns:
            Path to slate video
        """
        logger.info(f"Converting slate image to {duration}s video")
        
        width, height = resolution
        
        # Use pre-generated silent audio file for faster, more reliable slate creation
        silent_audio = 'app/assets/silent_5s.aac'
        
        cmd = [
            'ffmpeg',
            '-loop', '1',                          # Loop the image
            '-i', image_path,                      # Input image
            '-i', silent_audio,                    # Pre-made silent audio
            '-c:v', 'libx264',                     # Video codec
            '-c:a', 'copy',                        # Copy silent audio (no re-encode)
            '-t', str(duration),                   # Duration
            '-pix_fmt', 'yuv420p',                 # Pixel format for compatibility
            '-r', str(fps),                        # Frame rate
            '-s', f'{width}x{height}',             # Resolution
            '-shortest',                           # Stop at shortest stream
            '-y',                                  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Slate video created: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to create slate video: {error_msg}")
            raise RuntimeError(f"FFmpeg failed: {error_msg}")
    
    def concatenate_videos(
        self,
        slate_video_path: str,
        original_video_path: str,
        output_path: str
    ) -> str:
        """
        Concatenate slate video with original video
        
        Args:
            slate_video_path: Path to slate video
            original_video_path: Path to original UGC video
            output_path: Where to save final concatenated video
            
        Returns:
            Path to final video
        """
        logger.info("Concatenating slate and original video")
        
        # Use filter_complex concat for both video and audio
        # Slate has silent audio, original has real audio
        cmd = [
            'ffmpeg',
            '-i', slate_video_path,                # Input 1: slate (with silent audio)
            '-i', original_video_path,             # Input 2: original (with audio)
            '-filter_complex',
            '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]',  # Concat both streams
            '-map', '[outv]',                      # Map concatenated video
            '-map', '[outa]',                      # Map concatenated audio
            '-c:v', 'libx264',                     # Encode video
            '-preset', 'fast',                     # Fast encoding
            '-crf', '18',                          # High quality
            '-c:a', 'aac',                         # Encode audio
            '-b:a', '192k',                        # Audio bitrate
            '-y',                                  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Final video created: {output_path}")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to concatenate videos: {error_msg}")
            raise RuntimeError(f"FFmpeg concatenation failed: {error_msg}")
