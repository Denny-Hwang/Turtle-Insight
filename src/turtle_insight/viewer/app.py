"""Streamlit viewer (run with ``make run-viewer``).

Explore the thesis graph (layer-coloured, parent+child edges), thesis detail,
the market-regime badge, the calibration scorecard, the latest proposal, and
the briefings. Read-only. Rendering logic lives in ``viewer/render.py`` (tested);
this file is a thin shell. Absolute imports because Streamlit runs it as a script.
"""

from __future__ import annotations

import streamlit as st

from turtle_insight.config.settings import get_settings
from turtle_insight.services.advisory import (
    calibration_scorecard,
    current_regime,
    daily_brief,
    latest_proposal,
    monthly_brief,
    weekly_brief,
)
from turtle_insight.storage.sqlite_repo import SqliteRepository
from turtle_insight.viewer.render import (
    build_graph_dot,
    proposal_rows,
    regime_badge,
    scorecard_metrics,
)


def _repo() -> SqliteRepository:
    return SqliteRepository.from_url(get_settings().ti_db_url)


def main() -> None:
    st.set_page_config(page_title="Turtle Insight", layout="wide")
    st.title("🐢 Turtle Insight — Thesis Graph (local, read-only)")

    repo = _repo()
    theses = repo.list_theses()
    st.caption(regime_badge(current_regime(repo)))

    if not theses:
        st.info("No theses in the DB yet. Run `make analyze` to populate it.")
        return

    statuses = sorted({t.status.value for t in theses})
    chosen = st.sidebar.multiselect("Status filter", statuses, default=statuses)
    visible = [t for t in theses if t.status.value in chosen]

    st.subheader("Thesis graph")
    st.graphviz_chart(build_graph_dot(visible))

    ids = [t.id for t in visible]
    if ids:
        detail = repo.get_thesis(st.selectbox("Inspect thesis", ids))
        if detail is not None:
            st.subheader(f"{detail.id} — {detail.title}")
            st.write(detail.claim)
            st.metric("Conviction", f"{detail.conviction}/100")
            st.write("**Falsifiers**")
            for falsifier in detail.falsifiers:
                st.write(f"- {falsifier}")
            st.write("**Evidence (links + summaries)**")
            for ev in detail.evidence:
                st.write(f"- [{ev.source}]({ev.url}) — {ev.summary} ({ev.date.isoformat()})")

    st.header("Calibration scorecard")
    columns = st.columns(3)
    metrics = scorecard_metrics(calibration_scorecard(repo))
    for column, (label, value) in zip(columns, metrics, strict=False):
        column.metric(label, value)

    st.header("Latest proposal (suggestions — not buy/sell)")
    rows = proposal_rows(latest_proposal(repo))
    if rows:
        st.table(rows)
    else:
        st.write("_No active proposals._")

    st.header("Briefings")
    kind = st.selectbox("Brief kind", ["daily", "weekly", "monthly"], index=1)
    if kind == "daily":
        brief = daily_brief(repo)
    elif kind == "monthly":
        brief = monthly_brief(repo)
    else:
        brief = weekly_brief(repo)
    st.markdown(brief.body_md)


if __name__ == "__main__":
    main()
