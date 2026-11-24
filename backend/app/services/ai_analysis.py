from pathlib import Path


def analyze_image(filename: str | None = None) -> dict:
    """Return a transparent baseline until a model package and weights are configured."""
    suffix = Path(filename or "").suffix.lower()
    category = "mixed" if suffix in {".jpg", ".jpeg", ".png", ".webp"} else "other"
    return {
        "predicted_category": category,
        "confidence": 0.25,
        "severity": "medium",
        "analysis_method": "labeled_baseline_fallback",
        "model_available": False,
    }
