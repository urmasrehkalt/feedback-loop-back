import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


def main() -> None:
    output_path = ROOT / "openapi" / "openapi.json"
    output_path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
