# UGC Video Metadata Generation App - Technical Proposal

## Executive Summary

This application will streamline the process of preparing user-generated content (UGC) videos for publication by Reuters journalists. By leveraging Google Gemini Flash 2.5's multi-modal capabilities, the system will analyze video content and generate Reuters-compliant metadata, shotlists, headlines, and scripts.

---

## Architecture Overview

### 1. User Input Collection Layer

A multi-step form interface to gather essential metadata before AI processing:

#### **Step 1: User & Story Information**
- **User name** (for attribution)
- **User email** (for tracking/contact)
- **Story context** (free text field describing the story background)
- **Date of incident** (date picker with manual override)

#### **Step 2: Source & Rights**
- **Source** (with template options):
  - "Video obtained by Reuters"
  - "Social Media - Twitter @username"
  - "Social Media - Instagram @username"
  - "Facebook User"
  - Custom input field
- **Restrictions** (template-based selector):
  - No restrictions (Access all)
  - No resale / No archive / Must on-screen courtesy [Source]
  - Custom restriction builder for complex cases

#### **Step 3: Location Details**
- **Country** (dropdown with search)
- **City/Region** (autocomplete based on country)
- **Specific location** (free text for precise details)
- **Location confidence** (High/Medium/Low)

#### **Step 4: Verification**
- **Location verified by:**
  - [ ] Building structures matched satellite imagery
  - [ ] Landmarks identified
  - [ ] Street layout matched mapping data
  - [ ] Topography matched terrain data
  - [ ] Corroborating footage
  - [ ] Other (specify)
  
- **Date verified by:**
  - [ ] Original file metadata
  - [ ] Corroborating reports
  - [ ] Known events on that date
  - [ ] Weather data
  - [ ] Could not be independently verified
  - [ ] Other (specify)

- **Additional verification notes** (free text)

#### **Step 5: Video Upload**
- File upload interface with drag-and-drop
- Support formats: MP4, MOV, AVI, MKV
- Progress indicator
- Automatic technical metadata extraction:
  - Duration
  - Resolution (SD/HD)
  - Aspect ratio (16:9, 4:3, Portrait)
  - Audio channels/languages detected

---

### 2. AI Processing Pipeline (Google Gemini Flash 2.5)

#### **Authentication & Access**
This application uses **Thomson Reuters' centralized authentication system** to access Google Gemini via Vertex AI. 

**Key Components:**
- TR Authentication Service provides temporary OAuth2 tokens
- Tokens include: workspace_id, project_id, region
- Automatic token refresh mechanism (every 50 minutes)
- Secure credential management via environment variables

**For detailed authentication implementation, see:** [TR Authentication & Gemini Integration Guide](./tr-authentication-gemini-integration.md)

#### **Why Gemini Flash 2.5?**
- Native video understanding (up to 1 hour of video content)
- Fast processing speed suitable for breaking news
- Multi-modal capabilities (video, audio, text)
- Cost-effective for production deployment
- Strong instruction-following for structured output
- Integrated with TR authentication infrastructure

#### **Processing Workflow**

```
User Authentication (TR System)
    ↓
Initialize TR Auth Module
    ├── Get workspace_id, model_name from env
    ├── Request token from CREDENTIALS_URL
    └── Receive: token, project_id, region
    ↓
Video Upload
    ↓
Technical Analysis
    ├── Extract metadata (duration, resolution, codec)
    ├── Detect aspect ratio
    └── Identify audio tracks/languages
    ↓
Initialize Vertex AI with TR Credentials
    ├── Create OAuth2Credentials(token)
    ├── vertexai.init(project_id, region, credentials)
    └── Load GenerativeModel
    ↓
Gemini Flash 2.5 Analysis
    ├── Frame-by-frame visual analysis
    ├── Action/event detection
    ├── Object/person identification
    ├── Audio transcription (if speech present)
    ├── Ambient sound identification
    └── Temporal sequencing
    ↓
Structured Metadata Generation
    ├── SLUG
    ├── HEADLINE
    ├── INTRO
    ├── VIDEO SHOWS
    ├── SHOTLIST
    └── STORY
    ↓
Validation & Quality Checks
    ↓
Present to Journalist for Review
```

#### **Gemini Flash 2.5 Implementation**

**Authentication Setup:**
```python
# Initialize TR authentication system
from modules.auth import initialize_auth, get_auth_instance

# On app startup
workspace_id, model_name = initialize_auth()
print(f"✓ TR Authentication successful")
print(f"  Workspace: {workspace_id}")
print(f"  Model: {model_name}")
```

**Video Processing Strategy:**
```python
# Using TR authentication with Gemini
from modules.gemini_enhancer import GeminiEnhancer
from google.oauth2.credentials import Credentials as OAuth2Credentials
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# Create enhancer (handles TR auth internally)
enhancer = GeminiEnhancer()

# Process video
result = enhancer.enhance_clip(
    video_path="path/to/ugc_video.mp4",
    shotlist=shotlist_dict,
    clip_id="clip_001",
    context="User provided context"
)
```

**Internal Implementation (in GeminiEnhancer):**
```python
def _initialize_vertex(self):
    """Initialize Vertex AI with Thomson Reuters credentials"""
    # Get credentials from TR auth module
    creds_data = self.auth.get_credentials()
    
    # Create OAuth2 credentials from TR token
    temp_creds = OAuth2Credentials(creds_data['token'])
    
    # Initialize Vertex AI
    vertexai.init(
        project=creds_data['project_id'],
        location=creds_data['region'],
        credentials=temp_creds
    )
    
    # Create the model
    self.model = GenerativeModel(
        model_name=self.auth.model_name,
        system_instruction=system_instruction
    )
```

**Structured Output Schema:**
```json
{
  "visual_analysis": {
    "shots": [
      {
        "timestamp": "00:00-00:05",
        "description": "string",
        "key_elements": ["string"],
        "action": "string"
      }
    ],
    "people_visible": ["string"],
    "locations_visible": ["string"],
    "text_visible": ["string"],
    "overall_scene": "string"
  },
  "audio_analysis": {
    "speech_detected": "boolean",
    "languages": ["string"],
    "transcription": "string",
    "ambient_sounds": ["string"],
    "notable_audio": "string"
  },
  "suggested_metadata": {
    "primary_subject": "string",
    "secondary_subjects": ["string"],
    "news_category": "string",
    "key_action": "string",
    "emotional_tone": "string"
  }
}
```

---

### 3. Metadata Generation Engine

#### **SLUG Generation**

**Reuters SLUG Format:** `CATEGORY-SUBCATEGORY/SPECIFIC-DETAIL`

