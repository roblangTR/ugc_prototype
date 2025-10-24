# UGC Video Metadata Generation App

AI-powered application that helps Reuters journalists quickly prepare User-Generated Content (UGC) videos for publication.

## Overview

This application streamlines the UGC video publishing workflow by:
- Collecting metadata through a 5-step form interface
- Analyzing videos using Google Gemini Flash 2.5
- Generating Reuters-compliant metadata (SLUG, HEADLINE, SHOTLIST, STORY)
- Using Thomson Reuters' centralized authentication system

## Features

- **Simple Web Interface**: Two-column layout with form and video player
- **AI Video Analysis**: Powered by Google Gemini Flash 2.5 via Vertex AI
- **Metadata Generation**: Automatic creation of Reuters-style SLUG, HEADLINE, SHOTLIST, and STORY
- **Slate Generation**: Reuters-branded 5-second slate with metadata overlay
- **Video Stitching**: Automatic concatenation of slate + original video
- **Video Player**: Preview final video with slate before download
- **GUID Validation**: Real-time validation and edit number extraction
- **Today/Yesterday Buttons**: Quick date selection for recent events
- **File-Based Storage**: No database required (prototype)

## Technology Stack

### Backend
- **Framework**: Python FastAPI
- **AI Integration**: Google Vertex AI SDK (Gemini Flash 2.5)
- **Authentication**: Thomson Reuters centralized auth system
- **Database**: PostgreSQL + SQLAlchemy
- **Task Queue**: Celery + Redis
- **Video Processing**: FFmpeg

### Frontend
- **Framework**: React + Next.js 14
- **UI**: Tailwind CSS + Shadcn/ui
- **Forms**: React Hook Form + Zod
- **State**: Zustand
- **Video Player**: Video.js

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis
- FFmpeg
- Thomson Reuters credentials (WORKSPACE_ID, CREDENTIALS_URL)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/roblangTR/ugc_prototype.git
cd ugc_prototype
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your TR credentials
# WORKSPACE_ID=your-tr-workspace-id
# MODEL_NAME=gemini-2.5-flash
# CREDENTIALS_URL=https://your-tr-auth-endpoint/api/token
```

### 3. Verify Assets

```bash
# Ensure Reuters slate background exists
ls -lh app/assets/reuters_slate_background.jpg

# Silent audio file should exist (created automatically if missing)
ls -lh app/assets/silent_5s.aac
```

### 4. Test Authentication

```bash
# Verify TR authentication and Gemini access
python scripts/test_auth.py
```

### 5. Run Development Server

```bash
# Start server
python -m app.main

# Access web interface
open http://localhost:8000
```

## Project Structure

```
ugc_prototype/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── assets/
│   │   ├── reuters_slate_background.jpg  # Slate background
│   │   └── silent_5s.aac                 # Silent audio for slate
│   └── static/
│       └── index.html          # Web interface
├── modules/
│   ├── auth.py                 # TR authentication
│   ├── gemini_enhancer.py      # Gemini video analysis
│   ├── slate_generator.py      # Slate image generation
│   ├── video_stitcher.py       # FFmpeg operations
│   └── slate_workflow.py       # Complete workflow
├── tests/
│   ├── test_auth.py            # Authentication tests
│   └── __init__.py
├── scripts/
│   ├── test_auth.py            # Test authentication
│   ├── test_video_analysis.py  # Test video analysis
│   └── test_slate_generation.py # Test slate generation
├── uploads/                    # Uploaded videos
├── outputs/                    # Generated metadata JSON
├── final_videos/               # Final videos with slates
├── .clinerules/                # Development guidelines
│   ├── git-commit-formatting.md
│   └── terminal-command-formatting.md
├── .env                        # Configuration (not in git)
├── .env.example                # Configuration template
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
```

## Authentication

This application uses Thomson Reuters' centralized authentication system to access Google Gemini via Vertex AI.

**Key Components:**
- TR Authentication Service provides temporary OAuth2 tokens
- Tokens include: workspace_id, project_id, region
- Automatic token refresh mechanism (every 50 minutes)
- Secure credential management

For detailed authentication documentation, see [seed files/tr-authentication-gemini-integration.md](seed%20files/tr-authentication-gemini-integration.md)

## Development Workflow

### Git Commit Strategy

We follow a structured commit strategy with frequent commits:

**Commit Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance

**Example:**
```
feat(auth): Implement TR authentication module

- Add ThomsonReutersAuth class
- Implement token refresh mechanism
- Add error handling for auth failures

Closes #12
```

### Branch Strategy

```
main (production-ready)
  ↓
develop (integration)
  ↓
feature/auth-module
feature/gemini-integration
feature/user-input-forms
```

## Testing

```bash
# Test authentication
python scripts/test_auth.py

# Test video analysis with Gemini
python scripts/test_video_analysis.py

# Test complete slate generation workflow
python scripts/test_slate_generation.py

# Run unit tests
pytest tests/test_auth.py -v
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

```
GET  /                             # Web interface
GET  /health                       # Health check

POST /api/analyze-video            # Upload video and generate metadata
GET  /api/outputs                  # List all metadata files
GET  /api/outputs/{filename}       # Get specific metadata

POST /api/generate-slate           # Generate slate and stitch video
GET  /api/validate-guid/{guid}     # Validate GUID format
GET  /api/download/{filename}      # Download final video
```

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# Thomson Reuters Authentication
WORKSPACE_ID=your-workspace-id
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://your-tr-auth-endpoint/api/token

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ugc_app

# Redis
REDIS_URL=redis://localhost:6379

# Storage
STORAGE_PROVIDER=s3
STORAGE_BUCKET=ugc-videos-bucket
```

## Documentation

- [Main Proposal](seed%20files/ugc-video-metadata-app-proposal.md) - Complete architecture and features
- [TR Authentication Guide](seed%20files/tr-authentication-gemini-integration.md) - Authentication implementation
- [README](seed%20files/README.md) - Documentation overview

## Usage

### Web Interface

1. **Start the server:**
   ```bash
   source venv/bin/activate
   python -m app.main
   ```

2. **Open browser:** http://localhost:8000

3. **Complete workflow:**
   - Fill in event context, location, date, source
   - Upload video (drag & drop or click)
   - Click "Generate Metadata" (wait ~30s)
   - Review metadata in left column
   - Enter GUID in right column (e.g., "F29000")
   - Click "Generate Final Video with Slate" (wait ~30-60s)
   - Preview video in player
   - Download final video

### Slate Format

The generated slate includes:
- **Edit Number** (gold/amber #F29000)
- **SLUG** (gold/amber #F29000)
- **Location, Duration, Date, Audio Type, Restrictions** (white)

### Output Files

- **Metadata:** `outputs/YYYYMMDD_HHMMSS_metadata.json`
- **Final Video:** `final_videos/EDIT#_SLUG_final.mp4`
- **Uploaded Videos:** `uploads/YYYYMMDD_HHMMSS_filename.ext`

## Contributing

1. Make changes with clear, frequent commits
2. Follow git commit formatting guidelines (see `.clinerules/`)
3. Test thoroughly before committing
4. Push to main branch

## License

Thomson Reuters Internal Use Only

## Support

For issues or questions, contact the development team or create an issue in the repository.

---

**Version**: 0.1.0 (MVP Development)  
**Last Updated**: October 24, 2025
