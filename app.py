import streamlit as st
import hashlib
import logging
from upwork_agent.config import load_secrets, init_session_state, rate_limit_check, update_api_call_stats, cleanup_session_state
from upwork_agent.gemini_client import GeminiClient, GeminiClientError, GeminiRateLimitError, GeminiQuotaExceededError
from upwork_agent.store import init_db, log_run, get_all_projects, add_project, cleanup_old_runs
from upwork_agent.relevance import score_projects, format_projects_for_gemini

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize
st.set_page_config(page_title="Upwork Proposal Agent", layout="wide")
st.title("🚀 Upwork Proposal Agent")
st.markdown("*Powered by Gemini AI | Generate polished proposals in minutes*")

# Initialize database and session state
init_db()
init_session_state()

# Sidebar: Settings + Project Management
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Gemini API Key
    gemini_api_key_default, _ = load_secrets()
    gemini_api_key = st.text_input(
        "Gemini API Key",
        value=gemini_api_key_default or "",
        type="password",
        help="Your Google Gemini API key"
    )
    
    # Model Selection
    gemini_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash", 
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    selected_model = st.selectbox("Select Gemini Model", gemini_models)
    
    # Rate limiting info
    if st.session_state.get("api_call_count", 0) > 0:
        st.info(f"API calls this minute: {st.session_state.api_call_count}")
    
    st.divider()
    
    # Digital Twin Management
    st.subheader("📚 Your Digital Twin")
    st.markdown("*Store your projects for relevance matching*")
    
    with st.expander("Add/Edit Projects"):
        project_name = st.text_input("Project Name", key="project_name")
        project_desc = st.text_area("Description", key="project_desc")
        project_techs = st.text_input("Tech Tags (comma-separated)", key="project_techs")
        project_outcomes = st.text_area("Outcomes/Results", key="project_outcomes")
        project_vertical = st.text_input("Vertical/Industry", key="project_vertical")
        project_link = st.text_input("Portfolio Link", key="project_link")
        
        if st.button("💾 Save Project", key="save_project"):
            if project_name and project_desc and project_techs and project_outcomes:
                try:
                    add_project(
                        name=project_name,
                        description=project_desc,
                        tech_tags=[t.strip() for t in project_techs.split(",")],
                        outcomes=project_outcomes,
                        vertical=project_vertical,
                        portfolio_link=project_link
                    )
                    st.success("✅ Project saved!")
                    # Clear form
                    st.session_state.project_name = ""
                    st.session_state.project_desc = ""
                    st.session_state.project_techs = ""
                    st.session_state.project_outcomes = ""
                    st.session_state.project_vertical = ""
                    st.session_state.project_link = ""
                except Exception as e:
                    st.error(f"❌ Failed to save project: {str(e)}")
            else:
                st.error("❌ Please fill in required fields")
    
    # Show existing projects
    try:
        projects = get_all_projects()
        if projects:
            st.subheader("📋 Existing Projects")
            for project in projects:
                with st.expander(f"📁 {project['name']}"):
                    st.write(f"**Description:** {project['description']}")
                    st.write(f"**Tech:** {', '.join(project['tech_tags'])}")
                    st.write(f"**Outcomes:** {project['outcomes']}")
    except Exception as e:
        st.warning("⚠️ Could not load projects")
        projects = []

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

with col3:
    st.subheader("📄 Proposal Output")

# Create placeholders for results
placeholder_analysis = st.empty()
placeholder_cover = st.empty()
placeholder_pdf = st.empty()

# Generate Button
st.divider()

