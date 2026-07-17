import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / "web" / "public" / "data"


def build(output_dir: Path = OUTPUT_DIR) -> None:
    """Stub: no turnout data collected yet. Writes an empty list so the
    frontend's list+detail contract holds even before real data exists."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "turnout.json").write_text(json.dumps([], indent=2), encoding="utf-8")
