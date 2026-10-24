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
        self._migrate()
        self.db.commit()

    def _migrate(self):
        # Databases created by earlier versions lack these columns.
        existing = {row[1] for row in self.db.execute("PRAGMA table_info(applications)")}
        for column in ("description", "updated_at"):
            if column not in existing:
                self.db.execute(f"ALTER TABLE applications ADD COLUMN {column} TEXT")
        self.db.execute("UPDATE applications SET updated_at = created_at WHERE updated_at IS NULL")

    def add(self, job, score: int, status="matched", notes=""):
        now = datetime.now().isoformat(timespec="seconds")
        # Re-discovery refreshes the score and status of jobs that have not been acted on
        # (matched / low_match). Approved jobs keep their status and notes.
        # A missing description is filled in.
        self.db.execute(
            "INSERT INTO applications "
            "(job_id, title, company, location, url, score, status, created_at, notes, description, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(job_id) DO UPDATE SET "
            "description = CASE WHEN applications.description IS NULL OR applications.description = '' "
            "  THEN excluded.description ELSE applications.description END, "
            "score = CASE WHEN applications.status IN ('matched','low_match') "
            "  THEN excluded.score ELSE applications.score END, "
            "notes = CASE WHEN applications.status IN ('matched','low_match') "
            "  THEN excluded.notes ELSE applications.notes END, "
            "updated_at = CASE WHEN applications.status IN ('matched','low_match') "
            "  AND applications.status <> excluded.status THEN excluded.updated_at ELSE applications.updated_at END, "
            "status = CASE WHEN applications.status IN ('matched','low_match') "
            "  THEN excluded.status ELSE applications.status END",
            (job.id, job.title, job.company, job.location, job.url, score, status,
             now, notes, job.description, now))
        self.db.commit()

    def update_status(self, job_id: str, status: str, notes=""):
        now = datetime.now().isoformat(timespec="seconds")
        self.db.execute(
            "UPDATE applications SET status=?, notes=?, updated_at=? WHERE job_id=?",
            (status, notes, now, job_id))
        self.db.commit()

    def job(self, job_id: str):
        """Return the stored job row as a dict, or None if it is not stored."""
        cursor = self.db.execute(
            "SELECT job_id, title, company, location, url, description, score, status "
            "FROM applications WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(zip([column[0] for column in cursor.description], row))

    def rows(self, since=None):
        """Rows created or status-changed on or after `since` (an ISO date), newest first."""
        query = ("SELECT job_id,title,company,location,url,score,status,created_at,notes,updated_at "
                 "FROM applications")
        params = ()
        if since:
            query += " WHERE created_at >= ? OR updated_at >= ?"
            params = (since, since)
        query += " ORDER BY created_at DESC"
        return self.db.execute(query, params).fetchall()
