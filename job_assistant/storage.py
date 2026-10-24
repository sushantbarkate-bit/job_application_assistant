import sqlite3
from pathlib import Path
from datetime import datetime

class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS applications (
            job_id TEXT PRIMARY KEY, title TEXT, company TEXT, location TEXT, url TEXT,
            score INTEGER, status TEXT, created_at TEXT, notes TEXT)""")
        self.db.commit()

    def add(self, job, score: int, status="matched", notes=""):
        self.db.execute("INSERT OR IGNORE INTO applications VALUES (?,?,?,?,?,?,?,?,?)",
            (job.id, job.title, job.company, job.location, job.url, score, status,
             datetime.now().isoformat(timespec="seconds"), notes))
        self.db.commit()

    def update_status(self, job_id: str, status: str, notes=""):
        self.db.execute("UPDATE applications SET status=?, notes=? WHERE job_id=?", (status, notes, job_id))
        self.db.commit()

    def rows(self, since=None):
        query = "SELECT job_id,title,company,location,url,score,status,created_at,notes FROM applications"
        params = ()
        if since:
            query += " WHERE created_at >= ?"
            params = (since,)
        query += " ORDER BY created_at DESC"
        return self.db.execute(query, params).fetchall()
