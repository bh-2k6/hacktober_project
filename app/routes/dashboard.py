from fastapi import APIRouter

from app.database import get_db_connection
from app.models import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    with get_db_connection() as conn:
        total_lost = conn.execute(
            "SELECT COUNT(*) FROM items WHERE type = 'lost' AND status = 'active'"
        ).fetchone()[0]

        total_found = conn.execute(
            "SELECT COUNT(*) FROM items WHERE type = 'found' AND status = 'active'"
        ).fetchone()[0]

        total_matches = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE status = 'pending'"
        ).fetchone()[0]

        confirmed_matches = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE status = 'confirmed'"
        ).fetchone()[0]

        reunited_items = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'reunited'"
        ).fetchone()[0]

        pending_matches = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE status = 'pending'"
        ).fetchone()[0]

        return DashboardStats(
            total_lost=total_lost,
            total_found=total_found,
            total_matches=total_matches,
            confirmed_matches=confirmed_matches,
            reunited_items=reunited_items,
            pending_matches=pending_matches,
        )
