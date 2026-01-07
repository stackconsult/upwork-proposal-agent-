from upwork_agent.schemas import JobAnalysis
from upwork_agent.store import get_all_projects

def score_projects(job_analysis: JobAnalysis) -> list[tuple[dict, float]]:
    """
    Score your projects against job requirements.
    Returns: [(project_dict, score), ...] sorted by score descending.
    """
    projects = get_all_projects()
    
    scored = []
    
    for project in projects:
        score = 0.0
        
        # Tech stack overlap
        project_techs = set(tag.lower() for tag in project.get("tech_tags", []))
        job_techs = set(tech.lower() for tech in job_analysis.tech_stack)
        tech_overlap = len(project_techs & job_techs)
        score += tech_overlap * 10
        
        # Vertical match
        if project.get("vertical") and project["vertical"].lower() in " ".join(job_analysis.pain_points).lower():
            score += 15
        
        # Keyword match in description + outcomes
        description_text = (project.get("description", "") + " " + project.get("outcomes", "")).lower()
        for keyword in job_analysis.pain_points:
            if keyword.lower() in description_text:
                score += 5
        
        scored.append((project, score))
    
    # Sort by score descending, return top 3
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:3]

def format_projects_for_gemini(scored_projects: list[tuple[dict, float]]) -> list[str]:
    """Format top projects as readable strings for Gemini context."""
    formatted = []
    
    for project, score in scored_projects:
        text = f"""
Project: {project['name']}
Description: {project['description']}
Tech Used: {', '.join(project.get('tech_tags', []))}
Outcomes: {project['outcomes']}
"""
        if project.get('portfolio_link'):
            text += f"Link: {project['portfolio_link']}\n"
        formatted.append(text)
    
    return formatted