**Generation Logic:**
```
1. Identify primary news category from video content:
   - CONFLICT/WAR (Israel-Palestinians, Ukraine-Russia, etc.)
   - POLITICS (Elections, Government, Parliament)
   - DISASTER (Natural disasters, accidents)
   - CRIME (Incidents, investigations)
   - PROTESTS (Demonstrations, civil unrest)
   - etc.

2. Identify geographic/entity focus:
   - Country or region
   - Specific organization or event

3. Add specific detail:
   - Type of incident (STRIKE, PROTEST, EXPLOSION)
   - Location name (ALBUREIJ, LOUVRE)
   - Add "UGC" suffix if appropriate

4. Validation:
   - Use two hyphens before forward slash
   - Maximum 40 characters
   - All caps
   - No special characters

Examples:
- ISRAEL-PALESTINIANS/ALBUREIJ-STRIKE-UGC
- FRANCE-CRIME/LOUVRE-ROBBERY-UGC
- KENYA-ODINGA/TEARGAS-UGC
```

**Gemini Prompt for SLUG:**
```
Based on the video analysis, generate a Reuters-style slug following this format:
CATEGORY-SUBCATEGORY/SPECIFIC-DETAIL

Rules:
- Use all caps
- Two hyphens before forward slash
- Maximum 40 characters
- Categories: CONFLICT, POLITICS, DISASTER, CRIME, PROTESTS, ACCIDENTS, etc.
- Include country/region name
- Add specific incident type
- Add UGC suffix if user-generated content

Video shows: {visual_summary}
Location: {location}
Context: {story_context}

Generate the SLUG:
```

---

#### **HEADLINE Generation**

**Reuters Headline Guidelines (from production guide p.3):**
- 6-8 words target
- Present tense, active voice
- "Who does what" structure
- Include geographic location
- Be punchy and clear
- Use single quotation marks for quotes
- For UGC: use "Eyewitness video" or "Social media video" (NOT "UGC")
- No clichés or puns
- Sell the story

**Gemini Prompt for HEADLINE:**
```
Create a Reuters-style headline for this UGC video following these strict rules:

RULES:
1. Length: 6-8 words (strict)
2. Tense: Present tense
3. Voice: Active voice
4. Structure: Who does what
5. Must include: Geographic location
6. Style: Clear, punchy, newsworthy
7. For UGC: Start with "Eyewitness video shows..." or "Social media video shows..."
8. Use single quotes for any quotes
9. No humor, puns, or clichés

VIDEO CONTENT:
{visual_summary}

LOCATION: {location}
DATE: {date}
CONTEXT: {story_context}

KEY ACTION: {primary_action}

Generate 3 headline options, then select the best one:
```

**Example Headlines from Corpus:**
- "Video showing Israeli airstrikes on Gaza neighbourhood after two of its soldiers killed"
- "Tour guide video shows visitors leaving Louvre after museum closed for robbery"
- "Eyewitness video shows smoke rising in Pakistan following suicide attack near Afghan border"
- "Eyewitness video of Kenya police firing tear gas and shots in stadium at Odinga mourners"
- "Webcam captures sound of loud blast at Tennessee munitions plant"

---

#### **INTRO Line Generation** (for VIRAL/EYEWITNESS feeds only)

**Format:**
- Single sentence, present tense
- Elaborates on headline
- Ends with source credit

**Gemini Prompt for INTRO:**
```
Create a single-sentence intro for this UGC video:

RULES:
1. Present tense
2. One sentence only
3. Elaborate on what the video shows (don't just repeat headline)
4. End with: "Video credit: {source}"
5. Be descriptive but concise

HEADLINE: {generated_headline}
VIDEO SHOWS: {visual_summary}
SOURCE: {source}

Generate the INTRO:
```

**Examples:**
- "An unexploded Second World War bomb is detonated safely but residents within 100-metre exclusion zone cannot return home. Video credit: Exeter City Council"
- "UGC showing smoke rising out of Gaza neighbourhood after Israeli airstrike. Source: Video obtained by Reuters"

---

#### **VIDEO SHOWS Generation**

**Purpose:** Mini-shotlist for quick client understanding

**Format:**
- All caps
- Use -ing verbs
- Separate sequences with semicolons (;) or slashes (/)
- Separate elements within sequence with commas (,)
- 1-2 lines maximum

**Gemini Prompt for VIDEO SHOWS:**
```
Create a "VIDEO SHOWS" summary line in all caps:

RULES:
1. All caps
2. Use -ing verb forms (WALKING, RISING, FIRING, SHOWING)
3. Separate distinct sequences with semicolons or slashes
4. Separate elements within one sequence with commas
5. Maximum 2 lines
6. Focus on key visual elements
7. No location (already in dateline)

VIDEO ANALYSIS:
{shot_by_shot_description}

AUDIO ELEMENTS:
{audio_summary}

Generate VIDEO SHOWS line:
```

**Examples:**
```
SMOKE RISING IN GAZA NEIGHBOURHOOD AFTER ISRAELI AIRSTRIKE / SMOKE RISING

VISITORS MAKING THEIR WAY OUT OF LOUVRE MUSEUM AFTER CLOSURE FOR ROBBERY / 
AUDIO OF TOUR GUIDE SPEAKING

SMOKE RISING DURING ATTACK / AUDIO OF GUNFIRE

CELL PHONE FOOTAGE OF WHITE SMOKE ERUPTING AND SOUNDS OF SHOTS FIRED AS 
CROWDS START RUNNING

WEBCAM SHOWING VEHICLE PARKED OUTSIDE HOUSE, AUDIO OF LOUD BLAST HEARD
```

---

#### **SHOTLIST Generation**

**Structure:**
```
DATELINE: LOCATION (DATE) (SOURCE – Restrictions) (Additional info if needed)

1. DESCRIPTION OF FIRST SHOT IN -ING VERB FORM
2. DESCRIPTION OF SECOND SHOT
3. (SOUNDBITE) (Language) SPEAKER TITLE, NAME, SAYING:
   "Transcribed text of what they say"
4. CONTINUATION OF SHOTS
```

**Key Rules:**
- Use -ing verb forms (WALKING, ENTERING, FIRING, etc.)
- Describe what's visible, not camera movements
- Avoid: CUTAWAY, WIDE, PAN, TILT, VIEW OF, TOP SHOT
- Do use: TIME-LAPSE when applicable
- Use forward slash (/) for shot changes within same number
- Use commas for multiple elements in stable shot
- For text on screen: transcribe exactly with (Language) tag
- For soundbites: full format with language and speaker details
- If mute: add (MUTE) before shot description
- If night shots: add (NIGHT SHOTS) before shot or as section

