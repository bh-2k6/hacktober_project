import json
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.database import get_db_connection
from app.models import MatchResponse, MatchUpdate, ContactRequestCreate, ContactRequestResponse

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _row_to_match(row) -> dict:
    match = dict(row)
    match["factor_scores"] = json.loads(match.get("factor_scores", "{}"))
    return match


def _get_match_with_items(match_id: int) -> Optional[dict]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
        if not row:
            return None

        match = _row_to_match(row)

        lost = conn.execute("SELECT * FROM items WHERE id = ?", (match["lost_item_id"],)).fetchone()
        found = conn.execute("SELECT * FROM items WHERE id = ?", (match["found_item_id"],)).fetchone()

        if lost:
            lost = dict(lost)
            lost["characteristics"] = json.loads(lost.get("characteristics", "[]"))
            lost["distinctive_features"] = json.loads(lost.get("distinctive_features", "[]"))
            lost["other_attributes"] = json.loads(lost.get("other_attributes", "{}"))
            match["lost_item"] = lost

        if found:
            found = dict(found)
            found["characteristics"] = json.loads(found.get("characteristics", "[]"))
            found["distinctive_features"] = json.loads(found.get("distinctive_features", "[]"))
            found["other_attributes"] = json.loads(found.get("other_attributes", "{}"))
            match["found_item"] = found

        return match


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    status: Optional[str] = None,
    min_score: float = 0.0,
    limit: int = 50,
    offset: int = 0,
):
    query = "SELECT * FROM matches WHERE score >= ?"
    params = [min_score]

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY score DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        matches = []
        for row in rows:
            match = _get_match_with_items(row["id"])
            if match:
                matches.append(match)
        return matches


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int):
    match = _get_match_with_items(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(match_id: int, update: MatchUpdate):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")

        conn.execute("UPDATE matches SET status = ? WHERE id = ?", (update.status, match_id))

        if update.status == "confirmed":
            conn.execute(
                "UPDATE items SET status = 'reunited', updated_at = CURRENT_TIMESTAMP WHERE id IN (?, ?)",
                (row["lost_item_id"], row["found_item_id"]),
            )

    return _get_match_with_items(match_id)


@router.post("/contact", response_model=ContactRequestResponse)
async def create_contact_request(request: ContactRequestCreate):
    with get_db_connection() as conn:
        match = conn.execute("SELECT * FROM matches WHERE id = ?", (request.match_id,)).fetchone()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        cursor = conn.execute(
            """INSERT INTO contact_requests (match_id, requester_type, message, status)
               VALUES (?, ?, ?, 'pending')""",
            (request.match_id, request.requester_type, request.message),
        )

        row = conn.execute("SELECT * FROM contact_requests WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


@router.get("/contact/{match_id}", response_model=list[ContactRequestResponse])
async def get_contact_requests(match_id: int):
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM contact_requests WHERE match_id = ? ORDER BY created_at DESC",
            (match_id,),
        ).fetchall()
        return [dict(row) for row in rows]
