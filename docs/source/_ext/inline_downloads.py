"""Sphinx extension: make downloaded notebooks self-contained and Jupyter-friendly.

After the build, post-process every ``.ipynb`` in ``_downloads/``:

1. Replace ``%run -i <path>`` code cells with inlined file contents.
2. Convert MyST admonitions to HTML ``<div class="alert ...">`` blocks.
3. Convert MyST dropdowns to ``<details>`` elements (with literalinclude inlined).
4. Strip MyST-only inline roles to plain text.
5. Remove target labels and self-referential download links.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_RUN_PATTERN = re.compile(r'^%run\s+-i\s+(.+)$', re.MULTILINE)

# Colon-fence opening: :::{directive} optional_arg
_FENCE_OPEN = re.compile(r'^(:{3,})\{(\w+)\}\s*(.*)')
# Directive option: :key: value
_DIRECTIVE_OPT = re.compile(r'^:(\w[\w-]*):\s*(.*)')
# Backtick-fence directive: ```{directive} arg
_BACKTICK_DIRECTIVE = re.compile(r'^```\{(\w+)\}\s*(.*)')

# Inline MyST roles
_ROLE_WITH_ANGLE = re.compile(r'\{[a-z:]+\}`([^<`]*?)\s*<[^>]+>`')  # {ref}`text <target>`
_ROLE_TILDE = re.compile(r'\{[a-z:]+\}`~([^`]+)`')  # {py:class}`~full.path.Name` → Name
_ROLE_PLAIN = re.compile(r'\{[a-z:]+\}`([^`]+)`')  # {role}`text`
_TARGET_LABEL = re.compile(r'^\([a-z][a-z0-9:_-]*\)=\s*$', re.MULTILINE)
_NB_DOWNLOAD_LINE = re.compile(r'^.*\{nb-download\}.*$', re.MULTILINE)
_EMPTY_ALERT = re.compile(r'<div class="alert alert-\w+">\s*<strong>\w+:</strong>\s*</div>', re.DOTALL)

# Alert class mapping
_ALERT_MAP: dict[str, tuple[str, str]] = {
    'tip': ('info', 'Tip'),
    'note': ('info', 'Note'),
    'seealso': ('info', 'See also'),
    'important': ('warning', 'Important'),
    'warning': ('warning', 'Warning'),
    'danger': ('danger', 'Danger'),
}


# ---------------------------------------------------------------------------
# Code cell: inline %run -i
# ---------------------------------------------------------------------------


def _inline_run_cells(cells: list[dict], source_dir: Path) -> bool:
    """Replace ``%run -i <path>`` cells with inlined file contents."""
    modified = False

    for cell in cells:
        if cell.get('cell_type') != 'code':
            continue

        source = ''.join(cell.get('source', []))
        matches = list(_RUN_PATTERN.finditer(source))
        if not matches:
            continue

        new_parts: list[str] = []
        for match in matches:
            rel_path = match.group(1).strip().strip('\'"')
            include_file = source_dir / rel_path
            if not include_file.is_file():
                logger.warning('inline_downloads: file not found: %s', include_file)
                new_parts.append(match.group(0))
                continue
            content = include_file.read_text(encoding='utf-8')
            new_parts.append(f'# — inlined from {rel_path} —\n{content}')
            modified = True

        if modified:
            remaining = _RUN_PATTERN.sub('', source).strip()
            if remaining:
                new_parts.append(remaining)
            cell['source'] = ['\n\n'.join(new_parts)]
            cell['outputs'] = []
            cell['execution_count'] = None

    return modified


# ---------------------------------------------------------------------------
# Markdown cell: convert MyST → Jupyter-compatible markdown
# ---------------------------------------------------------------------------


def _read_include(rel_path: str, source_dir: Path) -> str | None:
    """Read an include file, returning its contents or None."""
    path = source_dir / rel_path
    if path.is_file():
        return path.read_text(encoding='utf-8')
    return None


def _convert_myst_block(lines: list[str], source_dir: Path) -> list[str]:
    """Process a markdown cell's lines, converting MyST block directives."""
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = _FENCE_OPEN.match(line)
        if m is None:
            output.append(line)
            i += 1
            continue

        fence_len = len(m.group(1))
        directive = m.group(2)
        arg = m.group(3).strip()

        # Collect options and content
        i += 1
        options: dict[str, str] = {}
        while i < len(lines):
            om = _DIRECTIVE_OPT.match(lines[i])
            if om is None:
                break
            options[om.group(1)] = om.group(2)
            i += 1

        # Skip blank line after options
        if i < len(lines) and lines[i].strip() == '':
            i += 1

        # Collect content until closing fence (matching or greater colon count)
        content_lines: list[str] = []
        while i < len(lines):
            if re.match(rf'^:{{{fence_len},}}$', lines[i].strip()):
                i += 1
                break
            content_lines.append(lines[i])
            i += 1

        content = '\n'.join(content_lines).strip()

        # --- Convert directive ---

        if directive in _ALERT_MAP:
            alert_type, title = _ALERT_MAP[directive]
            output.append(f'<div class="alert alert-{alert_type}">')
            output.append(f'<strong>{title}:</strong>\n')
            output.append(content)
            output.append('</div>')

        elif directive == 'admonition':
            css = options.get('class', 'note')
            alert_type = 'warning' if css in ('warning', 'important') else 'info'
            output.append(f'<div class="alert alert-{alert_type}">')
            output.append(f'<strong>{arg}:</strong>\n')
            output.append(content)
            output.append('</div>')

        elif directive == 'dropdown':
            # Inline any {literalinclude} inside the dropdown
            inner = _inline_literalinclude(content, source_dir)
            output.append('<details>')
            output.append(f'<summary>{arg}</summary>\n')
            output.append(inner)
            output.append('</details>')

        else:
            # Unknown directive — keep content as plain markdown
            if arg:
                output.append(f'**{arg}**\n')
            output.append(content)

    return output


