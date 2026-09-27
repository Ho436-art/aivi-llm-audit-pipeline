"""
Deliverable 2 - Production Pydantic Schema for Resume & Job Description Matching
Compatible with Pydantic v2.
"""

from typing import List
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo

class ResumeMatchResult(BaseModel):
    """
    Production-grade validation schema for Resume/Job Description AI Evaluation.
    Enforces strict typing, range limits, exact list lengths, and rejects unknown fields.
    """
    model_config = ConfigDict(
        extra="forbid",               # Reject any extraneous fields
        str_strip_whitespace=True,     # Sanitize and strip outer whitespace
        validate_assignment=True
    )

    match_score: int = Field(
        ...,
        description="Institutional alignment score as an integer from 0 to 100.",
        ge=0,
        le=100
    )

    top_strengths: List[str] = Field(
        ...,
        description="Exactly 3 key technical strengths or competencies possessed by candidate that match the JD."
    )

    missing_skills: List[str] = Field(
        ...,
        description="Relevant skills or requirements from JD that are absent or unverified in candidate resume."
    )

    summary: str = Field(
        ...,
        description="Concise evaluation summary of approximately 2 lines explaining score and core alignment.",
        min_length=10,
        max_length=500
    )

    @field_validator("top_strengths")
    @classmethod
    def validate_top_strengths_length(cls, v: List[str]) -> List[str]:
        if len(v) != 3:
            raise ValueError(f"top_strengths must contain exactly 3 items, received {len(v)}")
        for idx, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"top_strengths[{idx}] must be a non-empty string")
        return [item.strip() for item in v]

    @field_validator("missing_skills")
    @classmethod
    def validate_missing_skills(cls, v: List[str]) -> List[str]:
        cleaned = []
        for idx, item in enumerate(v):
            if not isinstance(item, str):
                raise ValueError(f"missing_skills[{idx}] must be a string")
            s = item.strip()
            if s:  # Filter out empty strings if any
                cleaned.append(s)
        return cleaned

    @field_validator("summary")
    @classmethod
    def validate_summary_lines(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("summary cannot be empty or whitespace only")
        return cleaned


if __name__ == "__main__":
    # Test valid case
    valid_data = {
        "match_score": 85,
        "top_strengths": ["Python", "SQL", "FastAPI"],
        "missing_skills": ["Cloud deployment", "Docker"],
        "summary": "Strong alignment with core backend and Python requirements. Candidate lacks explicitly verified cloud deployment experience."
    }
    result = ResumeMatchResult.model_validate(valid_data)
    print("Valid instance verified successfully:")
    print(result.model_dump_json(indent=2))

    # Test rejection of extra field
    try:
        ResumeMatchResult.model_validate({**valid_data, "extra_hack": True})
        print("ERROR: Extra field was NOT rejected!")
    except Exception as e:
        print("\nSuccessfully rejected extra field:", type(e).__name__)

    # Test rejection of wrong top_strengths count
    try:
        ResumeMatchResult.model_validate({**valid_data, "top_strengths": ["Python", "SQL"]})
        print("ERROR: Wrong top_strengths count was NOT rejected!")
    except Exception as e:
        print("Successfully rejected invalid top_strengths count:", type(e).__name__)

    # Test rejection of out-of-range score
    try:
        ResumeMatchResult.model_validate({**valid_data, "match_score": 105})
        print("ERROR: Out of range score was NOT rejected!")
    except Exception as e:
        print("Successfully rejected out-of-range score:", type(e).__name__)
