###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Sphinx extension: polish the downloadable tutorial notebooks (optional).

MyST-NB already emits a runnable ``.ipynb`` for every ``{nb-download}`` link, so
downloads work without this extension. It only makes the *rendering* of those
notebooks nicer in plain Jupyter, by post-processing each ``.ipynb`` in
``_downloads/`` after the build:

1. Convert MyST admonitions to HTML ``<div class="alert ...">`` blocks.
2. Convert MyST dropdowns to ``<details>`` elements and flatten grids, recursing
   into nested directives (images) inside them.
3. Inline ``{image}``/``{figure}`` directives as self-contained ``<img>`` tags.
4. Strip MyST-only inline roles to plain text.
5. Remove target labels and self-referential download links.

Only markdown cells are touched. The notebooks are already self-contained: their
setup cells create the profile inline and read the gsrd inputs from the installed
package, so the code cells need no post-processing.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

# Colon-fence opening: :::{directive} optional_arg
# Directive names may contain hyphens (``grid-item``, ``grid-item-card``).
_FENCE_OPEN = re.compile(r'^(:{3,})\{([\w-]+)\}\s*(.*)')
# Directive option: :key: value
_DIRECTIVE_OPT = re.compile(r'^:(\w[\w-]*):\s*(.*)')
# Backtick-fence directive: ```{directive} arg
_BACKTICK_DIRECTIVE = re.compile(r'^```\{(\w+)\}\s*(.*)')

# Inline MyST roles
# Role names may contain ``:`` (``py:class``) and ``-`` (``bdg-secondary``, ``nb-download``).
_ROLE_WITH_ANGLE = re.compile(r'\{[a-z:-]+\}`([^<`]*?)\s*<[^>]+>`')  # {ref}`text <target>`
_ROLE_TILDE = re.compile(r'\{[a-z:-]+\}`~([^`]+)`')  # {py:class}`~full.path.Name` → Name
_ROLE_PLAIN = re.compile(r'\{[a-z:-]+\}`([^`]+)`')  # {role}`text`
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


def _render_image(rel_path: str, options: dict[str, str], source_dir: Path) -> str:
    """Render an ``{image}``/``{figure}`` target as a self-contained ``<img>`` tag.

    A local image's bytes are embedded as a base64 data URI so the downloaded
    notebook displays it without depending on the working directory; a remote URL
    is kept as-is (the fallback for a path that is not a local file).
    """
    path = source_dir / rel_path
    attrs = ''
    if (width := options.get('width')) is not None:
        attrs += f' width="{width}"'
    if (alt := options.get('alt')) is not None:
        attrs += f' alt="{alt}"'

    if path.is_file():
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        data = base64.b64encode(path.read_bytes()).decode('ascii')
        src = f'data:{mime};base64,{data}'
    else:
        src = rel_path

    img = f'<img src="{src}"{attrs}>'
    if options.get('align') in ('center', 'left', 'right'):
        return f'<div align="{options["align"]}">\n{img}\n</div>'
    return img


def _collect_options(lines: list[str], start: int) -> tuple[dict[str, str], int]:
    """Parse consecutive ``:key: value`` directive-option lines starting at *start*.

    :return: the parsed options, and the index of the first line that is not an option.
    """
    options: dict[str, str] = {}
    i = start
    while i < len(lines) and (match := _DIRECTIVE_OPT.match(lines[i])) is not None:
        options[match.group(1)] = match.group(2)
        i += 1
    return options, i


