"""FastAPI read-only app (TDD §6): query the thesis graph, proposals, briefs.

There are NO trading/order endpoints — execution is permanently out of scope
(GOLDEN RULE 1 / ADR-0002). Intended for local single-user use.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from ..agents.market import MarketRegime
from ..config.settings import Settings, get_settings
from ..domain.calibration import Scorecard
from ..domain.proposal import Brief, Proposal
from ..domain.thesis import Layer, Status, Thesis
from ..services.advisory import (
    calibration_scorecard,
    current_regime,
    daily_brief,
    latest_proposal,
    monthly_brief,
    weekly_brief,
)
from ..storage.repository import Repository
from ..storage.sqlite_repo import SqliteRepository


class ThesisGraph(BaseModel):
    node: Thesis
    parents: list[Thesis]
    children: list[Thesis]


def get_repo() -> Iterator[Repository]:
    yield SqliteRepository.from_url(get_settings().ti_db_url)


RepoDep = Annotated[Repository, Depends(get_repo)]


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()

    def require_token(x_api_token: Annotated[str | None, Header()] = None) -> None:
        # Local single-user auth: enforced only when TI_API_TOKEN is configured.
        if config.ti_api_token and x_api_token != config.ti_api_token:
            raise HTTPException(status_code=401, detail="invalid or missing API token")

    app = FastAPI(
        title="Turtle Insight (local, read-only)",
        version="0.1.0",
        dependencies=[Depends(require_token)],
    )

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

    @app.get("/briefs/daily")
    def briefs_daily(repo: RepoDep) -> Brief:
        return daily_brief(repo)

    @app.get("/briefs/weekly")
    def briefs_weekly(repo: RepoDep) -> Brief:
        return weekly_brief(repo)

    @app.get("/briefs/monthly")
    def briefs_monthly(repo: RepoDep) -> Brief:
        return monthly_brief(repo)

    @app.get("/calibration")
    def calibration(repo: RepoDep) -> Scorecard:
        return calibration_scorecard(repo)

    @app.get("/market/regime")
    def market_regime(repo: RepoDep) -> MarketRegime:
        return current_regime(repo)

    return app


app = create_app()
