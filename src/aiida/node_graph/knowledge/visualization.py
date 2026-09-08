from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

try:  # pragma: no cover - import guarded
    from graphviz import Digraph
except Exception:  # pragma: no cover - import guarded
    Digraph = None


def _require_graphviz() -> None:
    if Digraph is None:
        raise RuntimeError("graphviz is not installed; please `pip install graphviz`.")


def to_graphviz(kg: Any) -> "Digraph":
    """Render a KnowledgeGraph into a Graphviz Digraph."""
    _require_graphviz()

    rdf = kg.as_rdflib()
    dot = Digraph(name="KnowledgeGraph")
    node_ids: dict[Any, str] = {}

    def _label(term: Any) -> str:
        try:
            return rdf.namespace_manager.normalizeUri(term)
        except Exception:
            return str(term)

    def _node_id(term: Any) -> str:
        if term not in node_ids:
            node_ids[term] = f"n{len(node_ids)}"
        return node_ids[term]

    for subj, pred, obj in rdf:
        s_id = _node_id(subj)
        o_id = _node_id(obj)
        dot.node(s_id, _label(subj))
        dot.node(o_id, _label(obj))
        dot.edge(s_id, o_id, label=_label(pred))
    return dot


def to_graphviz_svg(kg: Any) -> str:
    """Return an SVG serialization of the knowledge graph via graphviz."""
    graph = to_graphviz(kg)
    return graph.pipe(format="svg").decode("utf-8")


def _zoomable_html_fragment(
    *,
    container_id: str,
    inner_id: str,
    svg: str,
    zoom_in_id: str,
    zoom_out_id: str,
    reset_id: str,
    fullscreen_id: str,
    container_class: str = "",
    container_style: str = "",
    viewport_class: str = "",
    viewport_style: str = "",
    controls_class: str = "",
) -> str:
    """Reusable HTML/JS snippet that wires zoom/fullscreen controls to a graph SVG."""
    container_class_attr = f' class="{container_class}"' if container_class else ""
    container_style_attr = f' style="{container_style}"' if container_style else ""
    viewport_class_attr = f' class="{viewport_class}"' if viewport_class else ""
    viewport_style_attr = f' style="{viewport_style}"' if viewport_style else ""
    controls_class_attr = f' class="{controls_class}"' if controls_class else ""

    return "\n".join(
        [
            f'<div id="{container_id}"{container_class_attr}{container_style_attr}>',
            f"  <div{controls_class_attr}>",
            f'    <button id="{zoom_in_id}" title="Zoom in">+</button>',
            f'    <button id="{zoom_out_id}" title="Zoom out">-</button>',
            f'    <button id="{reset_id}" title="Reset zoom">reset</button>',
            f'    <button id="{fullscreen_id}" title="Fullscreen">fullscreen</button>',
            "  </div>",
            f'  <div id="{inner_id}"{viewport_class_attr}{viewport_style_attr}>{svg}</div>',
            "</div>",
            "<script>",
            "  (function() {",
            f"    const container = document.getElementById('{container_id}');",
            f"    const viewport = document.getElementById('{inner_id}');",
            f"    const btnIn = document.getElementById('{zoom_in_id}');",
            f"    const btnOut = document.getElementById('{zoom_out_id}');",
            f"    const btnReset = document.getElementById('{reset_id}');",
            f"    const btnFs = document.getElementById('{fullscreen_id}');",
            "    let kgScale = 1;",
            "    const clamp = (val) => Math.min(4, Math.max(0.25, val));",
            "    const apply = () => { viewport.style.transform = `scale(${kgScale})`; };",
            "    const setScale = (val) => { kgScale = clamp(val); apply(); };",
            "    const onWheel = (ev) => {",
            "      if (!ev.ctrlKey) return;",
            "      ev.preventDefault();",
            "      const factor = ev.deltaY < 0 ? 1.1 : 1/1.1;",
            "      const prev = kgScale;",
            "      setScale(kgScale * factor);",
            "      const rect = viewport.getBoundingClientRect();",
            "      const offsetX = ev.clientX - rect.left;",
            "      const offsetY = ev.clientY - rect.top;",
            "      const ratio = kgScale / prev;",
            "      container.scrollLeft = offsetX * (ratio - 1) + container.scrollLeft;",
            "      container.scrollTop = offsetY * (ratio - 1) + container.scrollTop;",
            "    };",
            "    container.addEventListener('wheel', onWheel, { passive: false });",
            "    btnIn.onclick = () => setScale(kgScale * 1.2);",
            "    btnOut.onclick = () => setScale(kgScale / 1.2);",
            "    btnReset.onclick = () => setScale(1);",
            "    btnFs.onclick = () => {",
            "      if (!document.fullscreenElement) {",
            "        container.requestFullscreen?.();",
            "      } else {",
            "        document.exitFullscreen?.();",
            "      }",
            "    };",
            "    apply();",
            "  })();",
            "</script>",
        ]
    )


