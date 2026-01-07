import streamlit as st
import hashlib
from datetime import datetime
from upwork_agent.config import load_secrets
from upwork_agent.gemini_client import GeminiClient, GeminiClientError
from upwork_agent.google_auth import get_authenticated_slides_service, get_authenticated_drive_service
from upwork_agent.slides_render import render_deck_to_slides
from upwork_agent.pdf_export import export_slides_to_pdf, cleanup_presentation
from upwork_agent.store import init_db, log_run, get_all_projects, add_project
from upwork_agent.relevance import score_projects, format_projects_for_gemini
from upwork_agent.errors import AuthenticationError

# Initialize
st.set_page_config(page_title="Upwork Proposal Agent", layout="wide")
st.title("🚀 Upwork Proposal Agent")
st.markdown("*Powered by Gemini AI | Generate polished proposals in minutes*")

# Initialize database
init_db()

# Sidebar: Settings + Project Management
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Gemini Model Selection
    st.subheader("Gemini Configuration")
    gemini_api_key = st.text_input(
        "Your Gemini API Key",
        type="password",
        help="Get it from https://ai.google.dev/api-keys"
    )
    
    gemini_models = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    selected_model = st.selectbox("Select Gemini Model", gemini_models)
    
    # Google Auth
    st.subheader("Google Cloud Auth")
    _, gcp_json_default = load_secrets()
    gcp_json = st.text_area(
        "Google Service Account JSON (paste entire JSON)",
        value=gcp_json_default or "",
        height=150,
        help="Used for Slides & Drive API access. Must include: type, project_id, private_key, client_email"
    )
    
    # Validate JSON format if provided
    if gcp_json:
        try:
            import json
            json.loads(gcp_json)
            st.success("✅ JSON format is valid")
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON format - please check your JSON")
    else:
        st.warning("⚠️ Google Service Account JSON is required for PDF generation")
    
    st.divider()
    
    # Digital Twin Management
    st.subheader("📚 Your Digital Twin")
    st.markdown("*Store your projects for relevance matching*")
    
    with st.expander("Add/Edit Projects"):
        project_name = st.text_input("Project Name", key="project_name")
        project_desc = st.text_area("Description", key="project_desc")
        project_techs = st.text_input("Tech Tags (comma-separated)", key="project_techs")
        project_outcomes = st.text_area("Outcomes & Metrics", key="project_outcomes")
        project_vertical = st.text_input("Vertical/Industry (optional)", key="project_vertical")
        project_link = st.text_input("Portfolio Link (optional)", key="project_link")
        
        if st.button("➕ Add Project", key="add_project"):
            if project_name and project_desc and project_outcomes:
                tech_list = [t.strip() for t in project_techs.split(",")]
                add_project(
                    name=project_name,
                    description=project_desc,
                    tech_tags=tech_list,
                    outcomes=project_outcomes,
                    vertical=project_vertical if project_vertical else None,
                    portfolio_link=project_link if project_link else None
                )
                st.success("Project added!")
                st.rerun()
            else:
                st.error("Please fill in required fields")
    
    # Show existing projects
    projects = get_all_projects()
    if projects:
        st.markdown(f"**Stored Projects: {len(projects)}**")
        for proj in projects:
            st.caption(f"• {proj['name']}")

# Main Interface
col1, col2, col3 = st.columns([1.2, 1.2, 1.2])

with col1:
    st.subheader("📋 Job Details")
    job_text = st.text_area(
        "Paste Upwork Job Post",
        height=250,
        placeholder="Paste the full job description from Upwork..."
    )
    
    tone_override = st.selectbox(
        "Communication Tone (override AI detection)",
        ["Auto-detect", "Technical", "Corporate", "Casual", "Direct"]
    )

with col2:
    st.subheader("🧠 Proposal Analysis")
    placeholder_analysis = st.empty()
    placeholder_cover = st.empty()

with col3:
    st.subheader("📄 PDF Output")
    placeholder_pdf = st.empty()