**Gemini Prompt for SHOTLIST:**
```
Create a Reuters-style shotlist with these rules:

DATELINE FORMAT:
LOCATION (DATE) (SOURCE – Restrictions)

SHOT DESCRIPTION RULES:
1. Number each shot
2. Use -ing verb forms: WALKING, RISING, SHOWING, FIRING
3. Describe action, NOT camera movements
4. DO NOT use: CUTAWAY, WIDE, PAN, TILT, VIEW OF
5. Use "/" for shot changes within same sequence
6. Use "," for multiple elements in one shot
7. For visible text: SIGN READING (Language): "exact text"
8. For soundbites: (SOUNDBITE) (Language) TITLE, NAME, SAYING:
9. Describe people by action first, then relevance to story
10. If mute section: add (MUTE) before shots
11. If night footage: add (NIGHT SHOTS) before shots

VIDEO ANALYSIS:
{detailed_shot_breakdown}

AUDIO:
{audio_transcription}

USER INPUT:
Location: {location}
Date: {date}
Source: {source}
Restrictions: {restrictions}

Generate complete SHOTLIST:
```

**Example Output:**
```
SHOWS: AL-BUREIJ, GAZA (OCTOBER 19, 2025) (VIDEO OBTAINED BY REUTERS - Access all)

1. DARK PLUME OF SMOKE RISING FROM DESTROYED BUILDINGS
```

**More Complex Example:**
```
SHOWS: NAIROBI, KENYA (OCTOBER 16, 2025) (EUGENE ODIYA - No resale / No archive / 
Must on-screen credit 'Eugene Odiya')

1. WHITE SMOKE ERUPTING AS PROTESTERS START RUNNING AND DROPPING TO GROUND / 
SCREAMING / SOUND OF SHOTS FIRED OFF SCREEN
```

**With Soundbite Example:**
```
SHOWS: MIR ALI, NORTH WAZIRISTAN, PAKISTAN (RELEASED OCTOBER 17, 2025) 
(SOCIAL MEDIA - No archive / No resale / News use only)

1. SMOKE RISING / AUDIO OF GUNFIRE HEARD
```

---

#### **VERIFICATION Statement Generation**

Must be included in SHOTLIST for UGC content.

**Format:**
```
Verified by:
- [Method 1]
- [Method 2]
- Date verified by [method]
```

**Gemini Prompt for VERIFICATION:**
```
Create a verification statement based on user input:

Location verified by: {location_verification_methods}
Date verified by: {date_verification_methods}
Additional notes: {verification_notes}

Format as bullet points starting with "Verified by:" or if unverified, state clearly.

Examples:
"Verified by: 
- Buildings, terrain, utility tower, and trees matched satellite imagery
- Mountain in background matched topography mapping
- Date could not be independently verified"

Generate verification statement:
```

---

#### **STORY Generation**

**Structure (3-4 paragraphs):**
1. **Lead paragraph:** What happened, where, when (most important info first)
2. **Context paragraph:** Why it matters, background, broader situation
3. **Detail paragraph:** Description that matches video content
4. **Verification paragraph:** How location/date were verified

