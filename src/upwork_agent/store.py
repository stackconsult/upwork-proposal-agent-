import sqlite3
import json
import tempfile
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Use temporary directory for Streamlit Cloud compatibility
if os.path.exists("/tmp"):
    DB_PATH = Path("/tmp/upwork_proposal_agent.db")
else:
    # Fallback to local data directory
    DB_PATH = Path("data/profile.db")

def init_db():
    """Initialize SQLite database with projects table."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                tech_tags TEXT NOT NULL,
                outcomes TEXT NOT NULL,
                vertical TEXT,
                portfolio_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_text_hash TEXT NOT NULL,
                job_analysis_json TEXT,
                proposal_json TEXT,
                model_name TEXT,
                presentation_id TEXT,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Continue without database - app will work but won't persist data

def add_project(
    name: str, 
    description: str, 
    tech_tags: list[str], 
    outcomes: str, 
    vertical: Optional[str] = None,
    portfolio_link: Optional[str] = None
) -> int:
    """Add a project to your Digital Twin."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO projects (name, description, tech_tags, outcomes, vertical, portfolio_link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, description, json.dumps(tech_tags), outcomes, vertical, portfolio_link))
        
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        logger.info(f"Added project {name} with ID {project_id}")
        return project_id
        
    except Exception as e:
        logger.error(f"Failed to add project: {str(e)}")
        # Return mock ID to prevent app crash
        return 0

def get_all_projects() -> list[dict]:
    """Retrieve all projects."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        conn.close()
        
        projects = [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "tech_tags": json.loads(row[3]),
                "outcomes": row[4],
                "vertical": row[5],
                "portfolio_link": row[6],
            }
            for row in rows
        ]
        logger.info(f"Retrieved {len(projects)} projects")
        return projects
        
    except Exception as e:
        logger.error(f"Failed to get projects: {str(e)}")
        # Return empty list to prevent app crash
        return []

def log_run(job_text_hash: str, job_analysis_json: str, proposal_json: str, model_name: str, presentation_id: str, status: str, error_message: Optional[str] = None):
    """Log a proposal generation run."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO runs (job_text_hash, job_analysis_json, proposal_json, model_name, presentation_id, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (job_text_hash, job_analysis_json, proposal_json, model_name, presentation_id, status, error_message))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged run with status: {status}")
        
    except Exception as e:
        logger.error(f"Failed to log run: {str(e)}")
        # Continue without logging - not critical

def cleanup_old_runs(days_old: int = 30):
    """Clean up old run logs to prevent database bloat."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM runs WHERE created_at < datetime('now', '-{} days')
        """.format(days_old))
        
        conn.commit()
        conn.close()
        logger.info(f"Cleaned up runs older than {days_old} days")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old runs: {str(e)}")

def get_database_stats() -> dict:
    """Get database statistics for monitoring."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM runs GROUP BY status")
        run_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "projects": project_count,
            "runs": run_count,
            "run_stats": run_stats,
            "db_path": str(DB_PATH),
            "db_size": DB_PATH.stat().st_size if DB_PATH.exists() else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {"error": str(e)}
