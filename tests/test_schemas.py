from upwork_agent.schemas import (
    JobAnalysis, SlideSpec, SlideDeckSpec,
    get_job_analysis_schema
)

def test_job_analysis_schema():
    job = JobAnalysis(
        pain_points=["Need faster deployment"],
        persona="technical",
        tech_stack=["Python", "AWS"],
        unspoken_needs=["reliability"],
        budget_signal="mid-market",
        timeline_signal="standard",
    )
    assert job.pain_points == ["Need faster deployment"]

def test_slide_deck_schema():
    spec = SlideDeckSpec(
        presentation_title="Test Proposal",
        proposal_intro="Introduction text",
        slides=[SlideSpec(
            slide_number=i+1,
            title=f"Slide {i+1}",
            slide_type="content",
            sections=[]
        ) for i in range(8)],
        cta_statement="Let's talk!"
    )
    assert len(spec.slides) == 8

def test_job_analysis_json_schema():
    schema = get_job_analysis_schema()
    assert "properties" in schema
    assert "pain_points" in schema["properties"]