def _convert_myst_block(lines: list[str], source_dir: Path) -> list[str]:
    """Process a markdown cell's lines, converting MyST block directives."""
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = _FENCE_OPEN.match(line)
        if m is None:
            bm = _BACKTICK_DIRECTIVE.match(line)
            if bm is not None and bm.group(1) in ('image', 'figure'):
                rel_path = bm.group(2).strip()
                options, i = _collect_options(lines, i + 1)
                # Drop any remaining content (e.g. a figure caption) up to the
                # closing backtick fence.
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    i += 1
                if i < len(lines):
                    i += 1  # consume the closing fence

                output.append(_render_image(rel_path, options, source_dir))
                continue
            output.append(line)
            i += 1
            continue

        fence_len = len(m.group(1))
        directive = m.group(2)
        arg = m.group(3).strip()

        # Collect options and content
        options, i = _collect_options(lines, i + 1)

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

        # Recurse so directives nested inside a container (an ``{image}`` in a
        # dropdown, images inside a ``{grid}``, ...) are converted too, not left
        # as raw MyST.
        inner = _convert_myst_block(content.split('\n'), source_dir)

        if directive in _ALERT_MAP:
            alert_type, title = _ALERT_MAP[directive]
            output.append(f'<div class="alert alert-{alert_type}">')
            output.append(f'<strong>{title}:</strong>\n')
            output.extend(inner)
            output.append('</div>')

        elif directive == 'admonition':
            css = options.get('class', 'note')
            alert_type = 'warning' if css in ('warning', 'important') else 'info'
            output.append(f'<div class="alert alert-{alert_type}">')
            output.append(f'<strong>{arg}:</strong>\n')
            output.extend(inner)
            output.append('</div>')

        elif directive == 'dropdown':
            output.append('<details>')
            output.append(f'<summary>{arg}</summary>\n')
            output.extend(inner)
            output.append('</details>')

        else:
            # Layout containers (``grid``, ``grid-item``, ...) have no Jupyter
            # equivalent: drop the wrapper and keep the converted content. Other
            # unknown directives keep their argument as a bold lead-in.
            if arg and not directive.startswith('grid'):
                output.append(f'**{arg}**\n')
            output.extend(inner)

    return output


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
    # Remove empty alert divs (e.g. the tip that only contained a {nb-download} link,
    # whose line is stripped earlier in _polish_source).
    text = _EMPTY_ALERT.sub('', text)
    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _has_myst(text: str) -> bool:
    """True if *text* contains a MyST construct worth converting."""
    return ':::' in text or '{' in text or ')=' in text


def _polish_source(source: str, source_dir: Path) -> str:
    """Convert every MyST construct in one markdown cell's source to plain-Jupyter markdown."""
    text = '\n'.join(_convert_myst_block(source.split('\n'), source_dir))
    # Drop the self-referential ``{nb-download}`` line before roles are stripped to plain
    # text: role conversion erases the ``{nb-download}`` marker this match relies on, which
    # would otherwise leave the "download as a notebook" tip (and its now-empty alert div)
    # stranded in the downloaded notebook.
    text = _NB_DOWNLOAD_LINE.sub('', text)
    text = _convert_inline_roles(text)
    return _clean_markdown(text)


def _polish_markdown_cells(cells: list[dict[str, Any]], source_dir: Path) -> bool:
    """Convert MyST syntax to plain-Jupyter markdown in each markdown cell, in place.

    The cells belong to a notebook just loaded from disk and about to be written back,
    so mutating them in place is deliberate.

    :return: ``True`` if any cell changed, so the caller only rewrites when needed.
    """
    changed = False
    for cell in cells:
        if cell.get('cell_type') != 'markdown':
            continue
        original = ''.join(cell.get('source', []))
        if not _has_myst(original):
            continue
        polished = _polish_source(original, source_dir)
        if polished != original.strip():
            cell['source'] = [polished]
            changed = True
    return changed


def on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    """Post-process downloaded notebooks after build completes."""
    if exception is not None:
        return

    downloads_dir = Path(app.outdir) / '_downloads'
    if not downloads_dir.is_dir():
        return

    source_dir = Path(app.srcdir) / 'tutorials'
    # Only the tutorial module notebooks need this treatment. Other downloadable
    # notebooks (e.g. howto pages) have their includes outside ``tutorials/`` and
    # would be mangled by the tutorial-relative image inlining and MyST conversions.
    module_stems = {path.stem for path in source_dir.glob('module*.md')}
    count = 0

    for notebook_path in downloads_dir.rglob('*.ipynb'):
        if notebook_path.stem not in module_stems:
            continue
        nb: dict[str, Any] = json.loads(notebook_path.read_text(encoding='utf-8'))

        if _polish_markdown_cells(nb.get('cells', []), source_dir):
            notebook_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
            count += 1
            logger.info('polish_download_notebooks: processed %s', notebook_path.name)

    if count:
        logger.info('polish_download_notebooks: post-processed %d notebook(s)', count)


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect('build-finished', on_build_finished)
    return {'version': '0.2', 'parallel_read_safe': True, 'parallel_write_safe': True}
