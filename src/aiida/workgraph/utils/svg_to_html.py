def svg_to_html(svg_xml: str, width: str = '100%', height: str = '100%') -> str:
    """
    Converts an SVG XML string into an HTML string with embedded SVG,
    scaled to the specified width and height using CSS and includes functionality
    for panning and zooming the SVG based on the mouse point.
    """
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interactive SVG Viewer</title>
        <style>
            svg {{
                width: {width};
                height: {height};
                cursor: grab;
            }}
            svg:active {{
                cursor: grabbing;
            }}
            #fullscreen-btn {{
                padding: 5px 10px;
            }}
            #fullscreen-btn:hover {{
                background-color: #0056b3;
                color: white;
            }}
        </style>
    </head>
    <body>
        <button id="fullscreen-btn">Fullscreen</button>
        {svg_xml}
        <script>
            const svgElement = document.querySelector('svg');
            let isPanning = false;
            let startPoint = {{x: 0, y: 0}};
            let translate = {{x: 0, y: 0}};
            let scale = 1;

            // Enable panning
            svgElement.addEventListener('mousedown', (e) => {{
                isPanning = true;
                startPoint = {{x: e.clientX - translate.x, y: e.clientY - translate.y}};
                svgElement.style.cursor = 'grabbing';
            }});

            window.addEventListener('mouseup', () => {{
                isPanning = false;
                svgElement.style.cursor = 'grab';
            }});

            window.addEventListener('mousemove', (e) => {{
                if (isPanning) {{
                    translate.x = e.clientX - startPoint.x;
                    translate.y = e.clientY - startPoint.y;
                    updateTransform();
                }}
            }});

            // Enable zooming
            svgElement.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const mouseX = e.clientX;
                const mouseY = e.clientY;
                const scaleFactor = 1.03;
                if (e.deltaY < 0) {{
                    // Zoom in
                    scale *= scaleFactor;
                }} else {{
                    // Zoom out
                    scale /= scaleFactor;
                }}
                translate.x -= mouseX * (scaleFactor - 1) * (e.deltaY < 0 ? 1 : -1);
                translate.y -= mouseY * (scaleFactor - 1) * (e.deltaY < 0 ? 1 : -1);
                updateTransform();
            }});

            function updateTransform() {{
                svgElement.style.transform = `translate(${{translate.x}}px, ${{translate.y}}px) scale(${{scale}})`;
            }}

            // Fullscreen toggle
            const fullscreenButton = document.getElementById('fullscreen-btn');
            fullscreenButton.addEventListener('click', () => {{
                if (!document.fullscreenElement) {{
                    svgElement.requestFullscreen().catch(err => {{
                        alert(`Error attempting to enable full-screen mode: ${{err.message}} (${{err.name}})`);
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_template
