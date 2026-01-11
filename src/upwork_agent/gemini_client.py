import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import ValidationError
from typing import Optional
import json
import logging
from upwork_agent.schemas import (
    JobAnalysis, SlideDeckSpec,
    get_job_analysis_schema, get_slide_deck_schema
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClientError(Exception):
    pass

class GeminiRateLimitError(GeminiClientError):
    pass

class GeminiQuotaExceededError(GeminiClientError):
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
        
        try:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise GeminiClientError(f"Failed to initialize Gemini client: {str(e)}")
    
    def _parse_json_response(self, response_text: str):
        """Extract JSON from response text with robust error handling."""
        if not response_text:
            raise ValueError("Empty response from Gemini")
        
        try:
            # Try to parse the response directly
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Last resort: try to fix common JSON issues
            cleaned_text = response_text.replace('\n', '').replace('\r', '')
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Could not extract valid JSON from response: {response_text[:200]}...")
    
    def _handle_api_error(self, error: Exception) -> None:
        """Handle different types of API errors appropriately."""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "too many requests" in error_str:
            raise GeminiRateLimitError("Rate limit exceeded. Please wait before making another request.")
        elif "quota" in error_str or "exceeded" in error_str:
            raise GeminiQuotaExceededError("API quota exceeded. Please check your usage limits.")
        elif "permission" in error_str or "forbidden" in error_str:
            raise GeminiClientError("Permission denied. Check your API key and permissions.")
        elif "invalid" in error_str and "key" in error_str:
            raise GeminiClientError("Invalid API key. Please check your credentials.")
        else:
            raise GeminiClientError(f"Gemini API error: {str(error)}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_job_analysis(self, job_text: str) -> JobAnalysis:
        """
        First call: Analyze the job post.
        Returns structured JobAnalysis.
        """
        if not job_text or len(job_text.strip()) < 50:
            raise ValueError("Job text too short for analysis")
        
        try:
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
                    temperature=0.3,
                )
            )
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            response_text = response.text
            parsed_json = self._parse_json_response(response_text)
            return JobAnalysis.model_validate(parsed_json)
            
        except ValidationError as e:
            logger.error(f"Validation error in job analysis: {str(e)}")
            raise GeminiClientError(f"Invalid response format from Gemini: {str(e)}")
        except ValueError as e:
            logger.error(f"JSON parsing error in job analysis: {str(e)}")
            raise GeminiClientError(f"Failed to parse Gemini response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in job analysis: {str(e)}")
            self._handle_api_error(e)
    
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
        """
        try:
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

Slide 1 (Title): "{{client_name}}" Proposal" + compelling tagline addressing their #1 pain point
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
                    temperature=0.3,
                )
            )
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            response_text = response.text
            parsed_json = self._parse_json_response(response_text)
            return SlideDeckSpec.model_validate(parsed_json)
            
        except ValidationError as e:
            logger.error(f"Validation error in slide deck: {str(e)}")
            raise GeminiClientError(f"Invalid response format from Gemini: {str(e)}")
        except ValueError as e:
            logger.error(f"JSON parsing error in slide deck: {str(e)}")
            raise GeminiClientError(f"Failed to parse Gemini response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in slide deck: {str(e)}")
            self._handle_api_error(e)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_cover_letter(
        self, 
        job_analysis: JobAnalysis, 
        relevant_projects: list[str]
    ) -> str:
        """
        Third call: Generate cover letter (text only, not structured output).
        """
        try:
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
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            self._handle_api_error(e)
    
    def generate_screening_answers(self, job_analysis: JobAnalysis) -> dict[str, str]:
        """
        Auto-generate answers to common screening questions based on job analysis.
        """
        try:
            common_questions = {
                "What's your availability?": "Available immediately for this project.",
                "What's your hourly rate or project fee?": "Rates vary based on scope; happy to discuss.",
                "Can you work in our timezone?": "Yes, flexible with timezone and working hours.",
                "Tell us about your experience with [tech].": f"Extensive experience with {', '.join(job_analysis.tech_stack[:2])} and related tech.",
                "How do you handle revisions?": "Unlimited revisions until you're satisfied; quality is my priority.",
            }
            return common_questions
        except Exception as e:
            logger.error(f"Error generating screening answers: {str(e)}")
            # Return basic answers as fallback
            return {
                "What's your availability?": "Available to discuss.",
                "What's your hourly rate or project fee?": "Open to discuss rates.",
                "Can you work in our timezone?": "Flexible with scheduling.",
            }