if st.button("🚀 Analyze & Generate Proposal", key="main_generate", disabled=st.session_state.generating):
    # Validation
    if not gemini_api_key:
        st.error("❌ Please provide your Gemini API key")
        st.stop()
    
    if not gemini_api_key.strip().startswith("AIza"):
        st.error("❌ Invalid Gemini API key format - should start with 'AIza'")
        st.stop()
    
    if not job_text.strip():
        st.error("❌ Please paste a job description")
        st.stop()
    
    if len(job_text.strip()) < 50:
        st.error("❌ Job description too short for meaningful analysis")
        st.stop()
    
    # Rate limiting check
    if rate_limit_check():
        st.error("❌ Rate limit exceeded. Please wait before making another request.")
        st.stop()
    
    # Start generation
    st.session_state.generating = True
    update_api_call_stats()
    
    try:
        # Initialize Gemini client
        gemini_client = GeminiClient(api_key=gemini_api_key, model_name=selected_model)
        
        # Step 1: Job Analysis
        with st.spinner("🔍 Analyzing job posting..."):
            job_analysis = gemini_client.generate_job_analysis(job_text)
            st.session_state.job_analysis = job_analysis
        
        with placeholder_analysis.container():
            st.subheader("🧠 Job Analysis")
            st.json(job_analysis.model_dump(), expanded=False)
        
        # Step 2: Project Relevance Matching (with error handling)
        with st.spinner("🎯 Finding relevant projects..."):
            try:
                scored_projects = score_projects(job_analysis)
                relevant_projects = format_projects_for_gemini(scored_projects)
            except Exception as e:
                logger.warning(f"Project matching failed: {str(e)}")
                st.warning("⚠️ Project matching failed - using generic approach")
                relevant_projects = ["No specific projects available - will create general proposal"]
        
        # Step 3: Generate Slide Deck
        tone = None if tone_override == "Auto-detect" else tone_override.lower()
        with st.spinner("📊 Creating proposal slides..."):
            slide_deck = gemini_client.generate_slide_deck(
                job_analysis, 
                relevant_projects, 
                tone_override=tone
            )
            st.session_state.slide_deck = slide_deck
        
        # Step 4: Generate Cover Letter
        with st.spinner("✍️ Writing cover letter..."):
            cover_letter = gemini_client.generate_cover_letter(job_analysis, relevant_projects)
            st.session_state.cover_letter = cover_letter
        
        # Step 5: Generate Screening Answers
        screening_answers = gemini_client.generate_screening_answers(job_analysis)
        st.session_state.screening_answers = screening_answers
        
        # Display Results
        with placeholder_cover.container():
            st.subheader("📝 Cover Letter")
            st.text_area("Cover Letter", cover_letter, height=200, disabled=True)
            
            st.subheader("❓ Common Screening Answers")
            for question, answer in screening_answers.items():
                st.write(f"**Q:** {question}")
                st.write(f"**A:** {answer}")
                st.write("---")
        
        with placeholder_pdf.container():
            st.subheader("📊 Slide Deck Content")
            
            # Display slides as formatted text
            for i, slide in enumerate(slide_deck.slides, 1):
                st.write(f"### Slide {i}: {slide.title}")
                for section in slide.sections:
                    if isinstance(section.content, list):
                        for item in section.content:
                            st.write(f"- {item}")
                    else:
                        st.write(f"- {section.content}")
                st.write("---")
            
            # Download as text file
            slide_text = f"PROPOSAL: {slide_deck.presentation_title}\n\n"
            slide_text += f"CLIENT ANALYSIS:\n{job_analysis.model_dump_json(indent=2)}\n\n"
            slide_text += f"COVER LETTER:\n{cover_letter}\n\n"
            slide_text += "SLIDES:\n"
            for i, slide in enumerate(slide_deck.slides, 1):
                slide_text += f"\n--- SLIDE {i}: {slide.title} ---\n"
                for section in slide.sections:
                    if isinstance(section.content, list):
                        for item in section.content:
                            slide_text += f"- {item}\n"
                    else:
                        slide_text += f"- {section.content}\n"
                slide_text += "\n"
            
            st.download_button(
                label="📥 Download Proposal (Text)",
                data=slide_text,
                file_name=f"proposal_{hashlib.md5(job_text.encode()).hexdigest()[:8]}.txt",
                mime="text/plain"
            )
        
        # Log the run
        try:
            log_run(
                job_text_hash=hashlib.md5(job_text.encode()).hexdigest(),
                job_analysis_json=job_analysis.model_dump_json(),
                proposal_json=slide_deck.model_dump_json(),
                model_name=selected_model,
                presentation_id="",
                status="success"
            )
        except Exception as e:
            logger.warning(f"Failed to log run: {str(e)}")
        
        st.success("✅ Proposal generated successfully!")
        
        # Cleanup session state to prevent memory leaks
        cleanup_session_state()
        
    except GeminiRateLimitError as e:
        st.error(f"❌ Rate limit exceeded: {str(e)}")
        logger.warning(f"Rate limit hit: {str(e)}")
    except GeminiQuotaExceededError as e:
        st.error(f"❌ API quota exceeded: {str(e)}")
        logger.error(f"Quota exceeded: {str(e)}")
    except GeminiClientError as e:
        st.error(f"❌ Gemini API Error: {str(e)}")
        logger.error(f"Gemini error: {str(e)}")
        try:
            log_run(
                job_text_hash=hashlib.md5(job_text.encode()).hexdigest(),
                job_analysis_json="",
                proposal_json="",
                model_name=selected_model,
                presentation_id="",
                status="failed",
                error_message=str(e)
            )
        except Exception:
            pass
    except Exception as e:
        st.error(f"❌ Unexpected Error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        try:
            log_run(
                job_text_hash=hashlib.md5(job_text.encode()).hexdigest(),
                job_analysis_json="",
                proposal_json="",
                model_name=selected_model,
                presentation_id="",
                status="failed",
                error_message=str(e)
            )
        except Exception:
            pass
    
    finally:
        st.session_state.generating = False

# Footer with monitoring info
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔒 Your API keys are never stored")
with col2:
    st.caption("📊 Powered by Google Gemini AI")
with col3:
    st.caption("🚀 Built for Upwork success")
