"""
Reuters Slate Generator Module

Generates Reuters-branded video slates by overlaying text on a background image.
Uses pre-designed Reuters background JPEG with gradient and branding.
"""

import os
import logging
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class SlateGenerator:
    """Generate Reuters video slate with metadata overlay"""
    
    # Reuters brand colors
    TITLE_COLOR = (242, 144, 0)  # #F29000 - Gold/Amber for title
    WHITE = (255, 255, 255)      # #FFFFFF
    
    # Layout constants (coordinates for 1920x1080)
    EDIT_NUMBER_POS = (130, 100)
    SLUG_POS = (130, 200)
    CONTENT_START_Y = 320
    LINE_HEIGHT = 65
    
    def __init__(
        self, 
        background_image_path: str,
        resolution: Tuple[int, int] = (1920, 1080)
    ):
        """
        Initialize slate generator
        
        Args:
            background_image_path: Path to Reuters slate background JPEG
            resolution: Video resolution (width, height)
        """
        self.background_image_path = background_image_path
        self.resolution = resolution
        self.width, self.height = resolution
        
        # Verify background image exists
        if not os.path.exists(background_image_path):
            raise FileNotFoundError(
                f"Background image not found: {background_image_path}"
            )
        
        logger.info(f"SlateGenerator initialized")
        logger.info(f"  Background: {background_image_path}")
        logger.info(f"  Resolution: {resolution}")
    
    def _load_background(self) -> Image.Image:
        """Load and resize background image to match video resolution"""
        try:
            img = Image.open(self.background_image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to match target resolution
            if img.size != self.resolution:
                img = img.resize(self.resolution, Image.Resampling.LANCZOS)
                logger.info(f"Resized background to {self.resolution}")
            
            return img
        except Exception as e:
            logger.error(f"Failed to load background image: {e}")
            raise
    
    def _get_font(self, size: int, bold: bool = True):
        """Get font with fallback options"""
        font_paths = [
            # macOS
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        # Fallback to default
        logger.warning(f"Could not load system font, using default")
        return ImageFont.load_default()
    
    def generate_slate(
        self,
        edit_number: str,
        slug: str,
        location: str,
        duration: str,
        date_shot: str,
        sound: str,
        restrictions_broadcast: str,
        restrictions_digital: str,
        output_path: str
    ) -> str:
        """
        Generate slate image with all metadata
        
        Args:
            edit_number: 4-digit edit number from GUID
            slug: Story slug
            location: Location string
            duration: Duration (e.g., "1:30")
            date_shot: Date in Reuters format
            sound: Sound description
            restrictions_broadcast: Broadcast restrictions
            restrictions_digital: Digital restrictions
            output_path: Where to save the slate image
            
        Returns:
            Path to generated slate image
        """
        logger.info(f"Generating slate for edit {edit_number}")
        
        # Load background image
        img = self._load_background()
        draw = ImageDraw.Draw(img)
        
        # Get fonts
        font_120 = self._get_font(120, bold=True)
        font_80 = self._get_font(80, bold=True)
        font_48 = self._get_font(48, bold=True)
        
        # Add edit number / slug (gold/amber, large) - combined on one line
        combined_title = f"{edit_number} / {slug}"
        draw.text(self.EDIT_NUMBER_POS, combined_title, font=font_80, fill=self.TITLE_COLOR)
        
        # Add content fields (white text)
        y_pos = self.CONTENT_START_Y
        
        # Location
        draw.text((130, y_pos), f"LOCATION: {location}", font=font_48, fill=self.WHITE)
        y_pos += self.LINE_HEIGHT
        
        # Duration
        draw.text((130, y_pos), f"Duration: {duration}", font=font_48, fill=self.WHITE)
        y_pos += self.LINE_HEIGHT
        
        # Date Shot
        draw.text((130, y_pos), f"Date Shot: {date_shot}", font=font_48, fill=self.WHITE)
        y_pos += self.LINE_HEIGHT
        
        # Sound (just the audio type, not description)
        draw.text((130, y_pos), sound, font=font_48, fill=self.WHITE)
        y_pos += self.LINE_HEIGHT
        
        # Restrictions (combined on one line)
        draw.text((130, y_pos), f"Restrictions: {restrictions_broadcast}", font=font_48, fill=self.WHITE)
        
        # Save image
        img.save(output_path, 'PNG')
        logger.info(f"Slate saved to {output_path}")
        
        return output_path
