import json
from pathlib import Path

from builders import county_boards

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_county_reads_frontmatter_and_renders_body():
    county = county_boards.parse_county(FIXTURES / "fulton.md")

    assert county["slug"] == "fulton"
    assert county["name"] == "Fulton"
    assert county["members"] == 5
    assert county["selection_method"] == "appointed"
    assert county["meeting_schedule"] == "First Tuesday monthly"
    assert "<p>" in county["body_html"]
    assert "Fulton County Board of Elections meets" in county["body_html"]


def test_build_writes_list_and_detail_json(tmp_path):
    output_dir = tmp_path / "data"

    county_boards.build(content_dir=FIXTURES, output_dir=output_dir)

    counties = json.loads((output_dir / "counties.json").read_text())
    assert counties == [
        {"slug": "fulton", "name": "Fulton", "members": 5, "selection_method": "appointed"}
    ]

    detail = json.loads((output_dir / "counties" / "fulton.json").read_text())
    assert detail["slug"] == "fulton"
    assert detail["meeting_schedule"] == "First Tuesday monthly"
    assert "<p>" in detail["body_html"]
