import json
from pathlib import Path

import frontmatter
import markdown
import nh3

CONTENT_DIR = Path(__file__).parent.parent / "content" / "county-boards"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "web" / "public" / "data"


def parse_county(md_path: Path) -> dict:
    post = frontmatter.load(md_path)
    return {
        "slug": md_path.stem,
        "name": post.get("county", md_path.stem),
        "members": post.get("members"),
        "selection_method": post.get("selection_method"),
        "meeting_schedule": post.get("meeting_schedule"),
        "body_html": nh3.clean(markdown.markdown(post.content)),
    }


def build(content_dir: Path = CONTENT_DIR, output_dir: Path = OUTPUT_DIR) -> None:
    detail_dir = output_dir / "counties"
    detail_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for md_path in sorted(content_dir.glob("*.md")):
        county = parse_county(md_path)
        summaries.append(
            {
                "slug": county["slug"],
                "name": county["name"],
                "members": county["members"],
                "selection_method": county["selection_method"],
            }
        )
        (detail_dir / f"{county['slug']}.json").write_text(
            json.dumps(county, indent=2), encoding="utf-8"
        )

    (output_dir / "counties.json").write_text(
        json.dumps(summaries, indent=2), encoding="utf-8"
    )
