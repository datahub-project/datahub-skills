"""Single-column ML impact query — the skill's thin driver over Blastradar's core.

This is the entry point the `datahub-ml-impact` skill calls to answer
"what ML systems break if I change <table>.<column>?". It does NOT reimplement any
lineage/scoring logic — it imports Blastradar's core library and runs the exact same
deterministic pipeline the CI agent uses (walk → score → narrate → render), just for a
single column instead of a whole PR diff.

Usage:
    python ml_impact.py --table customers --column customer_since
    python ml_impact.py --table customers --column customer_since --json
    python ml_impact.py --table customers --column customer_since --no-llm

Connection: reads DATAHUB_GMS_URL / DATAHUB_GMS_TOKEN from the environment (see
Blastradar's .env.example). Set BLASTRADAR_REPLAY=<recording.json> to try it fully
offline against Blastradar's recorded fixtures (no DataHub required) — handy for a
first look before pointing it at a real instance.

Requires Blastradar to be importable:  pip install "blastradar @ git+<repo-url>"
(or run from a Blastradar checkout that has been `pip install -e .`'d).
"""

from __future__ import annotations

import argparse
import sys


def _fail(msg: str) -> "int":
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        from blastradar.datahub.client import DataHubClient, DataHubClientError
        from blastradar.datahub.resolver import Resolver
        from blastradar.datahub.walker import walk
        from blastradar.models import ChangeEvent, ChangeKind
        from blastradar.narrate import narrate
        from blastradar.report import Analysis, render_report
        from blastradar.scoring import score_graph
    except ModuleNotFoundError as e:  # pragma: no cover - environment guard
        return _fail(
            f"Blastradar is not installed ({e}). Install it with:\n"
            f'  pip install "blastradar @ git+https://github.com/Pratham-90/blastradar"\n'
            f"or run from a Blastradar checkout after `pip install -e .`.")

    ap = argparse.ArgumentParser(description="Ask which ML systems a column change breaks.")
    ap.add_argument("--table", required=True, help="Model/table name, e.g. customers.")
    ap.add_argument("--column", required=True, help="Column being changed, e.g. customer_since.")
    ap.add_argument("--kind", default="DROP_COLUMN",
                    choices=[k.value for k in ChangeKind if k.value != "DROP_TABLE"],
                    help="Kind of change (default: DROP_COLUMN).")
    ap.add_argument("--max-hops", type=int, default=6, help="Lineage hop cap (default: 6).")
    ap.add_argument("--no-llm", action="store_true",
                    help="Skip the LLM; use the deterministic templated narration.")
    ap.add_argument("--json", action="store_true", help="Emit the machine-readable JSON.")
    args = ap.parse_args()

    try:
        client = DataHubClient.from_env()   # honours BLASTRADAR_REPLAY for offline use
        client.test_connection()
    except (DataHubClientError, OSError) as e:
        return _fail(
            f"Could not reach DataHub ({type(e).__name__}: {e}).\n"
            f"Set DATAHUB_GMS_URL (and DATAHUB_GMS_TOKEN if auth is on), or set "
            f"BLASTRADAR_REPLAY=<recording.json> to run offline against fixtures.")

    resolver = Resolver(client)
    change = ChangeEvent(kind=ChangeKind(args.kind), table=args.table, column=args.column,
                         source_file=f"models/{args.table}.sql")

    # The core library — unchanged — does the work.
    graph = walk(change, client=client, resolver=resolver, max_hops=args.max_hops)
    scored = score_graph(graph)
    narration = narrate(change, scored, use_llm=not args.no_llm)
    report = render_report([Analysis(change, graph)], scored, narration)

    print(report.json() if args.json else report.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
