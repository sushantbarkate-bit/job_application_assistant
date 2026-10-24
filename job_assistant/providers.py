"""Job discovery providers.

DemoProvider is safe/offline. Add providers only through official APIs, feeds, or
portals whose terms permit your intended use. Avoid scraping/login bypasses.
"""
from .models import Job

class DemoProvider:
    def search(self, keywords: list[str], locations: list[str], limit: int = 50) -> list[Job]:
        sample = [
            Job("demo-001", "Angular Developer", "Acme SaaS", "Pune", "Build Angular components, integrate REST APIs, and maintain TypeScript UI. 3+ years Angular preferred.", "https://example.com/jobs/demo-001"),
            Job("demo-002", "Frontend Engineer", "Northstar Labs", "Remote", "Develop accessible frontend applications using Angular, RxJS, HTML, CSS, and REST services.", "https://example.com/jobs/demo-002"),
            Job("demo-003", "Java Full Stack Developer", "Sample Systems", "Pune", "Build services using Java and Spring Boot and frontend features using Angular. SQL and REST APIs required.", "https://example.com/jobs/demo-003"),
            Job("demo-004", "Senior React Developer", "Fictional Co", "Remote", "Develop React applications and Node services. React expertise required.", "https://example.com/jobs/demo-004"),
        ]
        terms = [k.lower() for k in keywords]
        locs = [l.lower() for l in locations]
        matched = [j for j in sample if any(t in (j.title + " " + j.description).lower() for t in terms)
                  and (not locs or any(l in j.location.lower() for l in locs))]
        return matched[:limit]
