"""Photo management service.

Handles upload, thumbnail generation (Pillow), EXIF parsing,
and file storage on local filesystem.
"""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from PIL import ExifTags, Image

from verdanta.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
THUMBNAIL_MAX_SIZE = 400


def _extract_exif_taken_at(img: Image.Image) -> datetime | None:
    """Extract DateTimeOriginal from EXIF data if available."""
    try:
        exif_data = img.getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, "")
            if tag_name == "DateTimeOriginal":
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").replace(tzinfo=UTC)
    except Exception:
        logger.debug("Could not extract EXIF taken_at", exc_info=True)
    return None


async def save_photo(
    file: UploadFile,
    garden_id: int,
    planting_id: int | None,
) -> dict:
    """Save uploaded photo and generate thumbnail.

    Returns dict with file_path, thumbnail_path, taken_at.
    """
    filename = file.filename or "photo"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    stem = f"{timestamp}_{unique_id}"
    photo_name = f"{stem}{ext}"
    thumb_name = f"{stem}_thumb{ext}"

    planting_dir = str(planting_id) if planting_id else "_garden"
    photo_dir = Path(settings.photo_dir) / str(garden_id) / planting_dir
    photo_dir.mkdir(parents=True, exist_ok=True)

    photo_path = photo_dir / photo_name
    thumb_path = photo_dir / thumb_name

    content = await file.read()
    photo_path.write_bytes(content)

    taken_at: datetime | None = None
    try:
        img = Image.open(photo_path)
        taken_at = _extract_exif_taken_at(img)

        # Generate thumbnail
        img_copy = img.copy()
        img_copy.thumbnail((THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE), Image.Resampling.LANCZOS)
        img_copy.save(thumb_path)
        img.close()
        img_copy.close()
    except Exception:
        logger.warning("Could not generate thumbnail for %s", photo_path, exc_info=True)
        thumb_path = None

    if taken_at is None:
        taken_at = datetime.now(UTC)

    return {
        "file_path": str(photo_path),
        "thumbnail_path": str(thumb_path) if thumb_path else None,
        "taken_at": taken_at,
    }


def delete_photo_files(file_path: str, thumbnail_path: str | None) -> None:
    """Remove photo and thumbnail files from disk."""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
    except Exception:
        logger.warning("Failed to delete photo file: %s", file_path, exc_info=True)

    if thumbnail_path:
        try:
            t = Path(thumbnail_path)
            if t.exists():
                t.unlink()
        except Exception:
            logger.warning("Failed to delete thumbnail: %s", thumbnail_path, exc_info=True)
