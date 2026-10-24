
"""
Job discovery providers.

Supported:
1. DemoProvider: offline sample jobs.
2. GreenhouseProvider: public Greenhouse job-board API.
3. PortalSearchLinks: creates LinkedIn and Naukri search links.

LinkedIn and Naukri links are for user-driven job discovery.
This module does not scrape their pages or bypass login/CAPTCHA.
"""

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .matcher import normalise_location, normalise_phrase
from .models import Job


def clean_description(raw: str) -> str:
    """Turn Greenhouse's entity-escaped HTML content into plain text."""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()



class PortalSearchLinks:
    """Build search links for LinkedIn and Naukri."""

    @staticmethod
    def build(keywords: list[str], locations: list[str]) -> list[dict]:
        links = []

        for keyword in keywords:
            for location in locations:
                query = urllib.parse.quote(keyword)
                loc = urllib.parse.quote(location)

                links.append({
                    "source": "LinkedIn",
                    "keyword": keyword,
                    "location": location,
                    "url": (
                        "https://www.linkedin.com/jobs/search/"
                        f"?keywords={query}&location={loc}"
                    ),
                })

                # Naukri uses keyword/location-specific search URLs.
                slug = re.sub(
                    r"[^a-z0-9]+",
                    "-",
                    f"{keyword}-jobs-in-{location}".lower()
                ).strip("-")

                links.append({
                    "source": "Naukri",
                    "keyword": keyword,
                    "location": location,
                    "url": f"https://www.naukri.com/{slug}",
                })

        return links


class DemoProvider:
    """Offline provider for testing the assistant."""

    def search(
        self,
        keywords: list[str],
        locations: list[str],
        limit: int = 50,
    ) -> list[Job]:

        sample = [
            Job(
                "demo-001",
                "Angular Developer",
                "Acme SaaS",
                "Pune",
                (
                    "Build Angular components, integrate REST APIs, "
                    "and maintain TypeScript applications."
                ),
                "https://example.com/jobs/demo-001",
                source="demo",
            ),
            Job(
                "demo-002",
                "Frontend Engineer",
                "Northstar Labs",
                "Remote",
                (
                    "Develop accessible frontend applications using Angular, "
                    "RxJS, HTML, CSS, and REST services."
                ),
                "https://example.com/jobs/demo-002",
                source="demo",
            ),
            Job(
                "demo-003",
                "Java Full Stack Developer",
                "Sample Systems",
                "Pune",
                (
                    "Build services using Java and Spring Boot and "
                    "frontend features using Angular. SQL and REST APIs required."
                ),
                "https://example.com/jobs/demo-003",
                source="demo",
            ),
        ]

        keyword_terms = [k.lower() for k in keywords]
        location_terms = [l.lower() for l in locations]

        results = []

        for job in sample:
            searchable = f"{job.title} {job.description}".lower()

            # Match on meaningful words rather than requiring the entire
            # configured phrase to appear verbatim (e.g. Frontend Engineer
            # should match the keyword Frontend Developer).
            searchable_words = set(re.findall(r"[a-z0-9+#.]+", searchable))
            keyword_match = any(
                bool(set(re.findall(r"[a-z0-9+#.]+", term)) & searchable_words)
                for term in keyword_terms
            )

            location_match = (
                not location_terms
                or any(term in job.location.lower() for term in location_terms)
            )

            if keyword_match and location_match:
                results.append(job)

        return results[:limit]


class GreenhouseProvider:
    """
    Discover jobs through Greenhouse's public board API.

    Configure board tokens for employers whose public job boards
    you want to search.

    Example board token:
        acme

    Public API:
        https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true

    A keyword matches when its phrase appears in the job title or
    description (after treating "Engineer" and "Developer" as equal).
    A location matches when a configured location appears in the job's
    location name. Both checks are case-insensitive.
    """

    API_BASE = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(
        self,
        board_tokens: list[str],
        timeout: int = 20,
    ):
        self.board_tokens = board_tokens
        self.timeout = timeout

    def _fetch_board(self, token: str) -> list[dict]:
        token = token.strip()

        if not token:
            return []

        # Restrict tokens to a simple board identifier.
        if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
            raise ValueError(f"Invalid Greenhouse board token: {token}")

        url = f"{self.API_BASE}/{token}/jobs?content=true"

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "JobApplicationAssistant/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))

            return data.get("jobs", [])

        except urllib.error.HTTPError as exc:
            print(f"Greenhouse board {token}: HTTP {exc.code}")
            return []

        except urllib.error.URLError as exc:
            print(f"Greenhouse board {token}: {exc.reason}")
            return []

        except TimeoutError:
            print(f"Greenhouse board {token}: request timed out")
            return []

    def search(
        self,
        keywords: list[str],
        locations: list[str],
        limit: int = 50,
    ) -> list[Job]:

        results = []

        keyword_phrases = [
            normalise_phrase(term).strip()
            for term in keywords
            if term.strip()
        ]

        location_terms = [
            normalise_location(term).strip()
            for term in locations
            if term.strip()
        ]

        for token in self.board_tokens:
            jobs = self._fetch_board(token)

            for item in jobs:
                title = item.get("title", "")
                description = clean_description(item.get("content", ""))

                location_data = item.get("location") or {}
                location = location_data.get("name", "Not specified")

                title_phrase = normalise_phrase(title)
                description_phrase = normalise_phrase(description)

                keyword_match = (
                    not keyword_phrases
                    or any(
                        f" {phrase} " in title_phrase
                        or f" {phrase} " in description_phrase
                        for phrase in keyword_phrases
                    )
                )

                location_phrase = normalise_location(location)

                location_match = (
                    not location_terms
                    or any(
                        f" {term} " in location_phrase
                        for term in location_terms
                    )
                )

                if not keyword_match or not location_match:
                    continue

                job_id = item.get("id")

                if not job_id:
                    continue

                results.append(
                    Job(
                        id=f"greenhouse-{token}-{job_id}",
                        title=title,
                        company=token,
                        location=location,
                        description=description,
                        url=item.get("absolute_url", ""),
                        source="greenhouse",
                    )
                )

                if len(results) >= limit:
                    return results

        return results
