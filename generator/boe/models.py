"""Pydantic models for the Georgia board-of-elections database.

The models mirror the SQLite schema in ``db.py`` and are the single source of
truth for what a county, board, or member looks like at the Python boundary.
The repository layer converts rows ↔ models; the CLI never touches raw SQL.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class County(BaseModel):
    """One of Georgia's 159 counties."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    slug: str
    fips: str | None = None
    seat: str | None = None
    population: int | None = None


class Board(BaseModel):
    """A county board of elections — one per county (1:1)."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    county_id: int
    name: str
    organization: str | None = Field(
        default=None,
        description="How the board is organized (charter, local act, etc.).",
    )
    meeting_schedule: str | None = None
    meeting_location: str | None = None
    selection_method: Literal["appointed", "elected", "mixed"] | None = None
    selection_description: str | None = Field(
        default=None,
        description="How and by whom members are chosen, in plain text.",
    )
    authority: str | None = Field(
        default=None,
        description="The law / charter / local act that creates the board.",
    )
    term_length: str | None = None
    notes: str | None = None


class Member(BaseModel):
    """A person who sits on a county board of elections."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    board_id: int
    name: str
    role: str | None = None
    party: str | None = None
    is_elected: bool = False
    appointed_by: str | None = Field(
        default=None,
        description="Office or person that appointed the member.",
    )
    appointment_method: str | None = Field(
        default=None,
        description="party nomination, mayoral appointment, election, …",
    )
    appointment_authority: str | None = Field(
        default=None,
        description="Grand jury, county commission, mayor, …",
    )
    term_start: str | None = None
    term_end: str | None = None
    notes: str | None = None


class SearchResult(BaseModel):
    """One full-text-search hit."""

    entity_type: Literal["county", "board", "member"]
    entity_id: int
    title: str
    snippet: str


# --- update payloads: every field optional ----------------------------------

class CountyUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    fips: str | None = None
    seat: str | None = None
    population: int | None = None


class BoardUpdate(BaseModel):
    name: str | None = None
    organization: str | None = None
    meeting_schedule: str | None = None
    meeting_location: str | None = None
    selection_method: Literal["appointed", "elected", "mixed"] | None = None
    selection_description: str | None = None
    authority: str | None = None
    term_length: str | None = None
    notes: str | None = None


class MemberUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    party: str | None = None
    is_elected: bool | None = None
    appointed_by: str | None = None
    appointment_method: str | None = None
    appointment_authority: str | None = None
    term_start: str | None = None
    term_end: str | None = None
    notes: str | None = None