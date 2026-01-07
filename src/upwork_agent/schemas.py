from pydantic import BaseModel, Field
from typing import Literal, Optional

class JobAnalysis(BaseModel):
    """Result of first Gemini call: analyze the job post."""
    pain_points: list[str] = Field(
        ..., 
        description="2-3 core business problems the client faces"
    )
    persona: str = Field(
        ..., 
        description="Tone of client: 'technical', 'corporate', 'startup-informal', 'direct'"
    )
    tech_stack: list[str] = Field(
        ..., 
        description="Explicit + inferred technologies mentioned"
    )
    unspoken_needs: list[str] = Field(
        ..., 
        description="Implicit requirements (e.g., 'reliability', 'speed', 'scalability')"
    )
    budget_signal: str = Field(
        ..., 
        description="'enterprise', 'mid-market', 'bootstrap', or 'unknown'"
    )
    timeline_signal: str = Field(
        ..., 
        description="'urgent', 'standard', 'flexible', or 'unknown'"
    )
    red_flags: list[str] = Field(
        default_factory=list, 
        description="Scope creep, missing context, unrealistic expectations"
    )
    clarifying_questions: list[str] = Field(
        default_factory=list, 
        description="Questions to ask client during discovery"
    )

class SlideSection(BaseModel):
    """Content unit within a slide."""
    type: Literal["bullets", "paragraph", "callout", "metric", "heading"] = Field(
        ..., 
        description="Content type"
    )
    content: str | list[str] = Field(
        ..., 
        description="Single text string or list of bullet points"
    )
    emphasis: Optional[bool] = Field(
        default=False, 
        description="Bold/highlight this section"
    )

class SlideSpec(BaseModel):
    """Single slide specification."""
    slide_number: int = Field(..., ge=1, le=8)
    title: str = Field(..., description="Slide title (5-10 words)")
    subtitle: Optional[str] = Field(default=None, description="Optional subtitle")
    slide_type: Literal["title", "content", "two-column", "metrics", "timeline", "cta"] = Field(
        ..., 
        description="Layout type for Gemini to understand context"
    )
    sections: list[SlideSection] = Field(..., description="Content sections on this slide")
    notes: Optional[str] = Field(default=None, description="Speaker notes or context")

class SlideDeckSpec(BaseModel):
    """Complete 8-slide deck specification."""
    presentation_title: str = Field(..., description="Title of the proposal deck")
    proposal_intro: str = Field(..., description="50-100 word introduction")
    slides: list[SlideSpec] = Field(..., min_length=8, max_length=8, description="Exactly 8 slides")
    cta_statement: str = Field(..., description="Final call-to-action statement")

class ProposalPackComplete(BaseModel):
    """Final output: everything for the proposal."""
    cover_letter: str = Field(..., description="250-350 word personalized cover letter")
    screening_answers: dict[str, str] = Field(
        ..., 
        description="Auto-generated answers to common screening questions"
    )
    slide_deck_spec: SlideDeckSpec = Field(..., description="Full 8-slide specification")
    assumptions: list[str] = Field(
        default_factory=list, 
        description="Assumptions about scope / clarifications needed"
    )
    price_signal: Optional[str] = Field(
        default=None, 
        description="Ballpark pricing guidance (if appropriate)"
    )

def get_job_analysis_schema() -> dict:
    """Export Pydantic schema for Gemini structured output."""
    return JobAnalysis.model_json_schema()

def get_slide_deck_schema() -> dict:
    """Export Pydantic schema for Gemini structured output."""
    return SlideDeckSpec.model_json_schema()

def get_proposal_pack_schema() -> dict:
    """Export Pydantic schema for Gemini structured output."""
    return ProposalPackComplete.model_json_schema()
