from __future__ import annotations

import json
import re

from backend.ai_provider import generate_json, model_name
from backend.browser_service import read_linkedin_profile
from backend.candidate_profile import load_candidate_profile
from backend.logging_service import log_ai_interaction


def evaluate_linkedin() -> dict:
    profile = read_linkedin_profile()
    candidate = load_candidate_profile()
    identity = candidate["identity"]
    professional_facts = candidate["professional_facts"]
    prompt = f"""You are a LinkedIn SEO expert and international technical recruiter.
Assess {identity['full_name']}'s profile for discovery by recruiters hiring candidates aligned with the confirmed professional facts below. Review the headline, About, experience, skills, keywords, measurable outcomes, seniority, languages, Featured section, and consistency. Never invent facts or metrics.

Return valid JSON only, using this exact schema. Keep every text field concise so the complete JSON fits within 700 tokens:
{{
  "score": 0,
  "summary_pt": "brief diagnosis in Portuguese",
  "summary_en": "brief diagnosis in English",
  "headline_pt": "optimized Portuguese headline",
  "headline_en": "optimized English headline",
  "about_pt": "concise Portuguese About section",
  "about_en": "concise English About section",
  "recommendations": [{{"priority":"high|medium|low","section":"section","current_issue":"issue","change_pt":"change in Portuguese","change_en":"change in English","keywords":["keyword"]}}],
  "missing_keywords": ["keyword"],
  "recruiter_searches": ["likely recruiter query"]
}}
Provide at most five recommendations, eight missing keywords, and five recruiter searches.

CONFIRMED PROFESSIONAL FACTS:
{json.dumps(professional_facts, ensure_ascii=False, separators=(',', ':'))}

VISIBLE LINKEDIN PROFILE TEXT:
{profile['profile_text'][:2600]}
"""
    response_text = generate_json(prompt)
    log_ai_interaction(
        "evaluate_linkedin_profile",
        model_name(),
        prompt,
        response_text,
        {"profile_url": profile.get("url"), "profile_name": profile.get("name")},
    )
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text.strip(), flags=re.IGNORECASE)
    evaluation = json.loads(text)
    evaluation["score"] = max(0, min(100, int(evaluation.get("score", 0))))
    return {"profile": {key: profile[key] for key in ("connected", "url", "name", "headline")}, "evaluation": evaluation}
