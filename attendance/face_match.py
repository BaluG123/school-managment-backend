"""Improved face-photo similarity for on-server matching."""

from __future__ import annotations

from typing import BinaryIO, List, Optional, Tuple

from PIL import Image, ImageOps


def _load_normalized(image_file: BinaryIO, size: Tuple[int, int] = (120, 120)) -> List[float]:
    image_file.seek(0)
    img = Image.open(image_file)
    img = ImageOps.exif_transpose(img)
    img = img.convert('RGB')

    # Center-crop to square (faces are usually centered in capture/registration)
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Slight inset crop to focus more on face area
    inset = int(side * 0.08)
    if inset > 0 and side - 2 * inset > 40:
        img = img.crop((inset, inset, side - inset, side - inset))

    img = img.convert('L').resize(size, Image.Resampling.LANCZOS)
    img = ImageOps.equalize(img)
    pixels = list(img.getdata())
    mean = sum(pixels) / len(pixels)
    # Zero-mean normalized vector
    return [p - mean for p in pixels]


def face_similarity(capture_file: BinaryIO, reference_path: str) -> float:
    """
    Return similarity score 0–100 using cosine similarity on
    normalized center-cropped grayscale vectors.
    """
    try:
        capture = _load_normalized(capture_file)
        with open(reference_path, 'rb') as ref_fp:
            reference = _load_normalized(ref_fp)
    except Exception:
        return 0.0

    if len(capture) != len(reference) or not capture:
        return 0.0

    # Cosine similarity
    dot = sum(a * b for a, b in zip(capture, reference))
    norm_a = sum(a * a for a in capture) ** 0.5
    norm_b = sum(b * b for b in reference) ** 0.5
    if norm_a < 1e-6 or norm_b < 1e-6:
        return 0.0

    cosine = max(-1.0, min(1.0, dot / (norm_a * norm_b)))
    # Map cosine [-1,1] → [0,100], emphasize positive matches
    score = ((cosine + 1.0) / 2.0) * 100.0
    return round(score, 2)


def find_best_student_match(
    capture_file: BinaryIO,
    students,
    threshold: float = 52.0,
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
