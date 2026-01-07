import sqlite3
import json
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/profile.db")

def init_db():
    """Initialize SQLite database with projects table."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
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

def add_project(
    name: str, 
    description: str, 
    tech_tags: list[str], 
    outcomes: str, 
    vertical: Optional[str] = None,
    portfolio_link: Optional[str] = None
) -> int:
    """Add a project to your Digital Twin."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO projects (name, description, tech_tags, outcomes, vertical, portfolio_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, json.dumps(tech_tags), outcomes, vertical, portfolio_link))
    
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id

def get_all_projects() -> list[dict]:
    """Retrieve all projects."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()
    conn.close()
    
    return [
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

def log_run(job_text_hash: str, job_analysis_json: str, proposal_json: str, model_name: str, presentation_id: str, status: str, error_message: Optional[str] = None):
    """Log a proposal generation run."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO runs (job_text_hash, job_analysis_json, proposal_json, model_name, presentation_id, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_text_hash, job_analysis_json, proposal_json, model_name, presentation_id, status, error_message))
    
    conn.commit()
    conn.close()