**Writing Rules:**
- Simple past tense: "said," "killed," "fired," "attacked"
- Source all claims
- Include date with day name: "on Friday (October 17)"
- Use "according to" for attributions
- Write to the pictures (describe what's visible)
- Keep concise (3-4 paragraphs for most UGC)
- Include verification statement from Reuters
- British English spelling (unless US story)
- No emotive language or embellishment
- Factual, impartial, clear

**Gemini Prompt for STORY:**
```
Write a Reuters-style news story for this UGC video:

STRUCTURE:
Paragraph 1: Lead - What happened, where, when (most newsworthy first)
Paragraph 2: Context - Background and why it matters
Paragraph 3: Details - Description matching visible video content
Paragraph 4: Verification - How Reuters verified location/date

RULES:
1. Simple past tense: "said," "fired," "killed" (not "has fired" or "is firing")
2. Include date with day name: "on Thursday (October 16)"
3. Source all claims: "according to," "officials said," etc.
4. British English spelling (unless US location)
5. No emotive language
6. Factual and impartial
7. Write to the pictures - describe what's visible
8. Keep concise: 3-4 paragraphs for most UGC
9. Must include: "Reuters was able to independently verify the location by [method]. 
   The date was verified from [source]." OR "Reuters was not able to independently 
   verify the date."

INPUT DATA:
Headline: {headline}
Location: {location}
Date: {date}
Story context: {user_story_context}
Video shows: {visual_summary}
Audio contains: {audio_summary}
Verification: {verification_statement}

Generate the STORY:
```

**Example Story:**
```
STORY: Kenyan security forces fired into the air and lobbed tear gas on Thursday 
(October 16) to disperse thousands of mourners who had gathered at a Nairobi stadium 
to view the body of deceased opposition leader Raila Odinga.

Eyewitness material showed white smoke erupting with the sounds of a volley of shots 
fired as citizens ran, some falling to the ground, and many screaming.

Reuters was able to independently verify the location as the Kasarani stadium by the 
seating and field layout, and the canopy design that matched file and satellite imagery 
as well as corroborating footage from the scene. Reuters was able to independently 
verify the date by corroborating reports and the original file metadata from the source.
```

---

### 4. Technical Metadata Extraction

**Automatic Detection:**

```python
# Video technical analysis
{
  "duration": "0:45",  # Exclude 5-second slate
  "source_aspect": "W",  # W=16:9, P=Portrait/4:3 pillarboxed, M=Mixed
  "source_definition": "H",  # H=HD, S=SD, M=Mixed
  "sound": "NATURAL WITH ENGLISH SPEECH",
  "audio_languages": ["English", "Arabic"],
  "has_mute_sections": false,
  "has_night_shots": false,
  "contains_graphics": false,
  "contains_nudity": false,
  "contains_profanity": false
}
```

**Sound Field Generation:**
```
Formats:
- NATURAL (no speech)
- NATURAL WITH ENGLISH SPEECH
- NATURAL WITH FRENCH AND RUSSIAN SPEECH (multiple languages)
- NATURAL WITH ENGLISH SPEECH AND RUSSIAN COMMENTARY
- NATURAL WITH FARSI NARRATION
- NATURAL WITH ENGLISH SPEECH/PART MUTE
- MUTE
```

---

### 5. Output Format & Structure

**Complete JSON Output:**

```json
{
  "metadata": {
    "slug": "KENYA-ODINGA/TEARGAS-UGC",
    "headline": "Eyewitness video of Kenya police firing tear gas at Odinga mourners",
    "intro": "Cell phone footage inside Kasarani stadium in Nairobi shows white smoke billowing, sounds of shots, and citizens fleeing. Video credit: Eugene Odiya",
    "video_shows": "CELL PHONE FOOTAGE OF WHITE SMOKE ERUPTING AND SOUNDS OF SHOTS FIRED AS CROWDS START RUNNING IN KASARANI STADIUM",
    "duration": "0:45",
    "tx_date": "2025-10-16"
  },
  
  "location": {
    "city": "Nairobi",
    "region": "",
    "country": "Kenya",
    "full_location": "NAIROBI, KENYA"
  },
  
  "dates": [
    {
      "date": "OCTOBER 16, 2025",
      "date_iso": "2025-10-16"
    }
  ],
  
  "source": {
    "name": "EUGENE ODIYA",
    "type": "social_media",
    "source_line": "EUGENE ODIYA"
  },
  
  "restrictions": {
    "broadcast": "No resale / No archive / Must on-screen credit 'Eugene Odiya'",
    "digital": "No resale / No archive / Must on-screen credit 'Eugene Odiya'",
    "is_unrestricted": false
  },
  
  "technical": {
    "source_aspect": "P",
    "source_definition": "M",
    "sound": "NATURAL / AUDIO OF SHOTS FIRED OFF SCREEN",
    "languages": [],
    "has_mute_sections": false,
    "has_night_shots": false
  },
  
  "content_warnings": {
    "graphic": false,
    "nudity": false,
    "profanity": false,
    "notes": ""
  },
  
  "shotlist": {
    "dateline": "NAIROBI, KENYA (OCTOBER 16, 2025) (EUGENE ODIYA - No resale / No archive / Must on-screen credit 'Eugene Odiya')",
    "shots": [
      {
        "number": 1,
        "description": "WHITE SMOKE ERUPTING AS PROTESTERS START RUNNING AND DROPPING TO GROUND / SCREAMING / SOUND OF SHOTS FIRED OFF SCREEN",
        "type": "visual",
        "has_audio_note": true
      }
    ],
    "verification": {
      "location_method": "Kasarani stadium verified by seating and field layout, and canopy design that matched file and satellite imagery",
      "date_method": "Verified by corroborating reports and original file metadata"
    }
  },
  
  "story": "Kenyan security forces fired into the air and lobbed tear gas on Thursday (October 16) to disperse thousands of mourners who had gathered at a Nairobi stadium to view the body of deceased opposition leader Raila Odinga.\n\nEyewitness material showed white smoke erupting with the sounds of a volley of shots fired off as citizens ran, some falling to the ground, and many screaming.\n\nReuters was able to independently verify the location as the Kasarani stadium by the seating and field layout, and the canopy design that matched file and satellite imagery as well as corroborating footage from the scene. Reuters was able to independently verify the date by corroborating reports and the original file metadata from the source.",
  
  "user_info": {
    "name": "John Smith",
    "email": "john.smith@reuters.com",
    "story_context": "Mourning ceremony for opposition leader turned violent",
    "verification_notes": "Multiple angles available, stadium easily identifiable"
  },
  
  "processing": {
    "generated_at": "2025-10-24T14:30:00Z",
    "model": "gemini-2.0-flash-exp",
    "processing_time_seconds": 45.3,
    "confidence_score": 0.87
  }
}
```

---

### 6. Quality Validation & Checks

**Automated Validation Rules:**

```python
validation_checks = {
    "headline": {
        "word_count": (6, 8),  # Target range
        "max_length": 100,  # characters
        "must_include": ["location_term"],
        "forbidden_terms": ["UGC", "claims", "alleged"],
        "check_present_tense": True
    },
    
    "slug": {
        "format": r"^[A-Z0-9]+-[A-Z0-9]+/[A-Z0-9-]+$",
        "max_length": 40,
        "must_have_location": True
    },
    
    "story": {
        "min_paragraphs": 2,
        "max_paragraphs": 5,
        "must_include_verification": True,
        "check_past_tense": True,
        "check_attribution": True
    },
    
    "shotlist": {
        "must_have_dateline": True,
        "check_ing_verbs": True,
        "forbidden_terms": ["CUTAWAY", "WIDE SHOT", "PAN TO"],
        "numbering_sequential": True
    },
    
    "restrictions": {
        "format_valid": True,
        "broadcast_specified": True,
        "digital_specified": True
    }
}
```

**Content Warning Flags:**

```python
content_checks = {
    "graphic_imagery": {
        "triggers": ["blood", "bodies", "injuries", "violence"],
        "action": "FLAG for review, tick graphic checkbox"
    },
    
    "sensitive_content": {
        "triggers": ["children in distress", "nudity", "profanity"],
        "action": "FLAG for editorial review"
    },
    
    "legal_concerns": {
        "triggers": ["copyrighted music", "branded content", "private property"],
        "action": "FLAG for legal review"
    },
    
    "verification_low_confidence": {
        "threshold": 0.6,
        "action": "FLAG for additional verification"
    }
}
```

**Quality Scoring:**

```python
quality_score = {
    "headline_quality": 0.0 - 1.0,  # Clarity, newsworthiness
    "story_coherence": 0.0 - 1.0,   # Logical flow, completeness
    "shotlist_accuracy": 0.0 - 1.0,  # Matches video content
    "overall_confidence": 0.0 - 1.0  # AI confidence in output
}

# Flag for human review if overall_confidence < 0.70
```

---

### 7. User Interface Design

#### **Workflow Screens:**

**Screen 1: User Information**
```
┌─────────────────────────────────────────┐
│  UGC Video Metadata Generator           │
├─────────────────────────────────────────┤
│                                          │
│  Your Information                        │
│  ────────────────                        │
│  Name: [________________]                │
│  Email: [________________]               │
│                                          │
│  Story Context                           │
│  ────────────                            │
│  [_________________________________]     │
│  [_________________________________]     │
│  [_________________________________]     │
│                                          │
│  Date of Incident                        │
│  ────────────                            │
│  [📅 Oct 16, 2025  ▼]                   │
│                                          │
│          [Continue →]                    │
└─────────────────────────────────────────┘
```

**Screen 2: Source & Rights**
```
┌─────────────────────────────────────────┐
│  Step 2 of 5: Source & Rights            │
├─────────────────────────────────────────┤
│                                          │
│  Video Source                            │
│  ────────────                            │
│  ○ Video obtained by Reuters             │
│  ○ Social Media - Twitter                │
│  ○ Social Media - Instagram              │
│  ○ Social Media - Facebook               │
│  ○ Other: [________________]             │
│                                          │
│  Source Name/Handle                      │
│  [________________]                      │
│                                          │
│  Usage Restrictions                      │
│  ───────────────                         │
│  ○ No restrictions (Access all)          │
│  ○ Standard UGC restrictions             │
│     ☑ No resale                          │
│     ☑ No archive                         │
│     ☑ Must on-screen courtesy            │
│  ○ Custom restrictions                   │
│    [_____________________________]       │
│                                          │
│  [← Back]              [Continue →]      │
└─────────────────────────────────────────┘
```

**Screen 3: Location Details**
```
┌─────────────────────────────────────────┐
│  Step 3 of 5: Location                   │
├─────────────────────────────────────────┤
│                                          │
│  Where was this filmed?                  │
│  ──────────────────                      │
│  Country:  [Kenya            ▼]         │
│  City:     [Nairobi          ▼]         │
│  Region:   [________________]            │
│                                          │
│  Specific Location (optional)            │
│  [Kasarani Stadium___________]           │
│                                          │
│  Location Confidence                     │
│  ○ High  ○ Medium  ○ Low                 │
│                                          │
│  [← Back]              [Continue →]      │
└─────────────────────────────────────────┘
```

**Screen 4: Verification**
```
┌─────────────────────────────────────────┐
│  Step 4 of 5: Verification               │
├─────────────────────────────────────────┤
│                                          │
│  How was the LOCATION verified?          │
│  ───────────────────────────             │
│  ☑ Building structures matched           │
│    satellite imagery                     │
│  ☐ Landmarks identified                  │
│  ☑ Street layout matched mapping         │
│  ☐ Topography matched terrain            │
│  ☑ Corroborating footage                 │
│  ☐ Other: [_______________]              │
│                                          │
│  How was the DATE verified?              │
│  ──────────────────────                  │
│  ☑ Original file metadata                │
│  ☑ Corroborating reports                 │
│  ☐ Known events on that date             │
│  ☐ Weather data                          │
│  ☐ Could not be verified                 │
│  ☐ Other: [_______________]              │
│                                          │
│  Additional Notes                        │
│  [_________________________________]     │
│  [_________________________________]     │
│                                          │
│  [← Back]              [Continue →]      │
└─────────────────────────────────────────┘
```

**Screen 5: Video Upload**
```
┌─────────────────────────────────────────┐
│  Step 5 of 5: Upload Video               │
├─────────────────────────────────────────┤
│                                          │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │         📹                        │  │
│  │                                   │  │
│  │   Drag and drop video here        │  │
│  │   or click to browse              │  │
│  │                                   │  │
│  │   Supported: MP4, MOV, AVI, MKV   │  │
│  │   Max size: 2GB                   │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                          │
│  [← Back]              [Upload & Analyze]│
└─────────────────────────────────────────┘
```

**Screen 6: Processing**
```
┌─────────────────────────────────────────┐
│  Analyzing Video...                      │
├─────────────────────────────────────────┤
│                                          │
│  ✓ Video uploaded successfully           │
│  ✓ Technical metadata extracted          │
│  ⟳ Analyzing video content...            │
│    [████████████░░░░░░░░] 65%            │
│                                          │
│  Current step: Generating shotlist       │
│                                          │
│  Estimated time remaining: 30 seconds    │
│                                          │
│  🎬 AI is watching your video frame      │
│     by frame to create accurate          │
│     metadata...                          │
│                                          │
└─────────────────────────────────────────┘
```

**Screen 7: Review & Edit**
```
┌─────────────────────────────────────────────────────────┐
│  Review Generated Metadata  [Export ▼] [Regenerate]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Video Preview              │  Generated Metadata        │
│  ──────────────             │  ──────────────           │
│  ┌──────────────┐           │                           │
│  │              │  0:45     │  SLUG ⓘ                   │
│  │   [▶ Play]   │  ━━━●     │  [Edit] KENYA-ODINGA/     │
│  │              │           │         TEARGAS-UGC        │
│  └──────────────┘           │                           │
│                             │  HEADLINE ⓘ               │
│  ✓ Quality: HD              │  [Edit] Eyewitness video  │
│  ✓ Duration: 0:45           │  of Kenya police firing   │
│  ✓ Audio: Natural/Shots     │  tear gas at Odinga...    │
│  ⚠ Aspect: Portrait         │                           │
│                             │  VIDEO SHOWS ⓘ            │
│  ──────────────             │  [Edit] CELL PHONE        │
│  Validation Status:         │  FOOTAGE OF WHITE SMOKE   │
│  ✓ Headline (7 words)       │  ERUPTING AND SOUNDS...   │
│  ✓ Slug format valid        │                           │
│  ⚠ Story needs review       │  RESTRICTIONS ⓘ           │
│  ✓ Verification included    │  [Edit] Broadcast: No...  │
│                             │        Digital: No...      │
│                             │                           │
├─────────────────────────────┼───────────────────────────┤
│                             │                           │
│  SHOTLIST ⓘ                 │  STORY ⓘ                  │
│  [Edit Full Shotlist]       │  [Edit Full Story]        │
│                             │                           │
│  NAIROBI, KENYA (OCTOBER    │  Kenyan security forces   │
│  16, 2025) (EUGENE ODIYA..  │  fired into the air and   │
│                             │  lobbed tear gas on...    │
│  1. WHITE SMOKE ERUPTING    │                           │
│     AS PROTESTERS START...  │  Eyewitness material      │
│                             │  showed white smoke...    │
│  Verified by:               │                           │
│  - Kasarani stadium...      │  Reuters was able to...   │
│  - Date verified from...    │                           │
│                             │                           │
├─────────────────────────────┴───────────────────────────┤
│                                                          │
│  Content Warnings:  ☐ Graphic  ☐ Nudity  ☐ Profanity    │
│                                                          │
│  [← Back to Upload]    [Save Draft]    [Export Final →] │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Export Options Dialog:**
```
┌─────────────────────────────────────────┐
│  Export Metadata                         │
├─────────────────────────────────────────┤
│                                          │
│  Select export format:                   │
│                                          │
│  ○ JSON (structured data)                │
│  ○ Plain text (Reuters format)           │
│  ○ Reuters Connect ready                 │
│  ○ Email to desk                         │
│                                          │
│  Send copy to:                           │
│  ☑ My email (john.smith@reuters.com)     │
│  ☐ Desk email: [______________]          │
│                                          │
│  Additional options:                     │
│  ☑ Include video file                    │
│  ☐ Generate PDF summary                  │
│                                          │
│          [Cancel]    [Export]            │
│                                          │
└─────────────────────────────────────────┘
```

---

### 8. Implementation Recommendations

#### **Technology Stack**

**Frontend:**
- **Framework:** React with Next.js 14+
- **UI Library:** Tailwind CSS + Shadcn/ui components
- **Form Management:** React Hook Form + Zod validation
- **State Management:** Zustand or Redux Toolkit
- **Video Player:** Video.js or React Player
- **File Upload:** react-dropzone + tus-js-client (resumable uploads)

**Backend:**
- **Framework:** Python FastAPI
- **Video Processing:** FFmpeg for technical analysis
- **AI Integration:** Google Gemini API (vertex-ai SDK)
- **Task Queue:** Celery + Redis (for async processing)
- **Database:** PostgreSQL + SQLAlchemy ORM
- **File Storage:** AWS S3 / Google Cloud Storage / Azure Blob
- **Caching:** Redis for session data

**Infrastructure:**
- **Hosting:** Google Cloud Platform (GCP) for Gemini integration
- **Container:** Docker + Kubernetes
- **CI/CD:** GitHub Actions or GitLab CI
- **Monitoring:** Sentry (errors) + DataDog (performance)

#### **API Architecture**

```
Frontend (React)
    ↓
API Gateway (FastAPI)
    ↓
┌────────────────────────────────────┐
│  Async Task Queue (Celery)         │
│  ├─ Video Upload Handler           │
│  ├─ Technical Analysis Worker      │
│  ├─ Gemini Processing Worker       │
│  └─ Metadata Generation Worker     │
└────────────────────────────────────┘
    ↓
┌────────────────────────────────────┐
│  Services                          │
│  ├─ Video Service (FFmpeg)         │
│  ├─ Gemini Service (AI)            │
│  ├─ Validation Service             │
│  └─ Export Service                 │
└────────────────────────────────────┘
    ↓
Storage (S3) + Database (PostgreSQL)
```

#### **API Endpoints**

```python
# User & Session Management
POST   /api/v1/sessions                 # Create new session
GET    /api/v1/sessions/{id}            # Get session data
PATCH  /api/v1/sessions/{id}            # Update session data

# Video Upload
POST   /api/v1/videos/upload            # Upload video file
GET    /api/v1/videos/{id}/status       # Check upload status
POST   /api/v1/videos/{id}/analyze      # Trigger analysis

# Metadata Generation
POST   /api/v1/generate/slug            # Generate slug
POST   /api/v1/generate/headline        # Generate headline
POST   /api/v1/generate/shotlist        # Generate shotlist
POST   /api/v1/generate/story           # Generate story
POST   /api/v1/generate/all             # Generate all metadata

# Review & Edit
PATCH  /api/v1/metadata/{id}            # Update metadata
POST   /api/v1/metadata/{id}/validate   # Validate metadata
GET    /api/v1/metadata/{id}/warnings   # Get content warnings

# Export
POST   /api/v1/export/json              # Export as JSON
POST   /api/v1/export/text              # Export as plain text
POST   /api/v1/export/email             # Email to desk
```

#### **Database Schema**

```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) -- draft, processing, completed
);

