import logging
from typing import List, Dict, Any
from pcrs.backend.ai_recommender.models import (
    Application,
    ApplicationSystemRequirement,
    RequirementExtractionLog,
)
from .benchmark_matcher import match_to_benchmark
from .parsers.regex_parser import extract_regex_requirements
from .parsers.spacy_parser import extract_spacy_requirements

# from .parsers.ml_parser import extract_ml_requirements  # For future

logger = logging.getLogger(__name__)


def clean_cpu_gpu_name(name: str) -> str:
    return name.strip().title() if name else ""


def extract_requirements_pipeline(text: str) -> Dict[str, Any]:
    """Try multiple extractors in order of precision/fallbacks."""
    extractors = [
        ("regex", extract_regex_requirements),
        ("spacy", extract_spacy_requirements),
        # ("ml", extract_ml_requirements),  # To be added later
    ]

    for method, extractor in extractors:
        try:
            extracted = extractor(text)
            if extracted["requirements"]:  # At least one requirement found
                extracted["method"] = method
                return extracted
        except Exception as e:
            logger.warning(f"{method.upper()} extraction failed: {e}")

    logger.error("All extractors failed.")
    return {
        "requirements": [],
        "confidence": 0.0,
        "method": "none",
        "error": "All methods failed",
    }


def save_extracted_requirements(
    app_name: str, source_text: str, extracted_data: Dict[str, Any]
):
    try:
        app = Application.objects.get(name__iexact=app_name)
    except Application.DoesNotExist:
        raise ValueError(f"Application '{app_name}' not found.")

    for req in extracted_data.get("requirements", []):
        cpu = clean_cpu_gpu_name(req["cpu"]) or ""
        gpu = clean_cpu_gpu_name(req["gpu"]) or ""
        ram = req["ram"] or 0
        storage = req["storage"] or 0
        notes = req.get("notes")
        req_type = req["type"]
        confidence = extracted_data.get("confidence", 0.0)
        method = extracted_data.get("method", "unknown")

        # Benchmark matching
        cpu, gpu, cpu_score, gpu_score = match_to_benchmark(cpu, gpu)

        # Save extraction log
        RequirementExtractionLog.objects.create(
            application=app,
            source_text=source_text,
            extracted_json=req,
            confidence=confidence,
            method=method,
        )

        # Save system requirements
        ApplicationSystemRequirement.objects.update_or_create(
            application=app,
            type=req_type,
            defaults={
                "cpu": cpu,
                "gpu": gpu,
                "ram": ram,
                "storage": storage,
                "notes": notes,
                "cpu_score": cpu_score,
                "gpu_score": gpu_score,
            },
        )
