import json
import platform
from pathlib import Path

from doit.tools import title_with_actions

import docker
from dunamai import Version

_DOCKER_CLIENT = docker.from_env()
_DOCKER_ARCHITECTURE = _DOCKER_CLIENT.info()["Architecture"]

DOIT_CONFIG = {"default_tasks": ["build"]}

VERSION = Version.from_git().serialize().replace("+", "_")

_ARCH_MAPPING = {
    "x86_64": "amd64",
    "aarch64": "arm64",
}

ARCH = _ARCH_MAPPING.get(_DOCKER_ARCHITECTURE)

if ARCH is None:
    raise RuntimeError(
        f"Unsupported architecture {ARCH} on platform {platform.system()}."
    )

_REGISTRY_PARAM = {
    "name": "registry",
    "short": "r",
    "long": "registry",
    "type": str,
    "default": "",
    "help": "Specify the docker image registry.",
}

_ORGANIZATION_PARAM = {
    "name": "organization",
    "short": "o",
    "long": "organization",
    "type": str,
    "default": "aiidalab",
    "help": "Specify the docker image organization.",
}

_VERSION_PARAM = {
    "name": "version",
    "long": "version",
    "type": str,
    "default": VERSION,
    "help": (
        "Specify the version of the stack for building / testing. Defaults to a "
        "version determined from the state of the local git repository."
    ),
}

_ARCH_PARAM = {
    "name": "architecture",
    "long": "arch",
    "type": str,
    "default": ARCH,
    "help": "Specify the platform to build for. Examples: arm64, amd64.",
}


def task_build():
    """Build all docker images."""

    def generate_version_override(
        version, registry, targets, architecture, organization
    ):
        if len(targets) > 2:
            # Workaround of issue of doit, which rather than override the default value, it appends
            # https://github.com/pydoit/doit/issues/436
            targets = targets[2:]

        platforms = [f"linux/{architecture}"]

        Path("docker-bake.override.json").write_text(
            json.dumps(
                dict(
                    VERSION=version,
                    REGISTRY=registry,
                    TARGETS=targets,
                    ORGANIZATION=organization,
                    PLATFORMS=platforms,
                )
            )
        )

    return {
        "actions": [
            generate_version_override,
            "docker buildx bake -f docker-bake.hcl -f build.json "
            "-f docker-bake.override.json "
            "--load",
        ],
        "title": title_with_actions,
        "params": [
            _ORGANIZATION_PARAM,
            _REGISTRY_PARAM,
            _VERSION_PARAM,
            _ARCH_PARAM,
            {
                "name": "targets",
                "long": "targets",
                "short": "t",
                "type": list,
                "default": ["base", "base-with-services"],
                "help": "Specify the target to build.",
            },
        ],
        "verbosity": 2,
    }


def task_tests():
    """Run tests with pytest."""

    return {
        "actions": ["REGISTRY=%(registry)s VERSION=:%(version)s pytest -v"],
        "params": [_REGISTRY_PARAM, _VERSION_PARAM],
        "verbosity": 2,
    }


def task_up():
    """Start AiiDAlab server for testing."""
    return {
        "actions": [
            "AIIDALAB_PORT=%(port)i REGISTRY=%(registry)s VERSION=%(version)s "
            "docker-compose -f docker-compose.%(target)s.yml up"
        ],
        "params": [
            {
                "name": "port",
                "short": "p",
                "long": "port",
                "type": int,
                "default": 8888,
                "help": "Specify the AiiDAlab host port.",
            },
            {
                "name": "target",
                "short": "t",
                "long": "target",
                "type": str,
                "default": "base-with-services",
                "help": "Specify the target to run.",   
            },
            _REGISTRY_PARAM,
            _VERSION_PARAM,
        ],
        "verbosity": 2,
    }


def task_down():
   """Stop AiiDAlab server."""
   return {"actions": ["docker-compose down"], "verbosity": 2}