-- Videos table
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    filename VARCHAR(500),
    storage_path TEXT,
    duration_seconds NUMERIC,
    resolution VARCHAR(20),
    aspect_ratio VARCHAR(10),
    file_size_bytes BIGINT,
    upload_completed_at TIMESTAMP,
    processing_status VARCHAR(50)
);

-- Metadata table
CREATE TABLE metadata (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    video_id UUID REFERENCES videos(id),
    
    -- Story details
    slug VARCHAR(100),
    headline TEXT,
    intro TEXT,
    video_shows TEXT,
    story TEXT,
    
    -- Location
    location_city VARCHAR(255),
    location_region VARCHAR(255),
    location_country VARCHAR(255),
    location_full TEXT,
    
    -- Source & Rights
    source_name VARCHAR(255),
    source_type VARCHAR(50),
    restrictions_broadcast TEXT,
    restrictions_digital TEXT,
    
    -- Technical
    sound TEXT,
    source_aspect VARCHAR(10),
    source_definition VARCHAR(10),
    
    -- Flags
    is_graphic BOOLEAN DEFAULT FALSE,
    is_nudity BOOLEAN DEFAULT FALSE,
    is_profanity BOOLEAN DEFAULT FALSE,
    
    -- AI metadata
    gemini_response JSONB,
    confidence_score NUMERIC,
    generated_at TIMESTAMP,
    
    -- User edits
    manually_edited BOOLEAN DEFAULT FALSE,
    last_edited_at TIMESTAMP
);

