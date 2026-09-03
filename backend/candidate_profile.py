from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_PATH = ROOT / "data" / "candidate_profile.json"


class CandidateProfileError(RuntimeError):
    """Raised when the local candidate profile is missing or invalid."""


def profile_path() -> Path:
    configured_path = os.getenv("AUTOAPPLY_PROFILE_FILE", "").strip()
    return Path(configured_path).expanduser() if configured_path else DEFAULT_PROFILE_PATH


@lru_cache(maxsize=1)
def load_candidate_profile() -> dict[str, Any]:
    path = profile_path()
    try:
        profile = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise CandidateProfileError(
            f"Candidate profile not found at {path}. Copy data/candidate.example.json "
            "to data/candidate_profile.json and replace the example values."
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateProfileError(f"Could not read candidate profile at {path}: {exc}") from exc

    required_sections = {"identity", "professional_facts", "resume"}
    missing = sorted(required_sections.difference(profile))
    if missing:
        raise CandidateProfileError(f"Candidate profile is missing section(s): {', '.join(missing)}")
    return profile
