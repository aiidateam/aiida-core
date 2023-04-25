# -*- coding: utf-8 -*-
"""Doit tasks for building and testing the docker images.
The idea is borrowed from AiiDAlab docker stack.
"""
import json
from pathlib import Path
import platform

import docker  # pylint: disable=import-error
from doit.tools import title_with_actions  # pylint: disable=import-error
from dunamai import Version  # pylint: disable=import-error

_DOCKER_CLIENT = docker.from_env()
_DOCKER_ARCHITECTURE = _DOCKER_CLIENT.info()['Architecture']

DOIT_CONFIG = {'default_tasks': ['build']}

_ARCH_PLATFORM_MAPPING = {
    'aarch64': 'linux/arm64',
    'x86_64': 'linux/amd64',
}

VERSION = Version.from_git().serialize().replace('+', '_')
PLATFORM = _ARCH_PLATFORM_MAPPING.get(_DOCKER_ARCHITECTURE)

if PLATFORM is None:
    raise RuntimeError(f'Unsupported architecture {_DOCKER_ARCHITECTURE} on platform {platform.system()}.')

_REGISTRY_PARAM = {
    'name': 'registry',
    'short': 'r',
    'long': 'registry',
    'type': str,
    'default': '',
    'help': 'Specify the docker image registry.',
}

_VERSION_PARAM = {
    'name': 'version',
    'long': 'version',
    'type': 'str',
    'default': VERSION,
    'help': ('Specify the AiiDA version to build for.',),
}

_AIIDA_VERSION_PARAM = {
    'name': 'aiida_version',
    'long': 'aiida-version',
    'type': 'str',
    'default': '',
    'help': (
        'Specify the version of the stack for building / testing. Defaults to a '
        'version determined from the state of the local git repository.'
    ),
}

_PLATFORM_PARAM = {
    'name': 'platform',
    'long': 'platform',
    'type': str,
    'default': PLATFORM,
    'help': 'Specify the platform to build for. Examples: linux/amd64, linux/arm64',
}


def task_build():
    """Build all docker images."""

    def generate_version_override(version, registry, targets):
        if len(targets) > 2:
            # Workaround of issue of doit, which rather than override the default value, it appends
            # https://github.com/pydoit/doit/issues/436
            targets = targets[2:]
        Path('docker-bake.override.json').write_text(
            json.dumps(dict(VERSION=version, REGISTRY=registry, TARGETS=targets)),
            encoding='utf-8',
        )

    return {
        'actions': [
            generate_version_override,
            'docker buildx bake -f docker-bake.hcl -f build.json '
            '-f docker-bake.override.json '
            "--set '*.platform=%(platform)s' "
            '--load',
        ],
        'title': title_with_actions,
        'params': [
            _REGISTRY_PARAM,
            _VERSION_PARAM,
            _PLATFORM_PARAM,
            _AIIDA_VERSION_PARAM,
            {
                'name': 'targets',
                'long': 'targets',
                'short': 't',
                'type': list,
                'default': ['base', 'base-with-services'],
                'help': 'Specify the target to build.',
            },
        ],
        'verbosity': 2,
    }


def task_tests():
    """Run tests with pytest."""

    return {
        'actions': ['REGISTRY=%(registry)s VERSION=:%(version)s pytest -v'],
        'params': [_REGISTRY_PARAM, _VERSION_PARAM],
        'verbosity': 2,
    }


def task_up():
    """Start AiiDAlab server for testing."""
    return {
        'actions': ['REGISTRY=%(registry)s VERSION=:%(version)s '
                    'docker-compose up --detach'],
        'params': [
            _REGISTRY_PARAM,
            _VERSION_PARAM,
        ],
        'verbosity': 2,
    }


def task_down():
    """Stop AiiDAlab server."""
    return {'actions': ['docker-compose down'], 'verbosity': 2}
