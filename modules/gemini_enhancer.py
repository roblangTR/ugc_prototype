"""
Gemini Video Enhancer Module

This module handles video analysis using Google Gemini via Vertex AI
with Thomson Reuters authentication.

Based on TR Authentication & Gemini Integration specification.
"""

import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials as OAuth2Credentials
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from modules.auth import get_auth_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeminiEnhancer:
    """
    Handle video enhancement using Gemini API via Vertex AI SDK
    with Thomson Reuters authentication.
    
    This class provides:
    - Vertex AI initialization with TR credentials
    - Video analysis with Gemini Flash 2.5
    - Structured output parsing
    - Retry logic for connection errors
    """
    
    def __init__(self):
        """Initialize the Gemini enhancer with TR auth"""
        self.auth = get_auth_instance()
        self.model = None
        self._initialize_vertex()
        logger.info(f"Gemini enhancer initialized with model: {self.auth.model_name}")
    
    def _initialize_vertex(self):
        """Initialize Vertex AI with Thomson Reuters credentials"""
        try:
            logger.info("[VERTEX] Initializing Vertex AI with TR credentials")
            
            # Get credentials from auth module
            creds_data = self.auth.get_credentials()
            
            # Create OAuth2 credentials from TR token
            temp_creds = OAuth2Credentials(creds_data['token'])
            
            # Initialize Vertex AI
            vertexai.init(
                project=creds_data['project_id'],
                location=creds_data['region'],
                credentials=temp_creds
            )
            
            # Load system instruction
            system_instruction = self._load_system_instruction()
            
            # Create the model
            self.model = GenerativeModel(
                model_name=self.auth.model_name,
                system_instruction=system_instruction
            )
            
            logger.info(f"[VERTEX] ✓ Initialized successfully")
            logger.info(f"[VERTEX] Project: {creds_data['project_id']}")
            logger.info(f"[VERTEX] Region: {creds_data['region']}")
            logger.info(f"[VERTEX] Model: {self.auth.model_name}")
            
        except Exception as e:
            logger.error(f"[VERTEX] ✗ Initialization failed: {e}")
            raise RuntimeError(f"Vertex AI initialization failed: {e}")
    
    def _load_system_instruction(self) -> str:
        """Load system instruction for the model"""
        instruction = """You are an expert video analyst specializing in news and documentary footage analysis.

Your task is to analyze video clips and provide detailed, structured metadata in JSON format.

For each video clip, you should:
1. Provide an enhanced natural language description of what you see
2. Classify the shot type, size, and camera movement
3. Describe the composition and lighting
4. Identify primary subjects and actions
5. Assess visual quality
6. Determine the tone and news context

Be precise, objective, and thorough in your analysis. Focus on visual elements that would be important for video editing and news production."""
        
        return instruction
    
    def enhance_clip(
        self,
        video_path: str,
        shotlist: Dict[str, Any],
        clip_id: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Enhance a video clip with Gemini analysis and intelligent shot matching
        
        Args:
            video_path: Path to the video file
            shotlist: Complete shotlist dictionary with all shots and header
            clip_id: Identifier for the clip
            context: Additional context about the video
            
        Returns:
            Dictionary containing enhanced metadata with matched shot numbers and dateline info
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If analysis fails after retries
        """
        try:
            # Verify file exists
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Read video file
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            file_size_mb = len(video_data) / 1024 / 1024
            logger.info(f"Processing clip {clip_id}: {video_path} ({file_size_mb:.2f} MB)")
            
            # Check file size limit (Gemini has a ~20MB limit for video)
            if file_size_mb > 15:
                logger.warning(f"Clip {clip_id} is large ({file_size_mb:.2f} MB), may fail")
            
            # Determine MIME type
            file_ext = Path(video_path).suffix.lower()
            mime_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska'
            }
            mime_type = mime_type_map.get(file_ext, 'video/mp4')
            
            # Create video part
            video_part = Part.from_data(data=video_data, mime_type=mime_type)
            
            # Build prompt with full shotlist
            prompt = self._build_prompt(shotlist, clip_id, context)
            
            # Generate content with retry logic
            result = self._generate_with_retry(prompt, video_part, clip_id)
            
            # Add dateline metadata from matched shot(s)
            result = self._add_dateline_metadata(result, shotlist)
            
            logger.info(f"Successfully enhanced clip {clip_id}")
            return result
            
        except FileNotFoundError as e:
            logger.error(f"File not found for clip {clip_id}: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error enhancing clip {clip_id}: {e}")
            raise
    
    def _build_prompt(
        self,
        shotlist: Dict[str, Any],
        clip_id: str,
        context: str
    ) -> str:
        """Build analysis prompt with shotlist context"""
        
        prompt = f"""Analyze this video clip and provide detailed metadata.

CLIP ID: {clip_id}

CONTEXT: {context if context else 'No additional context provided'}

SHOTLIST REFERENCE:
{json.dumps(shotlist, indent=2)}

YOUR TASK:
Analyze the video and provide:

1. VISUAL ANALYSIS:
   - Detailed description of what you see
   - Shot-by-shot breakdown if multiple scenes
   - Key visual elements (people, objects, locations)
   - Any visible text or signs
   - Lighting and composition notes

2. AUDIO ANALYSIS:
   - Languages spoken (if any)
   - Transcription of speech (with timestamps if possible)
   - Ambient sounds (gunfire, explosions, sirens, crowd noise, etc.)
   - Audio quality notes

3. SHOT MATCHING:
   - Which shot number(s) from the shotlist does this clip match?
   - Is this a slate/title card? (true/false)
   - Is this part of a "VARIOUS" shot? (true/false)

4. METADATA:
   - Primary subject/action
   - News category (conflict, protest, disaster, etc.)
   - Emotional tone
   - Visual quality assessment

Return your analysis as a JSON object with this structure:
{{
  "clip_id": "{clip_id}",
  "matched_shot_numbers": [1, 2],  // Array of shot numbers this clip matches
  "is_slate": false,
  "is_part_of_various": false,
  "original_description": "Brief description",
  "enhanced_description": "Detailed description of visual content",
  "audio_summary": "Description of audio elements",
  "languages_detected": ["English"],
  "transcription": "Transcribed speech if any",
  "ambient_sounds": ["gunfire", "sirens"],
  "primary_subject": "Main subject",
  "key_action": "Main action",
  "news_category": "conflict/protest/disaster/etc",
  "emotional_tone": "urgent/calm/tense/etc",
  "visual_quality": "HD/SD/poor/excellent",
  "confidence_score": 0.85
}}

Provide ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _generate_with_retry(
        self,
        prompt: str,
        video_part: Part,
        clip_id: str
    ) -> Dict[str, Any]:
        """Generate content with retry logic for connection errors"""
        
        max_retries = int(os.getenv('GEMINI_MAX_RETRIES', '3'))
        retry_delay = int(os.getenv('GEMINI_RETRY_DELAY_SECONDS', '5'))
        
        generation_config = {
            "temperature": float(os.getenv('GEMINI_TEMPERATURE', '0.4')),
            "top_p": float(os.getenv('GEMINI_TOP_P', '0.5')),
            "top_k": int(os.getenv('GEMINI_TOP_K', '20')),
            "max_output_tokens": int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192')),
            "response_mime_type": "text/plain",
        }
        
        logger.info(f"Sending clip {clip_id} to Gemini for analysis...")
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    [prompt, video_part],
                    generation_config=generation_config
                )
                
                # Extract JSON from response
                response_text = response.text
                logger.info(f"Received response for clip {clip_id}")
                
                # Parse JSON response
                result = self._parse_json_response(response_text, clip_id)
                return result
                
            except (BrokenPipeError, ConnectionError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(
                        f"Connection error for clip {clip_id} "
                        f"(attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed after {max_retries} attempts for clip {clip_id}: {e}"
                    )
                    raise RuntimeError(f"Max retries exceeded: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error for clip {clip_id}: {e}")
                raise
        
        # Should not reach here, but just in case
        raise RuntimeError(f"Failed to generate content: {last_error}")
    
    def _parse_json_response(
        self,
        response_text: str,
        clip_id: str
    ) -> Dict[str, Any]:
        """Parse JSON response from Gemini"""
        
        try:
            # Try to extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
            
            # Ensure required fields are present
            if 'clip_id' not in result:
                result['clip_id'] = clip_id
            if 'matched_shot_numbers' not in result:
                result['matched_shot_numbers'] = []
            if 'is_slate' not in result:
                result['is_slate'] = False
            if 'is_part_of_various' not in result:
                result['is_part_of_various'] = False
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for clip {clip_id}: {e}")
            logger.error(f"Response text: {response_text}")
            
            # Return a fallback response
            return {
                'clip_id': clip_id,
                'matched_shot_numbers': [],
                'is_slate': False,
                'is_part_of_various': False,
                'original_description': 'Unknown',
                'enhanced_description': response_text,
                'error': 'Failed to parse structured response',
                'raw_response': response_text
            }
    
    def _add_dateline_metadata(
        self,
        result: Dict[str, Any],
        shotlist: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add dateline metadata from matched shot(s)"""
        
        matched_nums = result.get('matched_shot_numbers', [])
        
        if matched_nums:
            # Get metadata from first matched shot
            shots = shotlist.get('shots', [])
            for shot in shots:
                if shot.get('number') in matched_nums:
                    result['location'] = shot.get('location', '')
                    result['date'] = shot.get('date', '')
                    result['source'] = shot.get('source', '')
                    result['restrictions'] = shot.get('restrictions', '')
                    break
        else:
            # Fallback to header if no match
            header = shotlist.get('header', {})
            result['location'] = header.get('location', '')
            result['date'] = header.get('date', '')
            result['source'] = header.get('source', '')
            result['restrictions'] = header.get('restrictions', '')
        
        return result
    
    def generate_metadata(
        self,
        video_path: str,
        event_context: str,
        location: str,
        date: str,
        source: str,
        restrictions: str = "Access all"
    ) -> Dict[str, Any]:
        """
        Generate complete Reuters-style metadata from a UGC video
        
        Args:
            video_path: Path to the video file
            event_context: Brief description of the event (e.g., "UGC showing smoke rising...")
            location: Location of the event (e.g., "Gaza", "Nairobi, Kenya")
            date: Date of the event (e.g., "October 19, 2024")
            source: Source of the video (e.g., "Video obtained by Reuters")
            restrictions: Usage restrictions (default: "Access all")
            
        Returns:
            Dictionary containing complete Reuters metadata:
            - slug
            - headline
            - video_shows
            - shotlist (with dateline and numbered shots)
            - story (3-4 paragraphs)
            - verification notes
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If analysis fails after retries
        """
        try:
            # Verify file exists
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Read video file
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            file_size_mb = len(video_data) / 1024 / 1024
            logger.info(f"Generating metadata for: {video_path} ({file_size_mb:.2f} MB)")
            
            # Check file size limit
            if file_size_mb > 15:
                logger.warning(f"Video is large ({file_size_mb:.2f} MB), may fail")
            
            # Determine MIME type
            file_ext = Path(video_path).suffix.lower()
            mime_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska'
            }
            mime_type = mime_type_map.get(file_ext, 'video/mp4')
            
            # Create video part
            video_part = Part.from_data(data=video_data, mime_type=mime_type)
            
            # Build metadata generation prompt
            prompt = self._build_metadata_prompt(
                event_context, location, date, source, restrictions
            )
            
            # Generate content with retry logic
            result = self._generate_with_retry(prompt, video_part, "metadata_generation")
            
            # Add input metadata
            result['input_metadata'] = {
                'event_context': event_context,
                'location': location,
                'date': date,
                'source': source,
                'restrictions': restrictions
            }
            
            logger.info(f"Successfully generated metadata for video")
            return result
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            raise
    
    def _build_metadata_prompt(
        self,
        event_context: str,
        location: str,
        date: str,
        source: str,
        restrictions: str
    ) -> str:
        """Build prompt for generating complete Reuters metadata"""
        
        prompt = f"""Analyze this UGC video and generate complete Reuters-style metadata.

EVENT CONTEXT: {event_context}

LOCATION: {location}
DATE: {date}
SOURCE: {source}
RESTRICTIONS: {restrictions}

YOUR TASK:
Generate complete Reuters-compliant metadata following these strict guidelines:

1. SLUG (Reuters format):
   - Format: CATEGORY-SUBCATEGORY/SPECIFIC-DETAIL
   - All caps, use hyphens, max 40 characters
   - Examples: "ISRAEL-PALESTINIANS/GAZA-STRIKE-UGC", "KENYA-ODINGA/TEARGAS-UGC"
   - Add UGC suffix if user-generated content

2. HEADLINE (Reuters style):
   - 6-8 words exactly
   - Present tense, active voice
   - Start with "Eyewitness video shows" or "Social media video shows"
   - Include location
   - Clear and punchy

3. VIDEO SHOWS (all caps):
   - Use -ing verb forms: RISING, SHOWING, FIRING, WALKING
   - Separate sequences with semicolons or slashes
   - Max 2 lines
   - Example: "SMOKE RISING FROM DESTROYED BUILDINGS / DEBRIS ON GROUND"

4. SHOTLIST (Reuters format):
   - Start with DATELINE: LOCATION (DATE) (SOURCE – Restrictions)
   - Number each shot (1., 2., 3., etc.)
   - Use -ing verbs for descriptions
   - Describe action, NOT camera movements
   - DO NOT use: CUTAWAY, WIDE, PAN, TILT, VIEW OF
   - Use "/" for shot changes within same sequence
   - Use "," for multiple elements in one shot
   - Example format:
     DATELINE: {location.upper()} ({date.upper()}) ({source.upper()} – {restrictions})
     1. SMOKE RISING FROM DESTROYED BUILDINGS
     2. DEBRIS SCATTERED ON STREET / DAMAGED VEHICLES

5. STORY (Reuters news style):
   - 3-4 paragraphs
   - Paragraph 1: Lead - What happened, where, when (most important first)
   - Paragraph 2: Context - Why it matters, background
   - Paragraph 3: Details - Description matching video content
   - Paragraph 4: Verification - How Reuters verified location/date
   - Simple past tense: "said," "fired," "killed"
   - Include date with day name if known
   - British English spelling
   - Factual and impartial
   - Must include verification statement

6. VERIFICATION:
   - How location was verified (buildings, landmarks, satellite imagery, etc.)
   - How date was verified (file metadata, corroborating reports, etc.)

Return your analysis as a JSON object with this structure:
{{
  "slug": "ISRAEL-PALESTINIANS/GAZA-STRIKE-UGC",
  "headline": "Eyewitness video shows smoke rising after Gaza airstrike",
  "video_shows": "SMOKE RISING FROM DESTROYED BUILDINGS / DEBRIS ON GROUND",
  "shotlist": {{
    "dateline": "GAZA (OCTOBER 19, 2024) (VIDEO OBTAINED BY REUTERS – Access all)",
    "shots": [
      {{
        "number": 1,
        "description": "SMOKE RISING FROM DESTROYED BUILDINGS"
      }},
      {{
        "number": 2,
        "description": "DEBRIS SCATTERED ON STREET / DAMAGED VEHICLES"
      }}
    ]
  }},
  "story": "Israeli forces struck a neighbourhood in Gaza on Saturday (October 19), according to eyewitness footage obtained by Reuters.\\n\\nThe video showed smoke rising from destroyed buildings with debris scattered across the street.\\n\\nReuters was able to independently verify the location by matching building structures and street layout with satellite imagery. The date was verified from the original file metadata.",
  "verification": {{
    "location_method": "Building structures and street layout matched satellite imagery",
    "date_method": "Original file metadata",
    "confidence": "high"
  }},
  "visual_analysis": "Detailed description of what you see in the video",
  "audio_analysis": "Description of any sounds, speech, or ambient audio",
  "duration_seconds": 50,
  "quality": "HD/SD",
  "confidence_score": 0.85
}}

IMPORTANT: Follow Reuters style guidelines exactly. Use present tense for headlines, past tense for stories. Use -ing verbs in shotlist. Be factual and impartial.

Provide ONLY the JSON object, no additional text."""
        
        return prompt
    
    def reinitialize(self):
        """Reinitialize Vertex AI (e.g., after token refresh)"""
        logger.info("[VERTEX] Reinitializing with refreshed credentials")
        self._initialize_vertex()
        logger.info("[VERTEX] ✓ Reinitialized successfully")


if __name__ == "__main__":
    # Test Gemini enhancer when run directly
    from modules.auth import initialize_auth
    
    try:
        print("Testing Gemini Enhancer...")
        print()
        
        # Initialize authentication
        print("Step 1: Initializing authentication...")
        workspace_id, model_name = initialize_auth()
        print(f"✓ Authentication successful")
        print(f"  Workspace: {workspace_id}")
        print(f"  Model: {model_name}")
        print()
        
        # Create Gemini enhancer
        print("Step 2: Initializing Gemini enhancer...")
        enhancer = GeminiEnhancer()
        print(f"✓ Gemini enhancer initialized")
        print()
        
        print("=" * 70)
        print("✓ Gemini enhancer ready for video analysis!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Provide a video file path")
        print("  2. Provide shotlist context")
        print("  3. Call enhancer.enhance_clip() to analyze")
        print()
        
    except Exception as e:
        print(f"\n✗ Gemini enhancer test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