def _inline_literalinclude(text: str, source_dir: Path) -> str:
    """Replace ``{literalinclude}`` blocks with the actual file contents."""
    result_lines: list[str] = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        m = _BACKTICK_DIRECTIVE.match(lines[i])
        if m is not None and m.group(1) == 'literalinclude':
            rel_path = m.group(2).strip()
            # Collect options
            lang = 'python'
            i += 1
            while i < len(lines) and _DIRECTIVE_OPT.match(lines[i]):
                om = _DIRECTIVE_OPT.match(lines[i])
                if om is not None and om.group(1) == 'language':
                    lang = om.group(2)
                i += 1
            # Skip closing backticks
            if i < len(lines) and lines[i].strip().startswith('```'):
                i += 1

            content = _read_include(rel_path, source_dir)
            if content is not None:
                result_lines.append(f'```{lang}')
                result_lines.append(content.rstrip())
                result_lines.append('```')
            else:
                result_lines.append(f'*File not found: {rel_path}*')
        else:
            result_lines.append(lines[i])
            i += 1

    return '\n'.join(result_lines)


def _convert_inline_roles(text: str) -> str:
    """Strip MyST inline roles to plain text."""
    # {role}`display text <target>` → display text
    text = _ROLE_WITH_ANGLE.sub(r'\1', text)
    # {py:class}`~aiida.orm.Dict` → Dict (last component after ~)
    text = _ROLE_TILDE.sub(lambda m: m.group(1).rsplit('.', 1)[-1], text)
    # {role}`text` → text
    text = _ROLE_PLAIN.sub(r'\1', text)
    return text


def _clean_markdown(text: str) -> str:
    """Remove MyST-only constructs that have no Jupyter equivalent."""
    # Remove target labels like (tutorial:module1)=
    text = _TARGET_LABEL.sub('', text)
    # Remove {nb-download} lines (self-referential in downloaded notebook)
    text = _NB_DOWNLOAD_LINE.sub('', text)
    # Remove empty alert divs (e.g. tip that only contained a {nb-download} link)
    text = _EMPTY_ALERT.sub('', text)
    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _process_markdown_cells(cells: list[dict], source_dir: Path) -> bool:
    """Convert MyST syntax in markdown cells to Jupyter-compatible markdown."""
    modified = False

    for cell in cells:
        if cell.get('cell_type') != 'markdown':
            continue

        original = ''.join(cell.get('source', []))

        # Skip cells that don't contain any MyST constructs
        if ':::' not in original and '{' not in original and ')=' not in original:
            continue

        lines = original.split('\n')
        converted = _convert_myst_block(lines, source_dir)
        text = '\n'.join(converted)
        text = _convert_inline_roles(text)
        text = _clean_markdown(text)

        if text != original.strip():
            cell['source'] = [text]
            modified = True

    return modified


# ---------------------------------------------------------------------------
# Sphinx hook
# ---------------------------------------------------------------------------


def on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    """Post-process downloaded notebooks after build completes."""
    if exception is not None:
        return

    downloads_dir = Path(app.outdir) / '_downloads'
    if not downloads_dir.is_dir():
        return

    source_dir = Path(app.srcdir) / 'tutorials'
    count = 0

    for notebook_path in downloads_dir.rglob('*.ipynb'):
        with open(notebook_path, encoding='utf-8') as f:
            nb = json.load(f)

        cells = nb.get('cells', [])
        changed_code = _inline_run_cells(cells, source_dir)
        changed_md = _process_markdown_cells(cells, source_dir)

        if changed_code or changed_md:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
                f.write('\n')
            count += 1
            logger.info('inline_downloads: processed %s', notebook_path.name)

    if count:
        logger.info('inline_downloads: post-processed %d notebook(s)', count)


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect('build-finished', on_build_finished)
    return {'version': '0.2', 'parallel_read_safe': True, 'parallel_write_safe': True}
