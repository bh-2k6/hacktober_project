import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image

from app.config import UPLOAD_DIR, MAX_IMAGE_SIZE_MB
from app.database import get_db_connection
from app.models import ItemCreate, ItemUpdate, ItemResponse
from app.ai import create_ai_provider
from app.matching.engine import compute_match_score, generate_explanation

router = APIRouter(prefix="/api/items", tags=["items"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _compute_ahash(image_path: str, hash_size: int = 8) -> str:
    try:
        img = Image.open(image_path).convert("L")
        img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = "".join("1" if p > avg else "0" for p in pixels)
        return hex(int(bits, 2))[2:].zfill(hash_size * hash_size // 4)
    except Exception:
        return ""


def _row_to_item(row) -> dict:
    item = dict(row)
    item["characteristics"] = json.loads(item.get("characteristics", "[]"))
    item["distinctive_features"] = json.loads(item.get("distinctive_features", "[]"))
    item["other_attributes"] = json.loads(item.get("other_attributes", "{}"))
    if item.get("embedding"):
        try:
            item["embedding"] = json.loads(item["embedding"])
        except (json.JSONDecodeError, TypeError):
            item["embedding"] = None
    else:
        item["embedding"] = None
    return item


def _find_matches_for_item(item_id: int, item_type: str):
    ai = create_ai_provider()

    with get_db_connection() as conn:
        item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not item:
            return

        item = _row_to_item(item)

        if item_type == "lost":
            opposite_type = "found"
        else:
            opposite_type = "lost"

        candidates = conn.execute(
            "SELECT * FROM items WHERE type = ? AND status = 'active' AND id != ?",
            (opposite_type, item_id),
        ).fetchall()

        for candidate in candidates:
            candidate = _row_to_item(candidate)

            if item_type == "lost":
                score, factors = compute_match_score(item, candidate)
            else:
                score, factors = compute_match_score(candidate, item)

            if score < 0.3:
                continue

            explanation = generate_explanation(factors, item, candidate)

            existing = conn.execute(
                "SELECT id FROM matches WHERE lost_item_id = ? AND found_item_id = ?",
                (
                    item_id if item_type == "lost" else candidate["id"],
                    candidate["id"] if item_type == "lost" else item_id,
                ),
            ).fetchone()

            if not existing:
                if item_type == "lost":
                    lost_id, found_id = item_id, candidate["id"]
                else:
                    lost_id, found_id = candidate["id"], item_id

                conn.execute(
                    """INSERT INTO matches (lost_item_id, found_item_id, score, explanation, factor_scores)
                       VALUES (?, ?, ?, ?, ?)""",
                    (lost_id, found_id, score, explanation, json.dumps(factors)),
                )


@router.post("", response_model=ItemResponse)
async def create_item(
    type: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(...),
    date_time: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    if type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="Type must be 'lost' or 'found'")

    image_path = None
    image_phash = ""

    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid image format. Allowed: {ALLOWED_EXTENSIONS}")

        content = await image.read()
        if len(content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Image too large. Max {MAX_IMAGE_SIZE_MB}MB")

        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = UPLOAD_DIR / filename
        with open(filepath, "wb") as f:
            f.write(content)

        image_path = f"/uploads/{filename}"
        image_phash = _compute_ahash(str(filepath))

    ai = create_ai_provider()
    analysis = await ai.analyze_item(
        str(UPLOAD_DIR / filename) if image and image.filename else "",
        description,
    )

    embedding_text = f"{title} {description} {analysis.object_type} {analysis.color} {analysis.brand}"
    embedding = await ai.generate_embedding(embedding_text)

    with get_db_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO items (type, title, description, category, object_type, color, brand,
               characteristics, distinctive_features, visible_text, other_attributes,
               location, date_time, image_path, image_phash, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                type,
                title,
                description,
                analysis.category,
                analysis.object_type,
                analysis.color,
                analysis.brand,
                json.dumps(analysis.characteristics),
                json.dumps(analysis.distinctive_features),
                analysis.visible_text,
                json.dumps(analysis.other_attributes),
                location,
                date_time,
                image_path,
                image_phash,
                json.dumps(embedding) if embedding else None,
            ),
        )
        item_id = cursor.lastrowid

    _find_matches_for_item(item_id, type)

    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return _row_to_item(row)


@router.get("", response_model=list[ItemResponse])
async def list_items(
    type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if type:
        query += " AND type = ?"
        params.append(type)
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR object_type LIKE ? OR color LIKE ? OR brand LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern] * 5)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_item(row) for row in rows]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        return _row_to_item(row)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, update: ItemUpdate):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")

        fields = []
        params = []

        if update.title is not None:
            fields.append("title = ?")
            params.append(update.title)
        if update.description is not None:
            fields.append("description = ?")
            params.append(update.description)
        if update.location is not None:
            fields.append("location = ?")
            params.append(update.location)
        if update.date_time is not None:
            fields.append("date_time = ?")
            params.append(update.date_time)
        if update.status is not None:
            fields.append("status = ?")
            params.append(update.status)

        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
            params.append(item_id)
            conn.execute(query, params)

        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return _row_to_item(row)


@router.delete("/{item_id}")
async def delete_item(item_id: int):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")

        item = _row_to_item(row)
        if item.get("image_path"):
            image_path = item["image_path"]
            if image_path.startswith("/uploads/"):
                image_path = image_path[len("/uploads/"):]
            filepath = UPLOAD_DIR / image_path
            if filepath.exists():
                filepath.unlink()

        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return {"status": "deleted"}
