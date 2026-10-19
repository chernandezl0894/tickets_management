"""Export the generated OpenAPI document to ``docs/openapi.json``."""

import json
from pathlib import Path

from tickets_management.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "openapi.json"


def main() -> None:
    """Write the current OpenAPI schema with stable formatting."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI schema written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
