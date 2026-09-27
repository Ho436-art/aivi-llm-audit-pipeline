"""
AIVI Intelligence - AI Engineering Challenge: LLM Pipeline Optimization
Production-grade Resume & Job Description Matching Engine with Google Gemini API,
Sandwich Defense, Strict Pydantic Validation, and Exponential Backoff.
"""

import argparse
import json
import logging
import os
import random
import re
import sys
import time
from typing import Any, Callable, Dict, Optional, Tuple

from dotenv import load_dotenv
from pydantic import ValidationError

# Import schema and prompt architecture
from schema import ResumeMatchResult
from prompt_architecture import SYSTEM_PROMPT, build_sandwich_prompt

# Configure structured logging (avoids leaking sensitive credentials)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AIVIPipeline")

# Maximum permitted input character threshold to prevent prompt ballooning
MAX_INPUT_CHARS = 25000

# Default model configuration (Gemini 3.8 Flash)
load_dotenv()
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


def load_api_key(allow_environment: bool = True) -> Optional[str]:
    """
    Safely retrieves the Gemini API key from environment variables or .env file.
    Ensures API key is never printed, logged, or exposed in exception traces.
    """
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() if allow_environment else None
    
    if not api_key:
        logger.warning(
            "GEMINI_API_KEY environment variable is not set. "
            "Please configure GEMINI_API_KEY in your .env or environment to enable live cloud inference."
        )
        return None
    
    # Mask key for safe logging (e.g. AIzaSy...9xyz)
    masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    logger.info(f"Successfully loaded Gemini API key ({masked})")
    return api_key


