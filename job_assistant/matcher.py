import re

from .models import Job


# Employers often use "Engineer" where a profile says "Developer".
TITLE_SYNONYMS = {"engineer": "developer"}

# Common spelling variants of place names.
LOCATION_ALIASES = {"bangalore": "bengaluru"}


def normalise_phrase(text: str) -> str:
    """Lower-case, strip punctuation, and apply synonyms so phrases compare as words."""
    words = re.findall(r"[a-z0-9+#]+", text.lower())
    return " " + " ".join(TITLE_SYNONYMS.get(w, w) for w in words) + " "


def normalise_location(text: str) -> str:
    words = re.findall(r"[a-z0-9+#]+", text.lower())
    return " " + " ".join(LOCATION_ALIASES.get(w, w) for w in words) + " "


def _has_term(text: str, term: str) -> bool:
    """Match whole terms so 'java' does not match 'javascript'."""
    return re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", text) is not None


def score_job(job: Job, profile: dict) -> dict:
    skills = {s.lower() for s in profile.get("skills", [])}
    text = f"{job.title} {job.description}".lower()
    found = sorted(s for s in skills if _has_term(text, s))
    # Transparent baseline score: title overlap + skill overlap + location fit.
    target_titles = [t.lower() for t in profile.get("target_titles", [])]
    job_title = normalise_phrase(job.title)
    title_hit = any(f" {normalise_phrase(t).strip()} " in job_title for t in target_titles)
    locs = [normalise_location(x).strip() for x in profile.get("target_locations", [])]
    job_location = normalise_location(job.location)
    location_hit = not locs or any(f" {x} " in job_location for x in locs)
    skill_score = round(60 * len(found) / max(1, len(skills)))
    score = min(100, skill_score + (25 if title_hit else 0) + (15 if location_hit else 0))
    return {"score": score, "matched_skills": found, "missing_skills": sorted(skills - set(found)),
            "title_match": title_hit, "location_match": location_hit}