# Generate Button
st.divider()
if st.button("🚀 Analyze & Generate Proposal", key="main_generate"):
    # Validation
    if not gemini_api_key:
        st.error("❌ Please provide your Gemini API key")
        st.stop()
    
    if not gcp_json:
        st.error("❌ Please provide Google service account JSON")
        st.stop()
    
    if not job_text.strip():
        st.error("❌ Please paste a job description")
        st.stop()
    
    # Start generation
    st.session_state.generating = True
    
    try:
        # Initialize clients
        gemini_client = GeminiClient(api_key=gemini_api_key, model_name=selected_model)
        
        # Test Google authentication first
        with st.spinner("🔐 Authenticating with Google APIs..."):
            try:
                slides_service = get_authenticated_slides_service(gcp_json)
                drive_service = get_authenticated_drive_service(gcp_json)
                st.success("✅ Google authentication successful")
            except AuthenticationError as e:
                st.error(f"❌ Google authentication failed: {str(e)}")
                st.error("Please check your service account JSON and ensure it has the correct permissions for Google Slides and Drive APIs.")
                st.stop()
        
        # Step 1: Job Analysis
        with st.spinner("🔍 Analyzing job posting..."):
            job_analysis = gemini_client.generate_job_analysis(job_text)
        
        with col2:
            with placeholder_analysis.container():
                st.json(job_analysis.model_dump(), expanded=False)
        
        # Step 2: Project Relevance Matching
        with st.spinner("🎯 Finding relevant projects..."):
            scored = score_projects(job_analysis)
            relevant_projects = format_projects_for_gemini(scored)
        
        # Step 3: Generate Slide Deck
        with st.spinner("🎨 Generating slide content..."):
            tone_for_slides = None if tone_override == "Auto-detect" else tone_override
            slide_deck_spec = gemini_client.generate_slide_deck(
                job_analysis, 
                relevant_projects,
                tone_override=tone_for_slides
            )
        
        # Step 4: Render to Google Slides
        with st.spinner("📊 Building Google Slides..."):
            presentation_id = render_deck_to_slides(slide_deck_spec, slides_service)
        
        # Step 5: Export to PDF
        with st.spinner("📥 Exporting to PDF..."):
            pdf_bytes = export_slides_to_pdf(presentation_id, drive_service)
            cleanup_presentation(presentation_id, drive_service)
        
        # Step 6: Generate Cover Letter
        with st.spinner("✍️ Writing cover letter..."):
            cover_letter = gemini_client.generate_cover_letter(job_analysis, relevant_projects)
        
        # Step 7: Auto-generate Screening Answers
        with st.spinner("❓ Generating screening answers..."):
            screening_answers = gemini_client.generate_screening_answers(job_analysis)
        
        # Display Results
        with col2:
            with placeholder_cover.container():
                st.markdown("**Cover Letter:**")
                st.text_area("", value=cover_letter, height=150, disabled=True)
                
                st.markdown("**Screening Answers:**")
                for q, a in screening_answers.items():
                    st.text_area(f"Q: {q}", value=a, height=80, disabled=True)
        
        # PDF Download
        with col3:
            st.markdown("**📥 Download Proposal PDF**")
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"upwork_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ Proposal generated successfully!")
        
        # Log Run
        job_hash = hashlib.md5(job_text.encode()).hexdigest()
        log_run(
            job_text_hash=job_hash,
            job_analysis_json=job_analysis.model_dump_json(),
            proposal_json=slide_deck_spec.model_dump_json(),
            model_name=selected_model,
            presentation_id=presentation_id,
            status="success"
        )
    
    except GeminiClientError as e:
        st.error(f"❌ Gemini Error: {e}")
        log_run(
            job_text_hash=hashlib.md5(job_text.encode()).hexdigest(),
            job_analysis_json="",
            proposal_json="",
            model_name=selected_model,
            presentation_id="",
            status="failed",
            error_message=str(e)
        )
    
    except Exception as e:
        st.error(f"❌ Unexpected Error: {e}")
        log_run(
            job_text_hash=hashlib.md5(job_text.encode()).hexdigest(),
            job_analysis_json="",
            proposal_json="",
            model_name=selected_model,
            presentation_id="",
            status="failed",
            error_message=str(e)
        )
    
    finally:
        st.session_state.generating = False
