import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, get_db_connection
from app.matching.engine import compute_match_score, generate_explanation

DEMO_ITEMS = [
    {
        "type": "lost",
        "title": "iPhone 13 with blue case",
        "description": "Lost my iPhone 13 with a blue silicone case. Has a small scratch on the back. Lock screen shows a photo of my dog.",
        "location": "AB2 Library",
        "date_time": (datetime.now() - timedelta(hours=2)).isoformat(),
        "category": "electronics",
        "object_type": "smartphone",
        "color": "blue",
        "brand": "apple",
        "characteristics": ["blue case", "scratch on back"],
        "distinctive_features": ["dog photo lock screen", "small scratch"],
        "visible_text": "",
    },
    {
        "type": "found",
        "title": "iPhone with blue case",
        "description": "Found an iPhone with a blue case on a library desk. Has a scratch on the back.",
        "location": "AB2 Library",
        "date_time": (datetime.now() - timedelta(hours=1)).isoformat(),
        "category": "electronics",
        "object_type": "smartphone",
        "color": "blue",
        "brand": "apple",
        "characteristics": ["blue case", "scratch on back"],
        "distinctive_features": ["scratch on back"],
        "visible_text": "",
    },
    {
        "type": "lost",
        "title": "Black North Face jacket",
        "description": "Lost my black North Face puffer jacket. Has a small tear on the left sleeve and a keychain in the pocket.",
        "location": "Student Center",
        "date_time": (datetime.now() - timedelta(hours=5)).isoformat(),
        "category": "clothing",
        "object_type": "jacket",
        "color": "black",
        "brand": "north face",
        "characteristics": ["puffer style", "tear on sleeve"],
        "distinctive_features": ["keychain in pocket", "small tear on left sleeve"],
        "visible_text": "The North Face",
    },
    {
        "type": "found",
        "title": "Black puffer jacket",
        "description": "Found a black puffer jacket in the student center cafeteria. There is a keychain in one of the pockets.",
        "location": "Student Center",
        "date_time": (datetime.now() - timedelta(hours=3)).isoformat(),
        "category": "clothing",
        "object_type": "jacket",
        "color": "black",
        "brand": "north face",
        "characteristics": ["puffer style"],
        "distinctive_features": ["keychain in pocket"],
        "visible_text": "The North Face",
    },
    {
        "type": "lost",
        "title": "MacBook Pro 14 inch",
        "description": "Lost my MacBook Pro 14 inch with a space gray color. Has several stickers on the lid including a GitHub sticker and a Linux sticker.",
        "location": "Engineering Building",
        "date_time": (datetime.now() - timedelta(hours=8)).isoformat(),
        "category": "electronics",
        "object_type": "laptop",
        "color": "gray",
        "brand": "apple",
        "characteristics": ["stickers on lid", "space gray"],
        "distinctive_features": ["GitHub sticker", "Linux sticker", "space gray color"],
        "visible_text": "",
    },
    {
        "type": "found",
        "title": "Laptop with stickers",
        "description": "Found a laptop with stickers on the lid in the engineering building. Space gray color.",
        "location": "Engineering Building",
        "date_time": (datetime.now() - timedelta(hours=6)).isoformat(),
        "category": "electronics",
        "object_type": "laptop",
        "color": "gray",
        "brand": "apple",
        "characteristics": ["stickers on lid", "space gray"],
        "distinctive_features": ["GitHub sticker", "Linux sticker"],
        "visible_text": "",
    },
    {
        "type": "lost",
        "title": "AirPods Pro with case",
        "description": "Lost my AirPods Pro with a white case. The case has a small crack on the front.",
        "location": "Gym",
        "date_time": (datetime.now() - timedelta(hours=12)).isoformat(),
        "category": "electronics",
        "object_type": "earbuds",
        "color": "white",
        "brand": "apple",
        "characteristics": ["white case", "crack on case"],
        "distinctive_features": ["crack on front of case"],
        "visible_text": "",
    },
    {
        "type": "found",
        "title": "White earbuds case",
        "description": "Found a white earbuds case at the gym. It has a small crack on it.",
        "location": "Gym",
        "date_time": (datetime.now() - timedelta(hours=10)).isoformat(),
        "category": "electronics",
        "object_type": "earbuds",
        "color": "white",
        "brand": "apple",
        "characteristics": ["white case", "crack on case"],
        "distinctive_features": ["crack on case"],
        "visible_text": "",
    },
    {
        "type": "lost",
        "title": "Brown leather wallet",
        "description": "Lost my brown leather wallet. Contains my student ID and some cash. Has my initials embossed on the front.",
        "location": "Cafeteria",
        "date_time": (datetime.now() - timedelta(hours=24)).isoformat(),
        "category": "accessories",
        "object_type": "wallet",
        "color": "brown",
        "brand": "",
        "characteristics": ["leather", "initials embossed"],
        "distinctive_features": ["initials embossed on front", "brown leather"],
        "visible_text": "JD",
    },
    {
        "type": "found",
        "title": "Brown wallet",
        "description": "Found a brown leather wallet in the cafeteria. Has initials on the front.",
        "location": "Cafeteria",
        "date_time": (datetime.now() - timedelta(hours=20)).isoformat(),
        "category": "accessories",
        "object_type": "wallet",
        "color": "brown",
        "brand": "",
        "characteristics": ["leather", "initials on front"],
        "distinctive_features": ["initials on front"],
        "visible_text": "JD",
    },
    {
        "type": "lost",
        "title": "Blue backpack",
        "description": "Lost my blue Jansport backpack. Has several pins on the front pocket and a water bottle in the side pocket.",
        "location": "Library",
        "date_time": (datetime.now() - timedelta(hours=4)).isoformat(),
        "category": "accessories",
        "object_type": "backpack",
        "color": "blue",
        "brand": "jansport",
        "characteristics": ["pins on front", "water bottle in side pocket"],
        "distinctive_features": ["several pins on front pocket"],
        "visible_text": "Jansport",
    },
    {
        "type": "found",
        "title": "Blue backpack with pins",
        "description": "Found a blue backpack with pins on it in the library.",
        "location": "Library",
        "date_time": (datetime.now() - timedelta(hours=2)).isoformat(),
        "category": "accessories",
        "object_type": "backpack",
        "color": "blue",
        "brand": "jansport",
        "characteristics": ["pins on front"],
        "distinctive_features": ["several pins on front pocket"],
        "visible_text": "Jansport",
    },
    {
        "type": "lost",
        "title": "Calculus textbook",
        "description": "Lost my Calculus textbook. It has my name written inside the cover and several highlighted sections.",
        "location": "Math Building",
        "date_time": (datetime.now() - timedelta(hours=48)).isoformat(),
        "category": "books",
        "object_type": "textbook",
        "color": "blue",
        "brand": "",
        "characteristics": ["highlighted sections", "name inside cover"],
        "distinctive_features": ["name written inside", "highlighted pages"],
        "visible_text": "Calculus - Stewart",
    },
    {
        "type": "found",
        "title": "Calculus book",
        "description": "Found a calculus textbook in the math building. It has highlighted sections and a name inside.",
        "location": "Math Building",
        "date_time": (datetime.now() - timedelta(hours=36)).isoformat(),
        "category": "books",
        "object_type": "textbook",
        "color": "blue",
        "brand": "",
        "characteristics": ["highlighted sections"],
        "distinctive_features": ["name inside cover", "highlighted pages"],
        "visible_text": "Calculus - Stewart",
    },
    {
        "type": "lost",
        "title": "Red water bottle",
        "description": "Lost my red Hydro Flask water bottle. Has several stickers on it and a dent on the bottom.",
        "location": "Gym",
        "date_time": (datetime.now() - timedelta(hours=6)).isoformat(),
        "category": "sports",
        "object_type": "water bottle",
        "color": "red",
        "brand": "hydro flask",
        "characteristics": ["stickers", "dent on bottom"],
        "distinctive_features": ["several stickers", "dent on bottom"],
        "visible_text": "Hydro Flask",
    },
    {
        "type": "found",
        "title": "Red water bottle with stickers",
        "description": "Found a red water bottle with stickers at the gym.",
        "location": "Gym",
        "date_time": (datetime.now() - timedelta(hours=4)).isoformat(),
        "category": "sports",
        "object_type": "water bottle",
        "color": "red",
        "brand": "hydro flask",
        "characteristics": ["stickers"],
        "distinctive_features": ["several stickers"],
        "visible_text": "Hydro Flask",
    },
    {
        "type": "lost",
        "title": "Black umbrella",
        "description": "Lost my black umbrella. It has a wooden handle and a small tear in the fabric.",
        "location": "Student Center",
        "date_time": (datetime.now() - timedelta(hours=16)).isoformat(),
        "category": "accessories",
        "object_type": "umbrella",
        "color": "black",
        "brand": "",
        "characteristics": ["wooden handle", "tear in fabric"],
        "distinctive_features": ["wooden handle", "small tear"],
        "visible_text": "",
    },
    {
        "type": "found",
        "title": "Black umbrella",
        "description": "Found a black umbrella with a wooden handle at the student center.",
        "location": "Student Center",
        "date_time": (datetime.now() - timedelta(hours=14)).isoformat(),
        "category": "accessories",
        "object_type": "umbrella",
        "color": "black",
        "brand": "",
        "characteristics": ["wooden handle"],
        "distinctive_features": ["wooden handle"],
        "visible_text": "",
    },
    {
        "type": "lost",
        "title": "Sony headphones",
        "description": "Lost my Sony WH-1000XM4 headphones. Black color with a small scratch on the right ear cup.",
        "location": "Library",
        "date_time": (datetime.now() - timedelta(hours=10)).isoformat(),
        "category": "electronics",
        "object_type": "headphones",
        "color": "black",
        "brand": "sony",
        "characteristics": ["over-ear", "scratch on ear cup"],
        "distinctive_features": ["scratch on right ear cup"],
        "visible_text": "SONY",
    },
    {
        "type": "found",
        "title": "Black Sony headphones",
        "description": "Found black Sony headphones at the library. They have a scratch on one ear cup.",
        "location": "Library",
        "date_time": (datetime.now() - timedelta(hours=8)).isoformat(),
        "category": "electronics",
        "object_type": "headphones",
        "color": "black",
        "brand": "sony",
        "characteristics": ["over-ear", "scratch on ear cup"],
        "distinctive_features": ["scratch on ear cup"],
        "visible_text": "SONY",
    },
]