-- Shotlist table
CREATE TABLE shotlist_shots (
    id UUID PRIMARY KEY,
    metadata_id UUID REFERENCES metadata(id),
    shot_number INTEGER,
    description TEXT,
    shot_type VARCHAR(50), -- visual, soundbite, etc
    timestamp_start VARCHAR(20),
    timestamp_end VARCHAR(20),
    has_audio_note BOOLEAN DEFAULT FALSE
);

-- Verification table
CREATE TABLE verification (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    incident_date DATE,
    location_methods TEXT[],
    date_methods TEXT[],
    additional_notes TEXT,
    location_confidence VARCHAR(20)
);

-- Audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    action VARCHAR(100),
    user_email VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

### 9. Gemini Integration Details

#### **Video Processing Strategy**

**Approach 1: Full Video Analysis (Recommended for accuracy)**
```python
import google.generativeai as genai
import time

# Configure API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Upload video
video_file = genai.upload_file(
    path="path/to/ugc_video.mp4",
    display_name="UGC_Analysis"
)

# Wait for processing
while video_file.state.name == "PROCESSING":
    time.sleep(5)
    video_file = genai.get_file(video_file.name)

if video_file.state.name == "FAILED":
    raise ValueError(f"Video processing failed: {video_file.state}")

# Initialize model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Create comprehensive prompt
prompt = f"""
Analyze this UGC news video and provide detailed metadata.

CONTEXT PROVIDED BY JOURNALIST:
- Location: {location}
- Date: {date}
- Story Context: {story_context}
- Source: {source}
- Verification: Location verified by {location_verification_methods}
- Date verified by {date_verification_methods}

YOUR TASK:
Analyze the entire video and provide:

1. VISUAL ANALYSIS:
   - Break down the video shot by shot
   - Describe each scene in detail
   - Identify people, objects, actions
   - Note any visible text or signs
   - Describe the sequence of events

2. AUDIO ANALYSIS:
   - Identify languages spoken
   - Transcribe any speech (with timestamps)
   - Note ambient sounds (gunfire, explosions, sirens, etc.)
   - Identify any music or audio overlays

3. NEWS VALUE ASSESSMENT:
   - What is the most newsworthy element?
   - What is the primary action/event shown?
   - Who are the key figures (if identifiable)?
   - What is the emotional tone/impact?

Provide your analysis in structured JSON format.
"""

# Generate with structured output
response = model.generate_content(
    [video_file, prompt],
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=VideoAnalysisSchema,
        temperature=0.2  # Lower for more factual output
    )
)

analysis = json.loads(response.text)
```

**Approach 2: Frame Sampling (Faster, for breaking news)**
```python
# Extract keyframes using FFmpeg
import subprocess

def extract_keyframes(video_path, output_dir, interval=2):
    """Extract frames every N seconds"""
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'fps=1/{interval}',
        f'{output_dir}/frame_%04d.jpg'
    ]
    subprocess.run(cmd, check=True)
    
# Upload frames to Gemini
frames = []
for frame_path in sorted(glob.glob(f"{output_dir}/frame_*.jpg")):
    frame_file = genai.upload_file(path=frame_path)
    frames.append(frame_file)

# Analyze frame sequence
prompt = f"""
These are frames extracted from a UGC news video at {interval}-second intervals.

Analyze the sequence and describe:
1. What happens in each frame
2. The overall sequence of events
3. Key visual elements
4. Any changes or progression

Context: {story_context}
Location: {location}
"""

response = model.generate_content([prompt] + frames)
```

