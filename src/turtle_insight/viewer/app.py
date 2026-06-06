"""Streamlit viewer (run with ``make run-viewer``).

Explore the thesis graph, thesis detail (claim, conviction, falsifiers,
evidence links), the latest proposal, and the weekly brief. Read-only.
Uses absolute imports because Streamlit runs this file as a script.
"""

from __future__ import annotations

import streamlit as st

from turtle_insight.config.settings import get_settings
from turtle_insight.services.advisory import (
    daily_brief,
    latest_proposal,
    monthly_brief,
    weekly_brief,
)
from turtle_insight.storage.sqlite_repo import SqliteRepository


def _repo() -> SqliteRepository:
    return SqliteRepository.from_url(get_settings().ti_db_url)


def main() -> None:
    st.set_page_config(page_title="Turtle Insight", layout="wide")
    st.title("🐢 Turtle Insight — Thesis Graph (local, read-only)")

    repo = _repo()
    theses = repo.list_theses()
    if not theses:
        st.info("No theses in the DB yet. Run `make sync` or an analysis cycle to populate it.")
        return

    statuses = sorted({t.status.value for t in theses})
    chosen = st.sidebar.multiselect("Status filter", statuses, default=statuses)
    visible = [t for t in theses if t.status.value in chosen]

    st.subheader("Thesis graph")
    dot = ["digraph G { rankdir=LR; node [shape=box, style=rounded];"]
    for thesis in visible:
        dot.append(
            f'"{thesis.id}" [label="{thesis.id}\\n{thesis.layer.value}/{thesis.status.value}"];'
        )
        for parent in thesis.parents:
            dot.append(f'"{parent}" -> "{thesis.id}";')
    dot.append("}")
    st.graphviz_chart("\n".join(dot))

    ids = [t.id for t in visible]
    if ids:
        selected = st.selectbox("Inspect thesis", ids)
        detail = repo.get_thesis(selected)
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

    st.header("Latest proposal (suggestions — not buy/sell)")
    proposal = latest_proposal(repo)
    if not proposal.items:
        st.write("_No active proposals._")
    for item in proposal.items:
        st.markdown(
            f"**{item.thesis_id} · {item.asset.market}:{item.asset.ticker}** — {item.stance}"
        )
        st.write(f"- bull: {item.scenarios.bull}")
        st.write(f"- base: {item.scenarios.base}")
        st.write(f"- bear: {item.scenarios.bear}")
        st.write(f"- sizing: {item.sizing_rationale}")

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
