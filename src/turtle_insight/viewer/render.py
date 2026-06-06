"""Pure rendering helpers for the Streamlit viewer.

No ``streamlit`` import here, so the visualization logic (graph DOT, regime
badge, scorecard/proposal tables) is unit-tested in CI; ``viewer/app.py`` stays
a thin rendering shell over these functions.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..agents.market import MarketRegime
from ..domain.calibration import PeriodScorecard, Scorecard
from ..domain.proposal import Proposal
from ..domain.thesis import Thesis

# Colour per layer; active nodes are drawn bolder.
LAYER_COLORS: dict[str, str] = {
    "macro": "#6a4c93",
    "trend": "#1982c4",
    "chain": "#8ac926",
    "asset": "#ff924c",
}
_REGIME_ICONS: dict[str, str] = {"risk_on": "🟢", "risk_off": "🔴", "neutral": "⚪"}


def _esc(text: str) -> str:
    return text.replace('"', '\\"')


def build_graph_dot(theses: Iterable[Thesis]) -> str:
    """Build a Graphviz DOT graph: layer-coloured nodes, parent+child edges."""
    items = list(theses)
    known = {t.id for t in items}
    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontcolor=white];',
    ]
    for thesis in items:
        color = LAYER_COLORS.get(thesis.layer.value, "#999999")
        penwidth = "2.5" if thesis.status.value == "active" else "1.0"
        label = _esc(f"{thesis.id}\n{thesis.layer.value} · {thesis.status.value}")
        lines.append(
            f'  "{thesis.id}" [label="{label}", fillcolor="{color}", penwidth={penwidth}];'
        )

    edges: set[tuple[str, str]] = set()
    for thesis in items:
        for parent in thesis.parents:
            if parent in known:
                edges.add((parent, thesis.id))
        for child in thesis.children:
            if child in known:
                edges.add((thesis.id, child))
    for src, dst in sorted(edges):
        lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines)


def regime_badge(regime: MarketRegime) -> str:
    icon = _REGIME_ICONS.get(regime.regime, "⚪")
    return (
        f"{icon} **{regime.regime}** · leader **{regime.leader}** "
        f"(KR {regime.kr_signals} / US {regime.us_signals} price signals)"
    )


def scorecard_metrics(scorecard: Scorecard) -> list[tuple[str, str]]:
    return [
        ("Predictions", str(scorecard.total)),
        ("Accuracy", f"{scorecard.accuracy:.0%}"),
        ("Mean Brier", f"{scorecard.mean_brier:.3f}"),
    ]


def accuracy_by_period(periods: Iterable[PeriodScorecard]) -> dict[str, float]:
    """Map period -> accuracy for a calibration trend line chart."""
    return {p.period: p.accuracy for p in periods}


def proposal_rows(proposal: Proposal) -> list[dict[str, str]]:
    return [
        {
            "thesis": item.thesis_id,
            "asset": f"{item.asset.market}:{item.asset.ticker}",
            "stance": item.stance,
            "bull": item.scenarios.bull,
            "bear": item.scenarios.bear,
        }
        for item in proposal.items
    ]
