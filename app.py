import streamlit as st
import hashlib
from upwork_agent.config import load_secrets
from upwork_agent.gemini_client import GeminiClient, GeminiClientError
from upwork_agent.store import init_db, log_run, get_all_projects, add_project
from upwork_agent.relevance import score_projects, format_projects_for_gemini

# Initialize
st.set_page_config(page_title="Upwork Proposal Agent", layout="wide")
st.title("🚀 Upwork Proposal Agent")
st.markdown("*Powered by Gemini AI | Generate polished proposals in minutes*")

# Initialize database
init_db()

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
                add_project(
                    name=project_name,
                    description=project_desc,
                    tech_tags=[t.strip() for t in project_techs.split(",")],
                    outcomes=project_outcomes,
                    vertical=project_vertical,
                    portfolio_link=project_link
                )
                st.success("✅ Project saved!")
                st.rerun()
            else:
                st.error("❌ Please fill in required fields")
    
    # Show existing projects
    projects = get_all_projects()
    if projects:
        st.subheader("📋 Existing Projects")
        for project in projects:
            with st.expander(f"📁 {project['name']}"):
                st.write(f"**Description:** {project['description']}")
                st.write(f"**Tech:** {', '.join(project['tech_tags'])}")
                st.write(f"**Outcomes:** {project['outcomes']}")

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
    
    if not job_text.strip():
        st.error("❌ Please paste a job description")
        st.stop()
    
    # Start generation
    st.session_state.generating = True
    
    try:
        # Initialize Gemini client
        gemini_client = GeminiClient(api_key=gemini_api_key, model_name=selected_model)
        
        # Step 1: Job Analysis
        with st.spinner("🔍 Analyzing job posting..."):
            job_analysis = gemini_client.generate_job_analysis(job_text)
        
        with col2:
            with placeholder_analysis.container():
                st.json(job_analysis.model_dump(), expanded=False)
        
        # Step 2: Project Relevance Matching
        with st.spinner("🎯 Finding relevant projects..."):
            scored_projects = score_projects(job_analysis)
            relevant_projects = format_projects_for_gemini(scored_projects)
        
        # Step 3: Generate Slide Deck
        tone = None if tone_override == "Auto-detect" else tone_override.lower()
        with st.spinner("📊 Creating proposal slides..."):
            slide_deck = gemini_client.generate_slide_deck(
                job_analysis, 
                relevant_projects, 
                tone_override=tone
            )
        
        # Step 4: Generate Cover Letter
        with st.spinner("✍️ Writing cover letter..."):
            cover_letter = gemini_client.generate_cover_letter(job_analysis, relevant_projects)
        
        # Step 5: Generate Screening Answers
        screening_answers = gemini_client.generate_screening_answers(job_analysis)
        
        # Display Results
        with col2:
            with placeholder_cover.container():
                st.subheader("📝 Cover Letter")
                st.text_area("", cover_letter, height=200, disabled=True)
                
                st.subheader("❓ Common Screening Answers")
                for question, answer in screening_answers.items():
                    st.write(f"**Q:** {question}")
                    st.write(f"**A:** {answer}")
                    st.write("---")
        
        with col3:
            with placeholder_pdf.container():
                st.subheader("📊 Slide Deck Content")
                
                # Display slides as formatted text
                for i, slide in enumerate(slide_deck.slides, 1):
                    st.write(f"### Slide {i}: {slide.title}")
                    for bullet in slide.content:
                        st.write(f"- {bullet}")
                    st.write("---")
                
                # Download as text file
                slide_text = f"PROPOSAL: {slide_deck.presentation_title}\n\n"
                slide_text += f"CLIENT ANALYSIS:\n{job_analysis.model_dump_json(indent=2)}\n\n"
                slide_text += f"COVER LETTER:\n{cover_letter}\n\n"
                slide_text += "SLIDES:\n"
                for i, slide in enumerate(slide_deck.slides, 1):
                    slide_text += f"\n--- SLIDE {i}: {slide.title} ---\n"
                    slide_text += "\n".join([f"- {bullet}" for bullet in slide.content])
                    slide_text += "\n"
                
                st.download_button(
                    label="📥 Download Proposal (Text)",
                    data=slide_text,
                    file_name=f"proposal_{hashlib.md5(job_text.encode()).hexdigest()[:8]}.txt",
                    mime="text/plain"
                )
        
        # Log the run
        log_run(job_text[:500], slide_deck.presentation_title, "success")
        
        st.success("✅ Proposal generated successfully!")
        st.session_state.generating = False
        
    except GeminiClientError as e:
        st.error(f"❌ Gemini API Error: {str(e)}")
        log_run(job_text[:500], "Failed", f"Gemini Error: {str(e)}")
        st.session_state.generating = False
    
    except Exception as e:
        st.error(f"❌ Unexpected Error: {str(e)}")
        log_run(job_text[:500], "Failed", f"Unexpected Error: {str(e)}")
        st.session_state.generating = False
    
    finally:
        st.session_state.generating = False