#### **Structured Output Schemas**

```python
from typing import List, Optional
from pydantic import BaseModel

class ShotDescription(BaseModel):
    shot_number: int
    timestamp_start: str
    timestamp_end: str
    description: str
    action_verb: str  # -ing form
    key_elements: List[str]
    visible_text: Optional[str] = None
    audio_note: Optional[str] = None

class SoundbiteInfo(BaseModel):
    shot_number: int
    language: str
    speaker_name: Optional[str]
    speaker_title: Optional[str]
    transcription: str
    timestamp_start: str
    timestamp_end: str

class VideoAnalysisSchema(BaseModel):
    visual_summary: str
    shot_breakdown: List[ShotDescription]
    soundbites: List[SoundbiteInfo]
    audio_summary: str
    languages_detected: List[str]
    ambient_sounds: List[str]
    visible_text_instances: List[dict]
    people_identified: List[dict]
    primary_subject: str
    key_action: str
    news_category: str
    emotional_tone: str
    verification_visual_markers: List[str]

# Use with Gemini
response = model.generate_content(
    [video_file, prompt],
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=VideoAnalysisSchema
    )
)
```

#### **Prompt Templates**

**Master Analysis Prompt:**
```python
ANALYSIS_PROMPT = """
You are a Reuters video journalist analyzing UGC footage for publication.

VIDEO CONTEXT:
- Date: {date}
- Location: {location}
- Story: {story_context}
- Source: {source}

ANALYZE THIS VIDEO AND PROVIDE:

1. SHOT-BY-SHOT BREAKDOWN:
   For each distinct shot or scene:
   - Timestamp range
   - Detailed description using -ing verbs (WALKING, FIRING, RISING)
   - Key visual elements
   - Any visible text or signs
   - Notable audio elements
   
   DO NOT USE: "wide shot", "pan", "cutaway", "view of"
   DO USE: Clear action descriptions (PROTESTERS MARCHING, SMOKE RISING)

2. AUDIO ANALYSIS:
   - Languages spoken (if any)
   - Full transcription of speech (with timestamps)
   - Ambient sounds (gunfire, explosions, sirens, crowd noise)
   - Audio quality notes

3. CONTENT IDENTIFICATION:
   - People visible (descriptions if not identifiable by name)
   - Objects/vehicles
   - Locations/landmarks visible
   - Text on signs, banners, buildings

4. NEWS ASSESSMENT:
   - Most newsworthy element
   - Primary action/event
   - Secondary interesting elements
   - Story category (conflict, protest, disaster, etc.)

5. VERIFICATION MARKERS:
   - Visible landmarks that could verify location
   - Date indicators (newspapers, visible dates, known events)
   - Any metadata visible in frame

Return structured JSON following the VideoAnalysisSchema.
"""

HEADLINE_PROMPT = """
Based on this video analysis, create a Reuters-style headline.

VIDEO SHOWS: {visual_summary}
LOCATION: {location}
KEY ACTION: {key_action}

STRICT RULES:
1. Exactly 6-8 words
2. Present tense, active voice
3. Start with "Eyewitness video shows" or "Social media video shows"
4. Include location
5. Focus on most newsworthy action
6. Clear and punchy
7. No jargon or unclear terms

Generate 3 options, then select the best:
"""

SHOTLIST_PROMPT = """
Create a Reuters-style shotlist from this video analysis.

SHOT BREAKDOWN:
{shot_breakdown_json}

AUDIO ELEMENTS:
{audio_summary}

RULES:
1. Use -ing verb forms (WALKING, RISING, SHOWING)
2. Number each shot
3. Describe action, NOT camera work
4. For shot changes within sequence: use "/"
5. For multiple elements in one shot: use ","
6. For soundbites: Full format with language and speaker
7. For visible text: SIGN READING (Language): "exact text"
8. If mute: add (MUTE) before shot
9. If night: add (NIGHT SHOT) before shot

DATELINE FORMAT:
{location} ({date}) ({source} - {restrictions})

Generate complete shotlist:
"""

STORY_PROMPT = """
Write a Reuters news story (3-4 paragraphs) for this UGC video.

VIDEO ANALYSIS:
{visual_summary}

CONTEXT:
- Location: {location}
- Date: {date}
- What happened: {story_context}

AUDIO/QUOTES:
{audio_summary}

VERIFICATION:
{verification_statement}

STRUCTURE:
Paragraph 1: Lead - What happened, where, when (most important first)
Paragraph 2: Context - Why it matters, background
Paragraph 3: Details - Describe visible content
Paragraph 4: Verification - How Reuters verified this

STYLE RULES:
- Simple past tense: "said", "fired", "killed"
- Include date: "on Thursday (October 16)"
- Source claims: "according to", "officials said"
- British spelling (unless US location)
- Factual, impartial tone
- Must include: "Reuters was able to independently verify the location by [method]. The date was verified from [source]."

Write the story:
"""
```

#### **Error Handling & Retry Logic**

```python
import time
from typing import Optional
import google.generativeai as genai

class GeminiVideoProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def upload_with_retry(self, video_path: str) -> Optional[genai.File]:
        """Upload video with retry logic"""
        for attempt in range(self.max_retries):
            try:
                video_file = genai.upload_file(
                    path=video_path,
                    display_name=f"UGC_Video_{int(time.time())}"
                )
                
                # Wait for processing
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                if video_file.state.name == "ACTIVE":
                    return video_file
                elif video_file.state.name == "FAILED":
                    raise ValueError(f"Processing failed: {video_file.state}")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise e
        
        return None
    
    def generate_with_retry(
        self, 
        prompt: str, 
        video_file: genai.File,
        response_schema: Optional[type] = None
    ) -> dict:
        """Generate content with retry logic"""
        for attempt in range(self.max_retries):
            try:
                config = genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=8192
                )
                
                if response_schema:
                    config.response_mime_type = "application/json"
                    config.response_schema = response_schema
                
                response = self.model.generate_content(
                    [video_file, prompt],
                    generation_config=config
                )
                
                if response_schema:
                    return json.loads(response.text)
                else:
                    return {"text": response.text}
                    
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    # Rate limit hit
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                elif attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise e
        
        raise RuntimeError("Max retries exceeded")
```

#### **Cost Optimization**

