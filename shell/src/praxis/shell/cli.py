"""Verdaca command-line entrypoint."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

from praxis.kernel.session_index.models import SessionFilter
from praxis.kernel.session_index.sqlite_store import (
    SqliteSessionIndex,
    default_dev_db_path,
)

_DB_ENV = "VERDACA_SESSION_INDEX_DB"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verdaca")
    subcommands = parser.add_subparsers(dest="resource", required=True)

    session = subcommands.add_parser("session", help="Inspect indexed Verdaca sessions")
    session_commands = session.add_subparsers(dest="action", required=True)

    list_command = session_commands.add_parser("list", help="List indexed sessions")
    list_command.add_argument("--user", dest="user_id", help="Filter sessions by user_id")
    list_command.set_defaults(func=_session_list)

    show_command = session_commands.add_parser("show", help="Show one indexed session")
    show_command.add_argument("session_id")
    show_command.set_defaults(func=_session_show)

    return parser


def _store() -> SqliteSessionIndex:
    db_path = os.environ.get(_DB_ENV)
    return SqliteSessionIndex(Path(db_path) if db_path else default_dev_db_path())


def _session_list(args: argparse.Namespace) -> int:
    criteria = None
    if args.user_id is not None:
        criteria = SessionFilter(
            schema_version=1,
            correlation_id="verdaca-cli",
            idempotency_key=None,
            user_id=args.user_id,
        )
    for record in _store().list_sessions(criteria=criteria):
        user_id = record.user_id if record.user_id is not None else "-"
        print(f"{record.session_id}\t{user_id}\t{record.status}\t{record.created_at.isoformat()}")
    return 0


def _session_show(args: argparse.Namespace) -> int:
    store = _store()
    record = store.get_session(args.session_id)
    if record is None:
        print(f"session not found: {args.session_id}")
        return 1

    print(f"session_id: {record.session_id}")
    print(f"user_id: {record.user_id if record.user_id is not None else '-'}")
    print(f"status: {record.status}")
    print(f"created_at: {record.created_at.isoformat()}")
    if record.title is not None:
        print(f"title: {record.title}")
    if record.artifact_ids:
        print("artifacts:")
        for artifact_id in record.artifact_ids:
            artifact = store.get_artifact(record.session_id, artifact_id)
            if artifact is None:
                continue
            print(f"- {artifact.id}\t{artifact.kind}\t{artifact.payload_uri}\t{artifact.byte_size}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
