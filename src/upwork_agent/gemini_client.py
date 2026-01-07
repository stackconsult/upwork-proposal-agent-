import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import ValidationError
from typing import Optional
from upwork_agent.schemas import (
    JobAnalysis, SlideDeckSpec,
    get_job_analysis_schema, get_slide_deck_schema
)

class GeminiClientError(Exception):
    pass

class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        """
        Initialize Gemini client.
        Args:
            api_key: User-provided Gemini API key
            model_name: Model name (e.g., 'gemini-2.0-flash', 'gemini-2.5-flash')
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_job_analysis(self, job_text: str) -> JobAnalysis:
        """
        First call: Analyze the job post.
        Returns structured JobAnalysis.
        """
        prompt = f"""Analyze this Upwork job posting and extract key insights.

JOB POSTING:
{job_text}

Return ONLY valid JSON matching this schema:
{get_job_analysis_schema()}

Focus on:
- Core pain points (2-3, be specific)
- Client communication style/persona
- Tech stack (explicit + inferred)
- Unspoken needs (what they really need but didn't say)
- Budget and timeline signals
- Any red flags or missing context
"""
        
        response = self.client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=get_job_analysis_schema(),
            )
        )
        
        try:
            return JobAnalysis.model_validate_json(response.text)
        except ValidationError as e:
            raise GeminiClientError(f"Job analysis validation failed: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_slide_deck(
        self, 
        job_analysis: JobAnalysis, 
        relevant_projects: list[str],
        tone_override: Optional[str] = None
    ) -> SlideDeckSpec:
        """
        Second call: Generate full 8-slide specification.
        Gemini creates 100% of content; no templates.
        
        Args:
            job_analysis: JobAnalysis object from first call
            relevant_projects: List of formatted project summaries (top 3)
            tone_override: Override persona tone if user specified
        """
        
        tone = tone_override or job_analysis.persona
        
        prompt = f"""You are a world-class proposal writer. Generate an 8-slide vertical proposal deck.

CLIENT CONTEXT:
Pain Points: {', '.join(job_analysis.pain_points)}
Persona: {tone}
Tech Stack: {', '.join(job_analysis.tech_stack)}
Timeline: {job_analysis.timeline_signal}
Budget Level: {job_analysis.budget_signal}

YOUR RELEVANT PROJECTS:
{chr(10).join(relevant_projects)}

TASK: Generate exactly 8 slides. Fill each with real, specific, persuasive content.

Slide 1 (Title): "{'{client_name}'} Proposal" + compelling tagline addressing their #1 pain point
Slide 2 (Problem): Validate their pain points with specific proof from your projects
Slide 3 (Your Approach): Detailed methodology/process for solving their problem
Slide 4 (Case Study 1): Full results + metrics from one relevant project
Slide 5 (Case Study 2): Full results + metrics from another relevant project
Slide 6 (Timeline): Phased approach with 3-5 milestones
Slide 7 (Investment): Budget/scope breakdown (or "pending discovery" if unclear)
Slide 8 (CTA): Next steps + contact info + urgency

For each slide:
- Title: 5-10 words max
- Content: Specific, data-backed, no generic filler
- Tone: {tone} (match their communication style)
- Bullets should be punchy (10-15 words each)
- Include metrics/proof wherever possible

Gemini, you are creating the ENTIRE proposal deck. Make it polished, compelling, and ready to win the job.

Return ONLY valid JSON matching this schema:
{get_slide_deck_schema()}
"""
        
        response = self.client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=get_slide_deck_schema(),
            )
        )
        
        try:
            return SlideDeckSpec.model_validate_json(response.text)
        except ValidationError as e:
            raise GeminiClientError(f"Slide deck validation failed: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_cover_letter(
        self, 
        job_analysis: JobAnalysis, 
        relevant_projects: list[str]
    ) -> str:
        """
        Third call: Generate cover letter (text only, not structured output).
        """
        prompt = f"""Write a compelling Upwork cover letter for this job.

CLIENT PAIN POINTS:
{', '.join(job_analysis.pain_points)}

CLIENT PERSONA: {job_analysis.persona}

YOUR RELEVANT PROJECTS:
{chr(10).join(relevant_projects)}

Requirements:
- 250-350 words
- Directly address their pain points
- Reference specific projects as proof
- Tone: {job_analysis.persona}
- Confident but not arrogant
- Include specific value proposition

Return ONLY the cover letter text. No metadata, no JSON, no explanations.
"""
        
        response = self.client.generate_content(prompt)
        return response.text.strip()
    
    def generate_screening_answers(self, job_analysis: JobAnalysis) -> dict[str, str]:
        """
        Auto-generate answers to common screening questions based on job analysis.
        """
        common_questions = {
            "What's your availability?": "Available immediately for this project.",
            "What's your hourly rate or project fee?": "Rates vary based on scope; happy to discuss.",
            "Can you work in our timezone?": "Yes, flexible with timezone and working hours.",
            "Tell us about your experience with [tech].": f"Extensive experience with {', '.join(job_analysis.tech_stack[:2])} and related tech.",
            "How do you handle revisions?": "Unlimited revisions until you're satisfied; quality is my priority.",
        }
        return common_questions
