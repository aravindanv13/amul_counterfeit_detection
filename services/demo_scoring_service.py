"""Explicit review-demo scoring using exact matches to local fixture images.

Browsers send file contents and a basename, not the user's source directory.
Folder labels are demo inputs, never evidence of product authenticity.
"""

import hashlib
from pathlib import Path

from utils.file_utils import allowed_file


def image_digest(path):
    digest = hashlib.sha256()
    with open(path, "rb") as image:
        for chunk in iter(lambda: image.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def match_demo_source(image_path, dataset_root):
    """Match bytes, even after renaming. Unmatched images use the 'other' bucket.

    Re-read the small fixture collection so additions/moves work without restart.
    If identical bytes occur in both folders, the fake label takes precedence.
    """
    root = Path(dataset_root)
    if not (root / "fake").is_dir() or not (root / "original").is_dir():
        raise FileNotFoundError("Demo dataset requires both fake and original folders.")
    uploaded_digest = image_digest(image_path)
    for label in ("fake", "original"):
        for candidate in sorted((root / label).rglob("*")):
            if candidate.is_file() and allowed_file(candidate.name):
                if image_digest(candidate) == uploaded_digest:
                    return label
    return "other"


def apply_demo_score(analysis, source):
    """Keep computed evidence intact while explicitly labelling the demo override."""
    if source not in {"fake", "original", "other"}:
        return analysis
    raw_score = float(analysis["risk_score"])
    score = max(26.0, raw_score) if source == "fake" else min(15.0, raw_score)
    score = round(max(0.0, min(100.0, score)), 1)
    tier = "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"
    return {
        **analysis,
        "risk_score": score,
        "risk_level": tier,
        "risk_tier": tier,
        "scoring_mode": "folder_demo",
        "demo_source": source,
        "computed_analysis": dict(analysis),
        "recommendation": "Reference-image demo score.",
    }
