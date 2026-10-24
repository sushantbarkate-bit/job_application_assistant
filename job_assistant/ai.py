import os
from dotenv import load_dotenv
load_dotenv()

class AIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _client(self):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env or use --no-ai.")
        from openai import OpenAI
        return OpenAI(api_key=self.api_key)

    def tailor_resume_bullets(self, resume_text: str, job_description: str) -> str:
        prompt = f"""Tailor the resume text to the job description. Keep all facts truthful; do not add skills,
roles, metrics, employers, dates, or credentials absent from the source resume. Return concise revised
resume text and mark any suggested additions as [USER VERIFY].\n\nRESUME:\n{resume_text}\n\nJOB:\n{job_description}"""
        response = self._client().chat.completions.create(
            model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.2)
        return response.choices[0].message.content or ""

    def answer_application_question(self, question: str, facts: dict) -> str:
        prompt = f"Answer only using these user-provided facts. If not answerable, return exactly NEEDS_USER_INPUT.\nFacts: {facts}\nQuestion: {question}"
        response = self._client().chat.completions.create(
            model=self.model, messages=[{"role":"user","content":prompt}], temperature=0)
        return response.choices[0].message.content or "NEEDS_USER_INPUT"
