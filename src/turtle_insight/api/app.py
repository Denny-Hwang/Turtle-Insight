"""FastAPI read-only app (TDD §6): query the thesis graph, proposals, briefs.

There are NO trading/order endpoints — execution is permanently out of scope
(GOLDEN RULE 1 / ADR-0002). Intended for local single-user use.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from ..config.settings import get_settings
from ..domain.proposal import Brief, Proposal
from ..domain.thesis import Layer, Status, Thesis
from ..services.advisory import latest_proposal, weekly_brief
from ..storage.repository import ThesisRepository
from ..storage.sqlite_repo import SqliteRepository


class ThesisGraph(BaseModel):
    node: Thesis
    parents: list[Thesis]
    children: list[Thesis]


def get_repo() -> Iterator[ThesisRepository]:
    yield SqliteRepository.from_url(get_settings().ti_db_url)


RepoDep = Annotated[ThesisRepository, Depends(get_repo)]


def create_app() -> FastAPI:
    app = FastAPI(title="Turtle Insight (local, read-only)", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/theses")
    def list_theses(
        repo: RepoDep,
        status: Status | None = None,
        layer: Layer | None = None,
        ticker: str | None = None,
    ) -> list[Thesis]:
        return repo.list_theses(status=status, layer=layer.value if layer else None, ticker=ticker)

    @app.get("/theses/{thesis_id}")
    def get_thesis(thesis_id: str, repo: RepoDep) -> Thesis:
        thesis = repo.get_thesis(thesis_id)
        if thesis is None:
            raise HTTPException(status_code=404, detail="thesis not found")
        return thesis

    @app.get("/theses/{thesis_id}/graph")
    def thesis_graph(thesis_id: str, repo: RepoDep) -> ThesisGraph:
        node = repo.get_thesis(thesis_id)
        if node is None:
            raise HTTPException(status_code=404, detail="thesis not found")
        parents: list[Thesis] = []
        for pid in node.parents:
            parent = repo.get_thesis(pid)
            if parent is not None:
                parents.append(parent)
        children: list[Thesis] = []
        for cid in node.children:
            child = repo.get_thesis(cid)
            if child is not None:
                children.append(child)
        return ThesisGraph(node=node, parents=parents, children=children)

    @app.get("/proposals/latest")
    def proposals_latest(repo: RepoDep) -> Proposal:
        return latest_proposal(repo)

    @app.get("/briefs/weekly")
    def briefs_weekly(repo: RepoDep) -> Brief:
        return weekly_brief(repo)

    return app


app = create_app()
