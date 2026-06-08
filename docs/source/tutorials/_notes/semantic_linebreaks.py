"""Reformat moduleX.md files: one sentence per line in prose paragraphs.

Skips code fences (``` and ~~~), HTML comments, directive markers (:::, ::::),
headings, bullets/lists, blockquotes, tables, and YAML frontmatter. Only
top-level prose paragraphs are reformatted.

Usage:
    uv run python docs/source/tutorials/_notes/semantic_linebreaks.py \
        docs/source/tutorials/module0.md  [more files...]

Backtick-aware (won't split inside inline code or fenced code).
Skips sentence breaks after common abbreviations (e.g., i.e., etc.).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ABBREVS = frozenset({
    'e.g.', 'i.e.', 'cf.', 'etc.', 'vs.', 'al.', 'Dr.', 'Mr.', 'Mrs.', 'Ms.',
    'Fig.', 'Eq.', 'vol.', 'pp.', 'ed.', 'Inc.', 'Ltd.', 'St.', 'Jr.', 'Sr.',
    'No.', 'viz.', 'Mod.',
})


_BULLET_RE = re.compile(r'^(?:[-+*]\s|\d+[.)]\s)')


def _skip_line(line: str) -> bool:
    """Return True for lines that should NOT be reformatted."""
    stripped = line.strip()
    if not stripped:
        return True
    # Headings, tables, blockquotes.
    if stripped[0] in '#|>':
        return True
    # Lists: a bullet marker (`-`, `+`, `*`) or ordered marker (`1.`, `1)`)
    # must be followed by whitespace. Bare `**bold**` or `*emphasis*` at the
    # start of a paragraph is prose, not a list.
    if _BULLET_RE.match(stripped):
        return True
    if stripped.startswith(':::') or stripped.startswith('::::'):
        return True
    if stripped.startswith('<!--') or stripped.startswith('-->') or stripped.startswith('---'):
        return True
    # Indented (likely list continuation, definition list, etc.).
    if line.startswith((' ', '\t')):
        return True
    # MyST role / link reference labels.
    if stripped.startswith('(') and stripped.endswith(')='):
        return True
    return False


_FENCE_RE = re.compile(r'^(```|~~~)')


def _split_into_sentences(paragraph: str) -> list[str]:
    """Split a single prose paragraph into one sentence per line."""
    # Replace inline-code spans with placeholders so we don't split inside them.
    spans: list[str] = []

    def stash(match: re.Match[str]) -> str:
        spans.append(match.group(0))
        return f'\x00{len(spans) - 1}\x00'

    masked = re.sub(r'``[^`\n]+``|`[^`\n]+`', stash, paragraph)

    # Candidate sentence boundary: `. ` followed by a sentence-start glyph.
    # `(?<=\.)` after the period, look ahead for whitespace + sentence start.
    # Sentence start: uppercase letter, *, _, `, [, \x00 (masked code), or digit.
    pattern = re.compile(r'(?<=[.!?])[ \t]+(?=[A-Z*_`\[\x00])')
    parts = pattern.split(masked)

    # Merge back parts that the split broke after an abbreviation.
    fixed: list[str] = []
    for part in parts:
        if fixed:
            tokens = fixed[-1].rstrip().split()
            if tokens and tokens[-1] in ABBREVS:
                fixed[-1] = fixed[-1].rstrip() + ' ' + part
                continue
        fixed.append(part)

    # Restore inline-code spans.
    def restore(s: str) -> str:
        return re.sub(r'\x00(\d+)\x00', lambda m: spans[int(m.group(1))], s)

    return [restore(p).rstrip() for p in fixed if p.strip()]


def _reformat_paragraph(lines: list[str]) -> list[str]:
    """Join a prose paragraph (list of source lines) and re-split per-sentence."""
    paragraph = ' '.join(line.strip() for line in lines)
    return _split_into_sentences(paragraph)


def reformat(text: str) -> str:
    out: list[str] = []
    in_fence = False
    in_frontmatter = False
    buffered: list[str] = []

    lines = text.splitlines()

    def flush() -> None:
        if buffered:
            out.extend(_reformat_paragraph(buffered))
            buffered.clear()

    for i, line in enumerate(lines):
        # YAML frontmatter (only at start of file).
        if i == 0 and line.strip() == '---':
            in_frontmatter = True
            out.append(line)
            continue
        if in_frontmatter:
            out.append(line)
            if line.strip() == '---':
                in_frontmatter = False
            continue

        # Code-fence toggle.
        if _FENCE_RE.match(line):
            flush()
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        if _skip_line(line):
            flush()
            out.append(line)
            continue

        # Prose line: accumulate.
        buffered.append(line)

    flush()
    return '\n'.join(out) + ('\n' if text.endswith('\n') else '')


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    for arg in argv:
        path = Path(arg)
        original = path.read_text()
        rewritten = reformat(original)
        if rewritten != original:
            path.write_text(rewritten)
            print(f'reformatted: {path}')
        else:
            print(f'unchanged:   {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
