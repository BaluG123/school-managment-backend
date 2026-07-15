"""Simple face-photo similarity for on-server matching."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO, Optional, Tuple

from PIL import Image, ImageOps


def _normalize(image_file: BinaryIO, size: Tuple[int, int] = (128, 128)):
    image_file.seek(0)
    img = Image.open(image_file)
    img = ImageOps.exif_transpose(img)
    img = img.convert('L').resize(size, Image.Resampling.LANCZOS)
    # Equalize contrast so lighting differences hurt less
    img = ImageOps.equalize(img)
    return list(img.getdata())


def face_similarity(capture_file: BinaryIO, reference_path: str) -> float:
    """
    Return similarity score 0–100 between capture upload and reference file.
    Uses mean absolute pixel difference on normalized grayscale face crops.
    """
    try:
        capture = _normalize(capture_file)
        with open(reference_path, 'rb') as ref_fp:
            reference = _normalize(ref_fp)
    except Exception:
        return 0.0

    if len(capture) != len(reference) or not capture:
        return 0.0

    total = sum(abs(a - b) for a, b in zip(capture, reference))
    mae = total / len(capture)  # 0–255
    score = max(0.0, 100.0 - (mae / 255.0) * 100.0)
    return round(score, 2)


def find_best_student_match(
    capture_file: BinaryIO,
    students,
    threshold: float = 62.0,
) -> Optional[Tuple[object, float]]:
    """
    Compare capture against each student's face_photo.
    Returns (student, confidence) or None.
    """
    best = None
    best_score = -1.0

    for student in students:
        if not student.face_photo:
            continue
        try:
            path = student.face_photo.path
        except Exception:
            continue

        capture_file.seek(0)
        score = face_similarity(capture_file, path)
        if score > best_score:
            best_score = score
            best = student

    if best is None or best_score < threshold:
        return None
    return best, best_score