def seed():
    init_db()

    with get_db_connection() as conn:
        conn.execute("DELETE FROM matches")
        conn.execute("DELETE FROM items")

        item_ids = {}
        for item_data in DEMO_ITEMS:
            cursor = conn.execute(
                """INSERT INTO items (type, title, description, category, object_type, color, brand,
                   characteristics, distinctive_features, visible_text, other_attributes,
                   location, date_time, image_path, image_phash, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item_data["type"],
                    item_data["title"],
                    item_data["description"],
                    item_data["category"],
                    item_data["object_type"],
                    item_data["color"],
                    item_data["brand"],
                    json.dumps(item_data["characteristics"]),
                    json.dumps(item_data["distinctive_features"]),
                    item_data["visible_text"],
                    json.dumps({}),
                    item_data["location"],
                    item_data["date_time"],
                    None,
                    "",
                    "active",
                ),
            )
            item_ids[item_data["title"]] = cursor.lastrowid

        lost_items = [dict(item_data, id=item_ids[item_data["title"]])
                      for item_data in DEMO_ITEMS if item_data["type"] == "lost"]
        found_items = [dict(item_data, id=item_ids[item_data["title"]])
                       for item_data in DEMO_ITEMS if item_data["type"] == "found"]

        for lost in lost_items:
            for found in found_items:
                score, factors = compute_match_score(lost, found)
                if score >= 0.3:
                    explanation = generate_explanation(factors, lost, found)
                    conn.execute(
                        """INSERT INTO matches (lost_item_id, found_item_id, score, explanation, factor_scores, status)
                           VALUES (?, ?, ?, ?, ?, 'pending')""",
                        (lost["id"], found["id"], score, explanation, json.dumps(factors)),
                    )

    print(f"Seeded {len(DEMO_ITEMS)} items")
    with get_db_connection() as conn:
        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        print(f"Generated {match_count} matches")


if __name__ == "__main__":
    seed()
