from upwork_agent.schemas import JobAnalysis
from upwork_agent.relevance import score_projects
from upwork_agent.store import init_db

def test_score_projects():
    # Initialize database for testing
    init_db()
    
    job = JobAnalysis(
        pain_points=["Need Python development"],
        persona="technical",
        tech_stack=["Python", "Django"],
        unspoken_needs=[],
        budget_signal="mid-market",
        timeline_signal="standard",
    )
    # Test that scoring works (may return empty list if no projects)
    scored = score_projects(job)
    assert isinstance(scored, list)
