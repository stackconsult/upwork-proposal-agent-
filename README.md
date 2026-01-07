# Upwork Proposal Agent

A Streamlit application that generates polished, personalized Upwork proposals using Gemini AI. User inputs a job posting, selects a Gemini model, provides their API key, and receives:

- AI-analyzed job details
- A full 8-slide Google Slides presentation (Gemini generates 100% of content)
- Auto-generated screening question answers
- A downloadable PDF proposal

## Architecture Stack

- **Frontend**: Streamlit (Community Cloud deployment)
- **AI**: Gemini API (user-selected model, user-provided API key)
- **Slides**: Google Slides API (create from scratch, no templates)
- **PDF Export**: Google Drive API
- **Database**: SQLite (local, stores your projects/"Digital Twin")
- **Auth**: Google Cloud service account (for Slides/Drive access)
- **Version Control**: GitHub
- **CI/CD**: GitHub Actions (lint + test on push)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd upwork-proposal-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up secrets**
   Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   GOOGLE_SERVICE_ACCOUNT_JSON = '''{"type": "service_account", ...}'''
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

### Required Google Cloud Setup

1. Create a Google Cloud project
2. Enable Google Slides API and Google Drive API
3. Create a service account with the following scopes:
   - `https://www.googleapis.com/auth/presentations`
   - `https://www.googleapis.com/auth/drive`
4. Download the service account JSON key

## Features

### Digital Twin (Project Database)
The app stores your past projects in a local SQLite database to enable intelligent relevance matching. Add your projects through the sidebar interface:

- Project name and description
- Technology tags
- Outcomes and metrics
- Vertical/industry
- Portfolio links

### AI-Powered Analysis
- **Job Analysis**: Extracts pain points, client persona, tech stack, unspoken needs, budget/timeline signals
- **Slide Generation**: Creates 8 compelling slides with specific, data-backed content
- **Cover Letter**: Personalized 250-350 word letter addressing client needs
- **Screening Answers**: Auto-generated responses to common Upwork screening questions

### 8-Slide Proposal Structure
1. **Title**: Client name + compelling tagline
2. **Problem**: Validate pain points with proof
3. **Approach**: Detailed methodology
4. **Case Study 1**: Full results + metrics
5. **Case Study 2**: Full results + metrics  
6. **Timeline**: Phased approach with milestones
7. **Investment**: Budget/scope breakdown
8. **CTA**: Next steps + contact info

## Testing

```bash
# Run tests
pytest -v

# Lint code
ruff check .

# Run with coverage
pytest --cov=upwork_agent tests/
```

## Deployment to Streamlit Community Cloud

1. Push code to GitHub repository
2. Go to https://streamlit.io/cloud
3. Connect GitHub account and select repository
4. Click "Deploy"
5. Add secrets in Advanced Settings:
   - `GEMINI_API_KEY`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (paste entire JSON)

The app will automatically deploy and update on each push.

## Project Structure

```
upwork-proposal-agent/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions: ruff + pytest
├── .gitignore
├── .streamlit/
│   └── config.toml
├── src/upwork_agent/
│   ├── __init__.py
│   ├── config.py                  # Load secrets, env, API keys
│   ├── schemas.py                 # Pydantic models + JSON schemas
│   ├── gemini_client.py           # Structured output calls to Gemini
│   ├── google_auth.py             # Slides + Drive service auth
│   ├── store.py                   # SQLite operations (projects CRUD)
│   ├── relevance.py               # Keyword-based project scoring
│   ├── slides_render.py           # Build Google Slides from SlideDeckSpec
│   ├── pdf_export.py              # Export Slides to PDF
│   └── errors.py                  # Custom exceptions
├── tests/
│   ├── test_schemas.py            # Pydantic validation
│   └── test_relevance.py          # Scoring logic
├── app.py                         # Streamlit main entry
├── pyproject.toml                 # Dependencies + tooling
├── README.md                      # This file
└── data/
    └── profile.db                 # SQLite database (gitignored)
```

## Key Design Decisions

- **User provides API key**: No server-side key storage for security
- **Gemini creates 100% of slides**: No templates, pure AI generation
- **Google Cloud for rendering**: Production-quality PDFs via Slides API
- **Streamlit Community Cloud**: Free deployment with built-in secrets
- **Local SQLite**: Your Digital Twin stays private
- **Batch rendering**: One API call with 100+ operations for efficiency
- **Structured output**: JSON schema validation for reliable responses

## Troubleshooting

### Common Issues

1. **Google API Authentication Errors**
   - Ensure service account has proper scopes
   - Verify JSON is correctly formatted
   - Check that APIs are enabled in Google Cloud Console

2. **Gemini API Errors**
   - Verify API key is valid
   - Check model availability in your region
   - Monitor quota limits

3. **PDF Export Issues**
   - Ensure Drive API is enabled
   - Check service account permissions
   - Verify presentation ID is valid

### Debug Mode

Set environment variable for verbose logging:
```bash
export STREAMLIT_LOG_LEVEL=debug
streamlit run app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `pytest -v` and `ruff check .`
6. Submit a pull request

## License

This project is licensed under the MIT License.
