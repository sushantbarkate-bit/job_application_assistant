from collections import Counter
from .models import Job


def score_job(job: Job, profile: dict) -> dict:
    skills = {s.lower() for s in profile.get("skills", [])}
    text = f"{job.title} {job.description}".lower()
    found = sorted(s for s in skills if s in text)
    # Transparent baseline score: title overlap + skill overlap + location fit.
    target_titles = [t.lower() for t in profile.get("target_titles", [])]
    title_hit = any(t in job.title.lower() for t in target_titles)
    locs = [x.lower() for x in profile.get("target_locations", [])]
    location_hit = not locs or any(x in job.location.lower() for x in locs)
    skill_score = round(60 * len(found) / max(1, len(skills)))
    score = min(100, skill_score + (25 if title_hit else 0) + (15 if location_hit else 0))
    return {"score": score, "matched_skills": found, "missing_skills": sorted(skills - set(found)),
            "title_match": title_hit, "location_match": location_hit}
