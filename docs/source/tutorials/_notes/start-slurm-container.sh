#!/usr/bin/env bash
#
# Start the xenonmiddleware/slurm:17 container the same way the docs-build
# CI does, and install gsrd inside it so Module 4's live cells can run
# against a real SSH+SLURM target locally (via sphinx-autobuild).
#
# CI equivalent: .github/workflows/docs-build.yml (`services.slurm` block +
# the "Install gsrd on SLURM container" step).
#
# Usage:
#   bash docs/source/tutorials/_notes/start-slurm-container.sh
#
# Then run `sphinx-autobuild docs/source docs/html` from the repo root.
# When done:
#   docker stop slurm-ssh

set -euo pipefail

CONTAINER_NAME=slurm-ssh
HOST_PORT=5001

# 1. Start the container (idempotent: skip if already running).
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Container '${CONTAINER_NAME}' is already running."
else
    if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
        # Stopped container with the same name; remove it before re-creating.
        docker rm "${CONTAINER_NAME}"
    fi
    echo "Starting xenonmiddleware/slurm:17 as '${CONTAINER_NAME}' on port ${HOST_PORT}..."
    docker run -d --rm \
        -p "${HOST_PORT}:22" \
        --name "${CONTAINER_NAME}" \
        xenonmiddleware/slurm:17
fi

# 2. Install gsrd inside the container, exactly mirroring CI's install step.
# Skip if already installed (idempotent across reruns).
if docker exec "${CONTAINER_NAME}" test -x /opt/gsrd/bin/gsrd; then
    echo "gsrd already installed in ${CONTAINER_NAME}."
else
    echo "Installing gsrd in ${CONTAINER_NAME} via uv..."
    # Copy the host's `uv` binary into the container (matches CI's docker cp).
    UV_HOST="$(readlink -f "$(which uv)")"
    docker cp "${UV_HOST}" "${CONTAINER_NAME}:/usr/local/bin/uv"
    docker exec "${CONTAINER_NAME}" bash -c "
        export UV_PYTHON_INSTALL_DIR=/opt/uv-python && \
        uv venv /opt/gsrd --python 3.12 && \
        uv pip install --python /opt/gsrd/bin/python --only-binary numpy \
            'gsrd @ https://github.com/aiidateam/gsrd/archive/refs/heads/main.zip' && \
        chmod -R a+rX /opt/gsrd /opt/uv-python
    "
fi

# 3. Sanity check.
echo
echo "Container status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo
echo "gsrd binary:"
docker exec "${CONTAINER_NAME}" ls -l /opt/gsrd/bin/gsrd
echo
echo "Done. Now run:  sphinx-autobuild docs/source docs/html"
echo "When finished:  docker stop ${CONTAINER_NAME}"