def _control_ids(container_id: str) -> tuple[str, str, str, str, str]:
    inner_id = f"{container_id}-inner"
    zoom_in_id = f"{container_id}-zin"
    zoom_out_id = f"{container_id}-zout"
    reset_id = f"{container_id}-reset"
    fullscreen_id = f"{container_id}-fs"
    return inner_id, zoom_in_id, zoom_out_id, reset_id, fullscreen_id


def repr_html(kg: Any) -> Optional[str]:
    """IPython/Jupyter HTML repr hook."""
    try:
        svg = to_graphviz_svg(kg)
    except RuntimeError:
        return None

    container_id = f"kg-{kg.graph_uuid or uuid4()}"
    inner_id, zoom_in_id, zoom_out_id, reset_id, fullscreen_id = _control_ids(
        container_id
    )
    fragment = _zoomable_html_fragment(
        container_id=container_id,
        inner_id=inner_id,
        svg=svg,
        zoom_in_id=zoom_in_id,
        zoom_out_id=zoom_out_id,
        reset_id=reset_id,
        fullscreen_id=fullscreen_id,
        container_class="node-graph-knowledge-graph",
        container_style="overflow:auto; position:relative;",
        viewport_style="transform-origin: top left; display:inline-block;",
        controls_class="node-graph-kg-controls",
    )
    return "\n".join(
        [
            "<style>",
            f"  #{container_id}, #{container_id} svg {{ background: #ffffff; }}",
            f"  #{container_id}:fullscreen {{ background: #ffffff; }}",
            "</style>",
            fragment,
        ]
    )


def to_html(kg: Any, *, title: Optional[str] = None) -> str:
    """Return an HTML document embedding the knowledge graph SVG."""
    svg = to_graphviz_svg(kg)
    page_title = title or f"{kg.graph_uuid or 'Graph'} knowledge graph"
    container_id = f"kg-{kg.graph_uuid or uuid4()}"
    inner_id, zoom_in_id, zoom_out_id, reset_id, fullscreen_id = _control_ids(
        container_id
    )
    fragment = _zoomable_html_fragment(
        container_id=container_id,
        inner_id=inner_id,
        svg=svg,
        zoom_in_id=zoom_in_id,
        zoom_out_id=zoom_out_id,
        reset_id=reset_id,
        fullscreen_id=fullscreen_id,
        container_class="kg-container",
        container_style="overflow:auto;",
        viewport_class="kg-viewport",
        controls_class="kg-controls",
    )
    return """<!DOCTYPE html>\n""" + "\n".join(
        [
            '<html lang="en">',
            "  <head>",
            '    <meta charset="utf-8" />',
            f"    <title>{page_title}</title>",
            "    <style>",
            "      body {",
            "        font-family: Helvetica, Arial, sans-serif;",
            "        background-color: #f9f9fb;",
            "        margin: 0;",
            "        padding: 1.5rem;",
            "        color: #212121;",
            "      }",
            "      .container {",
            "        background-color: #ffffff;",
            "        padding: 1.5rem;",
            "        border-radius: 12px;",
            "        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);",
            "        overflow: auto;",
            "        position: relative;",
            "        min-height: 60vh;",
            "      }",
            "      .kg-container { background: #ffffff; }",
            "      .kg-container:fullscreen { background: #ffffff; }",
            "      .kg-container svg { background: #ffffff; }",
            "      h1 {",
            "        font-size: 1.5rem;",
            "        margin-top: 0;",
            "        margin-bottom: 1rem;",
            "      }",
            "      svg {",
            "        height: auto;",
            "      }",
            "      .kg-controls {",
            "        display: flex;",
            "        gap: 0.5rem;",
            "        margin-bottom: 0.75rem;",
            "        flex-wrap: wrap;",
            "      }",
            "      .kg-controls button {",
            "        padding: 0.35rem 0.75rem;",
            "        border-radius: 6px;",
            "        border: 1px solid #e0e0e0;",
            "        background: #fafafa;",
            "        cursor: pointer;",
            "      }",
            "      .kg-controls button:hover {",
            "        background: #f1f1f1;",
            "      }",
            "      .kg-viewport {",
            "        transform-origin: top left;",
            "        display: inline-block;",
            "      }",
            "    </style>",
            "  </head>",
            "  <body>",
            '    <div class="container">',
            f"      <h1>{page_title}</h1>",
            f"      {fragment}",
            "    </div>",
            "  </body>",
            "</html>",
        ]
    )


def save_html(kg: Any, path: str, *, title: Optional[str] = None) -> str:
    """Serialize the HTML view to ``path`` and return the resolved path."""
    html = to_html(kg, title=title)
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(html, encoding="utf-8")
    return str(path_obj)
