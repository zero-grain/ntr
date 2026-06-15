import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_JSON = DATA_DIR / "report-data.json"
OUTPUT_JS = DATA_DIR / "report-data.js"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from generate_manual_score_report import fetch_score_rows, fetch_satisfaction_pairs
from manual_score_import_gui import normalize_title


def build_payload() -> dict:
    rows = fetch_score_rows()
    satisfaction_pairs = fetch_satisfaction_pairs()

    grouped: dict[str, list[dict]] = defaultdict(list)
    all_people = []
    seen_people = set()

    for row in rows:
        employee_name = (row.get("employee_name") or "").strip()
        unit_name = (row.get("unit_name") or "").strip()
        email = (row.get("email") or "").strip().lower()
        file_title = (row.get("file_title") or "").strip()
        score_text = (row.get("score_text") or "").strip()
        has_satisfaction = (normalize_title(file_title), email) in satisfaction_pairs if email else False

        item = {
            "employee_name": employee_name,
            "unit_name": unit_name,
            "email": email,
            "score_text": score_text,
            "has_satisfaction": has_satisfaction,
        }
        grouped[file_title].append(item)

        if employee_name and employee_name not in seen_people:
            seen_people.add(employee_name)
            all_people.append(
                {
                    "employee_name": employee_name,
                    "unit_name": unit_name,
                }
            )

    title_sections = []
    for file_title in sorted(grouped):
        items = sorted(
            grouped[file_title],
            key=lambda row: (
                row["employee_name"],
                row["unit_name"],
                row["score_text"],
                row["email"],
            ),
        )
        title_sections.append(
            {
                "file_title": file_title,
                "unique_people_count": len({row["employee_name"] for row in items if row["employee_name"]}),
                "row_count": len(items),
                "items": items,
            }
        )

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": {
            "row_count": len(rows),
            "title_count": len(title_sections),
            "people_count": len(all_people),
        },
        "all_people": all_people,
        "title_sections": title_sections,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    OUTPUT_JSON.write_text(json_text, encoding="utf-8")
    OUTPUT_JS.write_text(
        "window.STATIC_REPORT_DATA = " + json_text + ";\n",
        encoding="utf-8",
    )
    print(f"Static report data saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
