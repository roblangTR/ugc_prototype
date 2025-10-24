# UGC Video Metadata Generation App

AI-powered application that helps Reuters journalists quickly prepare User-Generated Content (UGC) videos for publication.

## Overview

This application streamlines the UGC video publishing workflow by:
- Collecting metadata through a 5-step form interface
- Analyzing videos using Google Gemini Flash 2.5
- Generating Reuters-compliant metadata (SLUG, HEADLINE, SHOTLIST, STORY)
- Using Thomson Reuters' centralized authentication system

## Features

- **Multi-step Form**: Guided data collection (User Info, Source & Rights, Location, Verification, Video Upload)
- **AI Video Analysis**: Powered by Google Gemini Flash 2.5 via Vertex AI
- **Metadata Generation**: Automatic creation of Reuters-style SLUG, HEADLINE, SHOTLIST, and STORY
- **Quality Validation**: Built-in checks for Reuters style compliance
- **Review & Edit**: Interactive interface for journalist review and refinement
- **Multiple Export Formats**: JSON, plain text, Reuters Connect ready

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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# WORKSPACE_ID=your-tr-workspace-id
# MODEL_NAME=gemini-2.0-flash-exp
# CREDENTIALS_URL=https://your-tr-auth-endpoint/api/token
```

### 3. Database Setup

```bash
# Initialize database
python scripts/init_db.py
```

### 4. Test Authentication

```bash
# Verify TR authentication and Gemini access
python scripts/test_auth.py
```

### 5. Run Development Server

```bash
# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
ugc_prototype/
├── modules/
│   ├── auth.py                 # TR authentication module
│   ├── gemini_enhancer.py      # Gemini video analysis
│   └── metadata_generator.py   # Metadata generation logic
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Database models
│   ├── routes/                 # API endpoints
│   └── services/               # Business logic
├── tests/
│   ├── test_auth.py
│   ├── test_gemini.py
│   └── test_metadata.py
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Next.js pages
│   │   └── lib/                # Utilities
│   └── public/
├── scripts/
│   ├── init_db.py
│   └── test_auth.py
├── .env.example
├── requirements.txt
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
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=modules --cov-report=html
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

```
POST /api/v1/sessions              # Create new session
POST /api/v1/videos/upload         # Upload video
POST /api/v1/generate/all          # Generate all metadata
GET  /api/v1/metadata/{id}         # Get metadata
POST /api/v1/export/json           # Export as JSON
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

## Contributing

1. Create a feature branch from `develop`
2. Make your changes with clear, frequent commits
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request to `develop`

## License

Thomson Reuters Internal Use Only

## Support

For issues or questions, contact the development team or create an issue in the repository.

---

**Version**: 0.1.0 (MVP Development)  
**Last Updated**: October 24, 2025