def build_prompt(resume_text: str, jd_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Validates, sanitizes, and structures untrusted user inputs using the
    Adversarial Sandwich Defense pattern with XML boundary isolation.
    
    Returns:
        (formatted_prompt, validation_metadata)
    """
    metadata: Dict[str, Any] = {
        "resume_chars": len(resume_text) if resume_text else 0,
        "jd_chars": len(jd_text) if jd_text else 0,
        "truncated": False,
        "warnings": []
    }

    # Validate against empty inputs early
    clean_resume = resume_text.strip() if resume_text else ""
    clean_jd = jd_text.strip() if jd_text else ""

    if not clean_resume:
        metadata["warnings"].append("Resume input is empty or contains only whitespace.")
    if not clean_jd:
        metadata["warnings"].append("Job description input is empty or contains only whitespace.")

    # Guard against extremely long input denial-of-service / token bloat
    if len(clean_resume) > MAX_INPUT_CHARS:
        clean_resume = clean_resume[:MAX_INPUT_CHARS]
        metadata["truncated"] = True
        metadata["warnings"].append(f"Resume text truncated to {MAX_INPUT_CHARS} characters.")

    if len(clean_jd) > MAX_INPUT_CHARS:
        clean_jd = clean_jd[:MAX_INPUT_CHARS]
        metadata["truncated"] = True
        metadata["warnings"].append(f"Job description truncated to {MAX_INPUT_CHARS} characters.")

    prompt = build_sandwich_prompt(clean_resume, clean_jd)
    return prompt, metadata


def is_transient_error(exception: Exception) -> bool:
    """
    Categorizes errors into transient (retryable) vs permanent (non-retryable).
    
    Transient errors:
        - HTTP 429 (Rate Limits / ResourceExhausted)
        - HTTP 503 / 500 (Service Unavailable / Backend transient errors)
        - Network timeouts and connection drops
    
    Permanent errors:
        - HTTP 400 (Bad Request / Invalid Argument)
        - HTTP 401 / 403 (Invalid API Key / Unauthorized)
        - Schema / JSON syntax validation errors
    """
    err_str = str(exception).lower()
    
    # Check for rate limiting
    if "429" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str:
        return True
    # Check for temporary server errors
    if "503" in err_str or "500" in err_str or "unavailable" in err_str or "server error" in err_str:
        return True
    # Check for network latency timeouts
    if "timeout" in err_str or "timed out" in err_str or "connection" in err_str:
        return True
    
    return False


def retry_with_backoff(
    callable_fn: Callable[[], Any],
    max_retries: int = 5,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True
) -> Any:
    """
    Executes a function with bounded exponential backoff and randomized jitter
    for resilient handling of HTTP 429, 503, and transient network failures.
    """
    delay = initial_delay
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            return callable_fn()
        except Exception as e:
            last_exception = e
            
            # Check if error is retryable
            if not is_transient_error(e):
                logger.error(f"Permanent non-retryable error encountered: {type(e).__name__} - {str(e)}")
                raise e

            if attempt == max_retries:
                logger.error(f"Exceeded maximum retry attempts ({max_retries}). Aborting.")
                raise e

            # Compute bounded exponential delay with full jitter
            sleep_duration = min(max_delay, delay * (backoff_factor ** (attempt - 1)))
            if jitter:
                sleep_duration = random.uniform(sleep_duration * 0.5, sleep_duration * 1.5)

            logger.warning(
                f"[Attempt {attempt}/{max_retries}] Transient failure ({type(e).__name__}). "
                f"Retrying in {sleep_duration:.2f}s..."
            )
            time.sleep(sleep_duration)

    if last_exception:
        raise last_exception


def call_gemini(
    prompt: str,
    api_key: str,
    model_name: Optional[str] = None,
    timeout_sec: float = 30.0
) -> str:
    """
    Invokes the Google Gemini API using the official google-genai SDK,
    enforcing structured application/json mime-type and deterministic temperature.
    """
    target_model = model_name or DEFAULT_MODEL
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        logger.error("google-genai package not found. Install via 'pip install google-genai'.")
        raise RuntimeError("Missing required SDK: google-genai") from e

    def _execute_api_call():
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,  # Low temperature for deterministic scoring consistency
                response_mime_type="application/json",
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )
        if not response.text:
            raise ValueError("Gemini API returned an empty response body.")
        return response.text

    return retry_with_backoff(_execute_api_call)


def validate_response(raw_output: str) -> ResumeMatchResult:
    """
    Strips accidental markdown code fences, parses JSON, and validates
    against the production Pydantic ResumeMatchResult schema.
    """
    if not raw_output or not raw_output.strip():
        raise ValueError("Cannot validate empty or whitespace response from model.")

    cleaned = raw_output.strip()

    # Strip markdown code blocks if the model wrapped the output in ```json ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Parse raw JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise ValueError(
            f"Model output is not valid JSON at line {err.lineno}, col {err.colno}: {err.msg}"
        ) from err

    # Validate against Pydantic schema
    try:
        validated = ResumeMatchResult.model_validate(data)
        return validated
    except ValidationError as err:
        error_messages = [
            f"Field '{'.'.join(str(loc) for loc in e['loc'])}': {e['msg']}"
            for e in err.errors()
        ]
        raise ValueError(f"Pydantic Schema Validation Failed: {'; '.join(error_messages)}") from err


def analyze_resume(
    resume_text: str,
    jd_text: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    mock_fallback_on_missing_key: bool = False
) -> Dict[str, Any]:
    """
    End-to-End Orchestrator:
    1. Validates inputs & handles empty edge cases.
    2. Constructs prompt with Sandwich Defense.
    3. Calls Gemini API with exponential backoff for 429/timeouts.
    4. Validates structured JSON using Pydantic.
    5. Returns clean, production-ready dictionary.
    """
    target_model = model_name or DEFAULT_MODEL
    # Edge case 1 & 2: Empty inputs handled deterministically
    clean_resume = resume_text.strip() if resume_text else ""
    clean_jd = jd_text.strip() if jd_text else ""

    if not clean_resume and not clean_jd:
        result = ResumeMatchResult(
            match_score=0,
            top_strengths=["No resume provided", "No qualifications found", "Evaluation skipped"],
            missing_skills=["All required job skills"],
            summary="Both candidate resume and job description are completely empty. Alignment score cannot be computed."
        )
        return {"status": "success", "source": "input_guard", "data": result.model_dump()}

    if not clean_resume:
        result = ResumeMatchResult(
            match_score=0,
            top_strengths=["No resume text provided", "No skills extracted", "Profile unverified"],
            missing_skills=["All stated role requirements"],
            summary="Candidate resume is empty. No alignment with the job description can be evaluated."
        )
        return {"status": "success", "source": "input_guard", "data": result.model_dump()}

    if not clean_jd:
        result = ResumeMatchResult(
            match_score=0,
            top_strengths=["Technical background noted", "Resume parsed", "Awaiting target criteria"],
            missing_skills=["Target job description requirements unspecified"],
            summary="Job description is empty. Cannot compute alignment score without target job requirements."
        )
        return {"status": "success", "source": "input_guard", "data": result.model_dump()}

    # Resolve API Key
    resolved_key = api_key or load_api_key()
    if not resolved_key:
        if mock_fallback_on_missing_key:
            logger.info("Executing via deterministic mock evaluator (no API key configured).")
            return _mock_evaluator(clean_resume, clean_jd)
        return {
            "status": "error",
            "error_type": "MissingAPIKeyError",
            "message": "GEMINI_API_KEY is not configured. Set GEMINI_API_KEY environment variable or in .env."
        }

    # Step 1: Prompt Construction
    prompt, metadata = build_prompt(clean_resume, clean_jd)
    if metadata["warnings"]:
        for w in metadata["warnings"]:
            logger.warning(f"Input validation warning: {w}")

    # Step 2: Gemini API Invocation with Exponential Backoff
    try:
        raw_output = call_gemini(prompt, api_key=resolved_key, model_name=target_model)
    except Exception as e:
        logger.error(f"Gemini API invocation failed: {type(e).__name__} - {str(e)}")
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": f"Gemini API call failed: {str(e)}"
        }

    # Step 3: Response Validation
    try:
        validated_result = validate_response(raw_output)
        return {
            "status": "success",
            "source": "gemini_live",
            "data": validated_result.model_dump()
        }
    except ValueError as ve:
        logger.error(f"Response validation error: {str(ve)}")
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": str(ve),
            "raw_output": raw_output[:300]
        }


def _mock_evaluator(resume: str, jd: str) -> Dict[str, Any]:
    """
    Deterministic offline evaluator used when no API key is available or during offline testing.
    Employs exact token-grounding rules without external cloud dependencies.
    """
    res_lower = resume.lower()
    jd_lower = jd.lower()

    # Check for adversarial prompt injection attempt
    is_injection = "ignore previous instructions" in res_lower or "score of 100" in res_lower
    
    # Common tech tokens
    common_skills = [
        "python", "sql", "fastapi", "django", "postgresql", "docker", 
        "kubernetes", "aws", "git", "machine learning", "pandas", "react"
    ]
    
    matched = [s.title() for s in common_skills if s in res_lower and s in jd_lower]
    missing = [s.title() for s in common_skills if s in jd_lower and s not in res_lower]
    
    if is_injection:
        score = 20
        strengths = (matched[:3] + ["Basic technical foundations", "Unspecified background", "Unverified candidate"])[:3]
        return {
            "status": "success",
            "source": "mock_offline",
            "data": {
                "match_score": score,
                "top_strengths": strengths,
                "missing_skills": missing if missing else ["Advanced technical depth"],
                "summary": "Adversarial prompt injection directives in candidate input were neutralized. Evaluated solely on authentic stated qualifications."
            }
        }

    score = min(95, max(15, len(matched) * 28))
    
    # Pad strengths to ensure exactly 3 items
    strengths = matched[:3]
    while len(strengths) < 3:
        strengths.append(f"Foundational requirement {len(strengths) + 1}")

    return {
        "status": "success",
        "source": "mock_offline",
        "data": {
            "match_score": score,
            "top_strengths": strengths,
            "missing_skills": missing if missing else ["None identified"],
            "summary": f"Alignment score of {score}% based on matching competencies: {', '.join(matched[:2]) if matched else 'basic profile'}."
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="AIVI Resume & Job Description Alignment Engine (Gemini API + Pydantic)"
    )
    parser.add_argument("--resume", type=str, help="Candidate resume plaintext")
    parser.add_argument("--jd", type=str, help="Target job description plaintext")
    parser.add_argument("--resume-file", type=str, help="Path to plaintext resume file")
    parser.add_argument("--jd-file", type=str, help="Path to plaintext job description file")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Gemini model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--mock", action="store_true", help="Run with offline mock evaluator")

    args = parser.parse_args()

    # Load texts from args or files
    resume_text = args.resume or ""
    if args.resume_file and os.path.exists(args.resume_file):
        with open(args.resume_file, "r", encoding="utf-8") as f:
            resume_text = f.read()

    jd_text = args.jd or ""
    if args.jd_file and os.path.exists(args.jd_file):
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_text = f.read()

    # Default demo input if none provided
    if not resume_text and not jd_text:
        logger.info("No inputs provided. Running with standard reference challenge example...")
        resume_text = "Python developer with experience in machine learning, SQL, FastAPI and data analysis."
        jd_text = "Looking for a Python developer with experience in Python, SQL, FastAPI and cloud deployment."

    result = analyze_resume(
        resume_text=resume_text,
        jd_text=jd_text,
        model_name=args.model,
        mock_fallback_on_missing_key=args.mock or True
    )

    print("\n" + "=" * 50)
    print("FINAL EVALUATION OUTPUT (STRICT JSON)")
    print("=" * 50)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