```python
# Gemini 2.0 Flash pricing (approximate)
PRICING = {
    "input_video_per_second": 0.00001,  # $0.01 per 1000 seconds
    "output_tokens_per_1k": 0.000075,   # $0.075 per 1M tokens
}

def estimate_cost(video_duration_seconds: int, expected_output_tokens: int = 2000):
    """Estimate processing cost"""
    video_cost = video_duration_seconds * PRICING["input_video_per_second"]
    output_cost = (expected_output_tokens / 1000) * PRICING["output_tokens_per_1k"]
    total = video_cost + output_cost
    return {
        "video_cost": video_cost,
        "output_cost": output_cost,
        "total_cost": total
    }

# Example: 60-second video = ~$0.0006 + ~$0.00015 = ~$0.00075 per analysis
```

**Optimization Strategies:**
1. **Batch processing**: Queue multiple videos during off-peak hours
2. **Frame sampling for breaking news**: Use 1 frame per 3 seconds for urgent content
3. **Cached analysis**: Store video hashes to avoid re-analyzing identical content
4. **Progressive generation**: Generate critical fields (headline, slug) first, story later
5. **Concurrent requests**: Process shotlist and story generation in parallel

---

### 10. Security & Compliance

#### **Data Privacy**
- Encrypt videos in transit (TLS) and at rest (AES-256)
- Implement user authentication/authorization
- Auto-delete uploaded videos after 30 days
- GDPR compliance for user data
- Audit trail for all actions

#### **Content Security**
- Virus scanning on upload
- File type validation
- Size limits (max 2GB)
- Watermarking options for sensitive content

#### **API Security**
- Rate limiting per user/session
- API key rotation
- Input sanitization
- SQL injection prevention
- XSS protection

---

### 11. Testing Strategy

#### **Unit Tests**
- Slug generation rules
- Headline validation
- Shotlist formatting
- Date/time parsing
- Restriction formatting

#### **Integration Tests**
- Gemini API integration
- Video upload flow
- Database operations
- Export functionality

#### **End-to-End Tests**
- Complete user workflow
- Multiple video formats
- Various restriction scenarios
- Error handling paths

#### **User Acceptance Testing**
- Test with real Reuters journalists
- Gather feedback on AI accuracy
- Refine prompts based on results
- A/B test different prompt strategies

---

### 12. Deployment & Monitoring

#### **Deployment Strategy**
- Containerized with Docker
- Kubernetes for orchestration
- Blue-green deployment
- Automated rollback on errors

#### **Monitoring**
```python
metrics_to_track = {
    "performance": [
        "video_upload_time",
        "gemini_processing_time",
        "total_generation_time"
    ],
    "quality": [
        "ai_confidence_scores",
        "manual_edit_rate",
        "user_satisfaction_score"
    ],
    "usage": [
        "videos_processed_per_day",
        "peak_usage_times",
        "average_video_duration"
    ],
    "errors": [
        "gemini_api_errors",
        "upload_failures",
        "validation_failures"
    ],
    "costs": [
        "gemini_api_costs_daily",
        "storage_costs",
        "compute_costs"
    ]
}
```

#### **Alerting**
- Error rate > 5%: Alert on-call engineer
- API cost spike > 150% of average: Alert finance team
- Processing time > 5 minutes: Alert DevOps
- User satisfaction < 3.5/5: Alert product team

---

### 13. Future Enhancements

#### **Phase 2 Features**
- Multi-language interface (for international bureaus)
- Automated translation of foreign-language soundbites
- Integration with Reuters Connect for direct publishing
- Mobile app for field journalists
- Collaborative editing with version control
- Advanced video editing tools (trim, splice)

#### **AI Improvements**
- Fine-tuned model on Reuters historical content
- Custom entity recognition for journalists, politicians
- Automated fact-checking against Reuters archive
- Plagiarism detection for UGC sourcing
- Deepfake detection algorithms

#### **Workflow Optimization**
- Batch processing for multiple videos
- Templates for common story types
- Auto-suggest based on similar past stories
- Integration with other newsroom tools

---

### 14. Success Metrics

**Key Performance Indicators:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to publish UGC | < 15 min | Time from upload to export |
| AI accuracy rate | > 85% | % of metadata accepted without edits |
| User satisfaction | > 4/5 | Post-use survey rating |
| Cost per video | < $0.002 | Gemini API + infrastructure |
| System uptime | > 99.5% | Availability monitoring |
| Manual edit rate | < 30% | % requiring substantial edits |

---

## Conclusion

This application will significantly accelerate the UGC publishing workflow for Reuters journalists by:

1. **Reducing manual effort** in creating metadata, shotlists, and scripts
2. **Ensuring compliance** with Reuters style guidelines automatically
3. **Improving consistency** across all UGC content
4. **Enabling faster breaking news** response times
5. **Maintaining quality** through validation and human review

The use of **Google Gemini Flash 2.5** provides:
- Fast processing suitable for breaking news
- Cost-effective scaling for high volume
- Native video understanding without frame extraction
- Structured output for reliable metadata generation

**Next Steps:**
1. Develop MVP with core features (Steps 1-5 of user input + basic Gemini integration)
2. Test with small group of Reuters journalists
3. Iterate based on feedback
4. Gradual rollout to all bureaus
5. Continuous improvement of AI prompts and quality

---

## Appendix A: Thomson Reuters Authentication

**Complete authentication documentation:** See [TR Authentication & Gemini Integration Guide](./tr-authentication-gemini-integration.md)

**Key Points:**
- Uses TR centralized authentication service
- Provides temporary OAuth2 tokens for Gemini access
- Automatic token refresh every 50 minutes
- Secure credential management
- Comprehensive error handling
- Production-ready monitoring and logging

**Environment Variables Required:**
```bash
WORKSPACE_ID=your-tr-workspace-id
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://your-tr-auth-endpoint/api/token
```

---

## Appendix B: Reuters Style Quick Reference

**Headline Rules:**
- 6-8 words
- Present tense
- Active voice
- Include location
- Use "Eyewitness video shows" for UGC

**Shotlist Rules:**
- Use -ing verbs
- Number shots
- DATELINE: LOCATION (DATE) (SOURCE – Restrictions)
- No camera terms (wide, pan, cutaway)

**Story Rules:**
- Simple past tense
- 3-4 paragraphs for UGC
- Include verification statement
- British spelling (except US stories)

**Restrictions Format:**
- Broadcast: [restrictions]
- Digital: [restrictions]
- Common: "No resale / No archive / Must on-screen courtesy [Source]"

**Sources:**
- Reuters-shot: REUTERS – Access all
- UGC: Individual/handle – Restrictions
- Third-party: SOURCE NAME – Restrictions
- Pool: AGENCY POOL – Access all

---

**Document Version:** 1.0  
**Date:** October 24, 2025  
**Author:** Technical Architecture Team  
**Model:** Google Gemini Flash 2.5
