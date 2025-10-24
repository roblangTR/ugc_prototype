# UGC Video Metadata Generation App - Documentation

## Overview

This documentation package provides a comprehensive technical proposal for building an AI-powered application that helps Reuters journalists quickly prepare UGC (User-Generated Content) videos for publication.

## Document Structure

### 1. Main Proposal Document
**File:** `ugc-video-metadata-app-proposal.md`

**Contents:**
- Executive summary
- Complete architecture overview
- User interface design (5-step workflow)
- AI processing pipeline with Google Gemini Flash 2.5
- Metadata generation engine (SLUG, HEADLINE, SHOTLIST, STORY)
- Quality validation system
- Technology stack recommendations
- Database schema
- Testing strategy
- Deployment guidelines
- Success metrics

**Start here** for the overall project understanding.

---

### 2. TR Authentication & Gemini Integration
**File:** `tr-authentication-gemini-integration.md`

**Contents:**
- Thomson Reuters authentication system architecture
- Token management and refresh mechanisms
- Vertex AI initialization with TR credentials
- Security best practices
- Error handling and monitoring
- Complete code examples
- Troubleshooting guide
- API reference

**Use this** for implementing authentication and Gemini access.

---

## Key Features

### What the App Does

1. **Collects Metadata** - Journalist provides basic info (date, location, source, verification)
2. **Uploads Video** - User uploads UGC video file
3. **AI Analysis** - Google Gemini analyzes video content
4. **Generates Metadata** - Creates Reuters-compliant:
   - SLUG
   - HEADLINE
   - INTRO
   - VIDEO SHOWS
   - SHOTLIST (with dateline and shot descriptions)
   - STORY (3-4 paragraphs)
5. **Review & Edit** - Journalist reviews and refines before export
6. **Export** - Outputs in multiple formats (JSON, plain text, Reuters Connect)

### AI Model

**Google Gemini Flash 2.5** via Thomson Reuters authentication system

**Why Gemini Flash 2.5?**
- Fast processing (suitable for breaking news)
- Native video understanding (up to 1 hour)
- Multi-modal (video + audio + text)
- Cost-effective
- Structured JSON output

### Authentication

**Thomson Reuters Centralized Auth System**
- Provides OAuth2 tokens for Gemini access
- Includes: workspace_id, project_id, region
- Automatic token refresh (every 50 minutes)
- Secure credential management

---

## Quick Start Guide

### Prerequisites

1. Thomson Reuters credentials:
   - `WORKSPACE_ID`
   - `CREDENTIALS_URL`
   - Access to Gemini models

2. Development environment:
   - Python 3.9+
   - Node.js 18+ (for frontend)
   - PostgreSQL 14+
   - Redis (for caching)

### Environment Setup

```bash
# .env file
WORKSPACE_ID=your-tr-workspace-id
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://your-tr-auth-endpoint/api/token

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ugc_app
REDIS_URL=redis://localhost:6379

# Storage
STORAGE_PROVIDER=s3  # or gcs, azure
STORAGE_BUCKET=ugc-videos-bucket
```

### Installation Steps

```bash
# 1. Clone repository
git clone <repo-url>
cd ugc-video-metadata-app

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Initialize database
python scripts/init_db.py

# 5. Test authentication
python scripts/test_auth.py

# 6. Run development server
# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

### Testing Authentication

```python
# test_auth.py
from modules.auth import initialize_auth
from modules.gemini_enhancer import GeminiEnhancer

# Initialize TR authentication
workspace_id, model_name = initialize_auth()
print(f"✓ Authenticated - Workspace: {workspace_id}")

# Test Gemini access
enhancer = GeminiEnhancer()
print(f"✓ Gemini initialized with model: {model_name}")
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│              (React + Next.js + Tailwind CSS)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                    (FastAPI / Python)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                            ↓
┌──────────────────┐                    ┌──────────────────────┐
│  TR Auth Service │                    │   Video Processing   │
│  - Get token     │                    │   - FFmpeg analysis  │
│  - Refresh token │                    │   - File validation  │
└──────────────────┘                    └──────────────────────┘
        ↓                                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Google Gemini (via Vertex AI)                   │
│  - Video analysis                                            │
│  - Metadata generation                                       │
│  - Structured JSON output                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Metadata Processing                        │
│  - Validation                                                │
│  - Quality checks                                            │
│  - Format generation                                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                            ↓
┌──────────────────┐                    ┌──────────────────────┐
│    PostgreSQL    │                    │   File Storage       │
│  - User data     │                    │   (S3/GCS/Azure)     │
│  - Metadata      │                    │   - Video files      │
│  - Audit logs    │                    │   - Generated docs   │
└──────────────────┘                    └──────────────────────┘
```

---

## Technology Stack

### Frontend
- **Framework:** React + Next.js 14
- **UI:** Tailwind CSS + Shadcn/ui
- **Forms:** React Hook Form + Zod
- **State:** Zustand
- **Video:** Video.js

### Backend
- **Framework:** Python FastAPI
- **AI SDK:** Google Vertex AI SDK
- **Video:** FFmpeg
- **Tasks:** Celery + Redis
- **Database:** PostgreSQL + SQLAlchemy

### Infrastructure
- **Cloud:** Google Cloud Platform (for Gemini)
- **Containers:** Docker + Kubernetes
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry + DataDog

---

## Key Workflows

### 1. User Input Collection (5 Steps)

```
Step 1: User Info & Story Context
  ↓
