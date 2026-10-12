from pathlib import Path
from uuid import uuid4
from PIL import Image, UnidentifiedImageError

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
VIDEO_SIGNATURES = {"video/mp4": b"ftyp", "video/webm": b"\x1aE\xdf\xa3"}
DOC_TYPES = {"image/jpeg", "image/png", "application/pdf"}


def sniff_media(file_storage, allowed):
    stream = file_storage.stream
    header = stream.read(32)
    stream.seek(0)
    if header.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        mime = "image/webp"
    elif header[4:8] == b"ftyp":
        mime = "video/mp4"
    elif header.startswith(b"\x1aE\xdf\xa3"):
        mime = "video/webm"
    elif header.startswith(b"%PDF-"):
        mime = "application/pdf"
    else:
        mime = "application/octet-stream"
    if mime not in allowed:
        raise ValueError("Formato file non supportato o contenuto non valido.")
    return mime


def validate_report_media(file_storage):
    mime = sniff_media(file_storage, IMAGE_TYPES | set(VIDEO_SIGNATURES))
    if mime in IMAGE_TYPES:
        try:
            image = Image.open(file_storage.stream)
            image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("Immagine danneggiata o non valida.") from error
        finally:
            file_storage.stream.seek(0)
    return mime


def validate_image_or_document(file_storage):
    mime = sniff_media(file_storage, DOC_TYPES)
    if mime in IMAGE_TYPES:
        try:
            Image.open(file_storage.stream).verify()
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("Immagine non valida.") from error
        finally:
            file_storage.stream.seek(0)
    return mime


def save_private_upload(file_storage, root, area, validator):
    mime = validator(file_storage)
    area_path = Path(root).resolve() / area
    area_path.mkdir(parents=True, exist_ok=True)
    safe_ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "video/mp4": ".mp4", "video/webm": ".webm", "application/pdf": ".pdf"}[mime]
    generated = f"{uuid4().hex}{safe_ext}"
    target = area_path / generated
    file_storage.save(target)
    return str(target)


def exif_coordinates(path):
    try:
        image = Image.open(path)
        exif = image.getexif()
        gps = exif.get_ifd(34853)
        lat = _dms(gps.get(2))
        lon = _dms(gps.get(4))
        if gps.get(1) == "S": lat *= -1
        if gps.get(3) == "W": lon *= -1
        return lat, lon
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError):
        return None, None


def _dms(values):
    if not values or len(values) != 3:
        raise ValueError("Coordinate EXIF mancanti")
    return float(values[0]) + float(values[1]) / 60 + float(values[2]) / 3600
