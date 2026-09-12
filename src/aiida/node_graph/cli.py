"""node-graph unified CLI (pluggable via ``node_graph.cli`` entry points) using Click."""

from __future__ import annotations

import click

try:
    from importlib.metadata import entry_points
except Exception:  # pragma: no cover - fallback for older Python
    from importlib_metadata import entry_points  # type: ignore


def _load_plugin_commands() -> list[tuple[click.Command, str]]:
    """Load click commands registered under the ``node_graph.cli`` entry point group."""

    try:
        eps = entry_points()
        eps_group = eps.get("node_graph.cli", []) if hasattr(eps, "get") else []
        if not eps_group:  # importlib.metadata newer API
            eps_group = entry_points(group="node_graph.cli")
    except Exception:
        eps_group = []
    commands: list[tuple[click.Command, str]] = []
    for ep in eps_group:
        try:
            cmd = ep.load()
            if isinstance(cmd, click.Command):
                # Register under the entry point name to allow short aliases (e.g., kg).
                commands.append((cmd, getattr(ep, "name", cmd.name or "")))
            else:
                click.echo(
                    f"CLI plugin {getattr(ep, 'name', ep)} did not return a click.Command; skipping.",
                    err=True,
                )
        except Exception as exc:
            click.echo(
                f"CLI plugin {getattr(ep, 'name', ep)} failed to load: {exc}",
                err=True,
            )
    return commands


class AliasGroup(click.Group):
    """Click group that supports aliases without listing them separately."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._aliases: dict[str, str] = {}

    def add_command(
        self,
        cmd: click.Command,
        name: str | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        canonical = name or cmd.name
        super().add_command(cmd, name=canonical)
        for alias in aliases or []:
            if alias and alias != canonical:
                self._aliases[alias] = canonical

    def get_command(self, ctx, cmd_name):
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        canonical = self._aliases.get(cmd_name)
        if canonical:
            return super().get_command(ctx, canonical)
        return None

    def list_commands(self, ctx):
        return super().list_commands(ctx)


@click.group(cls=AliasGroup)
def cli() -> None:
    """node-graph CLI."""


_plugins: dict[str, dict[str, object]] = {}
for command, alias in _load_plugin_commands():
    canonical = command.name or alias
    if canonical is None:
        continue
    entry = _plugins.get(canonical, {"cmd": command, "aliases": set()})
    entry["cmd"] = command
    if alias and alias != canonical:
        entry["aliases"].add(alias)
    _plugins[canonical] = entry

for canonical, meta in _plugins.items():
    cli.add_command(meta["cmd"], name=canonical, aliases=sorted(meta["aliases"]))  # type: ignore[arg-type]


def main(argv: list[str] | None = None) -> int:
    """Entry point for legacy script wiring."""

    try:
        cli.main(args=argv, prog_name="node-graph", standalone_mode=False)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
