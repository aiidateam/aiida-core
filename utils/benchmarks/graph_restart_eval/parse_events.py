###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Parse a `pi --mode json` JSONL event stream into an evaluation summary.

Authoritative usage comes from `message_end` records carrying assistant
messages (per `docs/json.md`: `message_end` holds the authoritative final
message; `message_update` deltas are display-only). Wall-clock time is measured
by the harness with `time.monotonic()` and passed in via `--wall-s`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_events_file(path: str | Path) -> dict:
    """Parse a JSONL event stream into token/time/stop-reason summary."""
    total = {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0, 'totalTokens': 0}
    assistant_messages: list[dict] = []
    tool_calls = 0
    tool_ends_ok = 0
    tool_ends_err = 0
    settled_aborted: bool | None = None
    records = 0
    first_type: str | None = None
    errors: list[str] = []

    with open(path, encoding='utf-8') as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            records += 1
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f'line {line_no}: invalid JSON ({exc})')
                continue
            etype = event.get('type')
            if first_type is None:
                first_type = etype
            if etype == 'message_end':
                message = event.get('message', {})
                if message.get('role') == 'assistant':
                    usage = message.get('usage', {})
                    for key in total:
                        total[key] += int(usage.get(key, 0) or 0)
                    assistant_messages.append(
                        {
                            'provider': message.get('provider'),
                            'model': message.get('model'),
                            'stopReason': message.get('stopReason'),
                            'usage': {k: usage.get(k, 0) for k in total},
                        }
                    )
            elif etype == 'tool_execution_start':
                tool_calls += 1
            elif etype == 'tool_execution_end':
                if event.get('isError'):
                    tool_ends_err += 1
                else:
                    tool_ends_ok += 1
            elif etype == 'agent_settled':
                settled_aborted = event.get('aborted')

    last = assistant_messages[-1] if assistant_messages else {}
    return {
        'records': records,
        'first_record_type': first_type,
        'assistant_responses': len(assistant_messages),
        'usage_tokens': total,
        'provider': last.get('provider'),
        'model': last.get('model'),
        'stop_reason': last.get('stopReason'),
        'tool_calls_started': tool_calls,
        'tool_calls_ok': tool_ends_ok,
        'tool_calls_error': tool_ends_err,
        'agent_settled_aborted': settled_aborted,
        'parse_errors': errors,
    }


def total_tokens(summary: dict) -> int:
    """Return the summed assistant total tokens from a parsed summary."""
    usage = summary.get('usage_tokens') or {}
    return int(usage.get('totalTokens') or 0)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events', help='Path to the JSONL event stream (stdout of pi --mode json).')
    parser.add_argument('--wall-s', type=float, default=None, help='Harness-measured wall time (monotonic).')
    parser.add_argument('--out', default=None, help='Write summary JSON here (default: stdout).')
    parser.add_argument(
        '--check-cap',
        type=int,
        default=None,
        help='Exit non-zero when summed totalTokens exceed this cap (post-hoc budget check).',
    )
    args = parser.parse_args()

    summary = parse_events_file(args.events)
    if args.wall_s is not None:
        summary['wall_s_monotonic'] = args.wall_s
    text = json.dumps(summary, indent=2)
    if args.out:
        Path(args.out).write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    if args.check_cap is not None and total_tokens(summary) > args.check_cap:
        msg = f'total tokens {total_tokens(summary)} exceed cap {args.check_cap}'
        raise SystemExit(msg)


if __name__ == '__main__':
    main()