Step 2: Source & Usage Rights
  ↓
Step 3: Location Details
  ↓
Step 4: Verification Methods
  ↓
Step 5: Video Upload
```

### 2. AI Processing

```
Video Upload
  ↓
TR Authentication (get token)
  ↓
Initialize Vertex AI with TR credentials
  ↓
Send video + metadata to Gemini
  ↓
Receive structured analysis
  ↓
Generate all metadata fields
  ↓
Validate & quality check
  ↓
Present for review
```

### 3. Export Options

- JSON (structured data)
- Plain text (Reuters format)
- Reuters Connect ready
- Email to desk
- PDF summary

---

## Reuters Style Guidelines

The app automatically follows Reuters production guidelines:

### Headlines
- 6-8 words
- Present tense, active voice
- Include location
- Start with "Eyewitness video shows" for UGC

### Shotlists
- Use -ing verbs (WALKING, RISING, FIRING)
- Number each shot
- Include DATELINE: LOCATION (DATE) (SOURCE – Restrictions)
- No camera terms (wide, pan, cutaway)

### Stories
- Simple past tense
- 3-4 paragraphs for UGC
- Include verification statement
- British spelling (except US stories)

### Sources & Restrictions
```
Format:
Broadcast: [restrictions]
Digital: [restrictions]

Example:
Broadcast: No resale / No archive / Must on-screen courtesy 'Eugene Odiya'
Digital: No resale / No archive / Must on-screen courtesy 'Eugene Odiya'
```

---

## Cost Estimates

### Gemini API Costs (Approximate)

| Video Duration | Processing Cost | Monthly (100 videos) |
|----------------|-----------------|---------------------|
| 30 seconds     | $0.0003         | $0.03               |
| 60 seconds     | $0.0006         | $0.06               |
| 2 minutes      | $0.0012         | $0.12               |
| 5 minutes      | $0.0030         | $0.30               |

**Notes:**
- Gemini Flash 2.5 is cost-effective ($0.01 per 1000 seconds of video)
- Output tokens add minimal cost (~$0.00015 per analysis)
- Production costs scale linearly with usage

---

## Performance Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Time to publish UGC | < 15 min | Development |
| AI accuracy rate | > 85% | TBD |
| User satisfaction | > 4/5 | TBD |
| Cost per video | < $0.002 | Estimated |
| System uptime | > 99.5% | TBD |

---

## Security Features

- **Authentication:** TR OAuth2 tokens
- **Encryption:** TLS in transit, AES-256 at rest
- **Access Control:** Role-based permissions
- **Audit Trail:** All actions logged
- **Data Privacy:** GDPR compliant
- **Token Security:** Automatic refresh, never logged

---

## Development Roadmap

### Phase 1: MVP (Months 1-2)
- [ ] Core authentication system
- [ ] Basic user input flow (5 steps)
- [ ] Gemini integration
- [ ] Basic metadata generation
- [ ] Simple review interface

### Phase 2: Production Ready (Months 3-4)
- [ ] Advanced validation
- [ ] Quality scoring
- [ ] Multiple export formats
- [ ] Error handling & retry logic
- [ ] Monitoring & alerting

### Phase 3: Enhancement (Months 5-6)
- [ ] Batch processing
- [ ] Template system
- [ ] Integration with Reuters Connect
- [ ] Mobile app for field journalists
- [ ] Advanced analytics

---

## Testing Strategy

### Unit Tests
- Authentication module
- Metadata generation logic
- Validation rules
- Utility functions

### Integration Tests
- TR auth flow
- Gemini API integration
- Database operations
- Export functionality

### End-to-End Tests
- Complete user workflow
- Various video formats
- Error scenarios
- Performance testing

### User Acceptance Testing
- Test with Reuters journalists
- Gather feedback on AI accuracy
- Refine prompts based on results

---

## Support & Documentation

### Internal Documentation
- API documentation (auto-generated from FastAPI)
- Database schema documentation
- Deployment runbooks
- Troubleshooting guides

### User Documentation
- User guide for journalists
- Video tutorials
- Style guide reference
- FAQ

### Developer Documentation
- Setup guide (this file)
- API reference
- Architecture diagrams
- Code examples

---

## Contact & Resources

### Project Team
- **Product Owner:** [Name]
- **Tech Lead:** [Name]
- **Backend Developer:** [Name]
- **Frontend Developer:** [Name]
- **AI/ML Engineer:** [Name]

### Resources
- **Main Proposal:** `ugc-video-metadata-app-proposal.md`
- **Auth Guide:** `tr-authentication-gemini-integration.md`
- **Reuters Style:** `RVN_PRODUCTION_GUIDELINES_2022_1.pdf`

### External Links
- [Thomson Reuters Developer Portal](https://developers.thomsonreuters.com)
- [Google Gemini Documentation](https://ai.google.dev/gemini-api/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)

---

## Next Steps

1. **Review Documentation** - Read both main documents thoroughly
2. **Setup Environment** - Configure TR credentials and local environment
3. **Test Authentication** - Verify TR auth and Gemini access
4. **Build MVP** - Start with core features (Steps 1-5 + basic Gemini)
5. **User Testing** - Test with small group of journalists
6. **Iterate** - Refine based on feedback
7. **Production Deploy** - Gradual rollout to all bureaus

---

**Last Updated:** October 24, 2025  
**Version:** 1.0  
**Status:** Ready for Development
