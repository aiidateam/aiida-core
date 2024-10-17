#!/bin/bash

set -euo pipefail

# Extract image names together with their sha256 digests
# from the docker/bake-action metadata output.
# These together uniquely identify newly built images.
#
# The input to this script is a JSON string passed via BAKE_METADATA env variable
# Here's example input (trimmed to relevant bits):
# BAKE_METADATA: {
#    "aiida-core-base": {
#      # ...
#      "containerimage.descriptor": {
#        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
#        "digest": "sha256:8e57a52b924b67567314b8ed3c968859cad99ea13521e60bbef40457e16f391d",
#        "size": 6170,
#      },
#      "containerimage.digest": "sha256:8e57a52b924b67567314b8ed3c968859cad99ea13521e60bbef40457e16f391d",
#      "image.name": "ghcr.io/aiidateam/aiida-core-base"
#    },
#    "aiida-core-dev": {
#      "containerimage.digest": "sha256:4d9be090da287fcdf2d4658bb82f78bad791ccd15dac9af594fb8306abe47e97",
#      "...": ...
#      "image.name": "ghcr.io/aiidateam/aiida-core-dev"
#    },
#    "aiida-core-with-services": {
#      "...": ""
#      "containerimage.digest": "sha256:85ee91f61be1ea601591c785db038e5899d68d5fb89e07d66d9efbe8f352ee48",
#      "image.name": "ghcr.io/aiidateam/aiida-core-with-services"
#    },
#    "some-other-key": ...
#  }
#
# Example output (real output is on one line):
#
# images={
#   "AIIDA_CORE_BASE_IMAGE": "ghcr.io/aiidateam/aiida-core-base@sha256:4c402a8bfd635650ad691674f8f29e7ddec5fa656fb425452067950415ee447f",
#   "AIIDA_CORE_DEV_IMAGE": "ghcr.io/aiidateam/aiida-core-dev@sha256:f94c06e47f801e751f9829010b31532039b210aad2649d43205e16c08371b2ed",
#   "AIIDA_CORE_WITH_SERVICES_IMAGE": "ghcr.io/aiidateam/aiida-core-with-services@sha256:bd8272f2a331af7eac3e83c44cc16d23b2e5f601a20ab4a865402659b758515e"
# }
#
# This json output is later turned to environment variables using fromJson() GHA builtin
# (e.g. AIIDA_CORE_BASE_IMAGE=ghcr.io/aiidateam/aiida-core-base@sha256:8e57a52b...)
# and these are in turn read in the docker-compose.<target>.yml files for tests.

if [[ -z ${BAKE_METADATA-} ]];then
    echo "ERROR: Environment variable BAKE_METADATA is not set!"
    exit 1
fi

images=$(echo "${BAKE_METADATA}" |
jq -c 'to_entries | map(select(.key | startswith("aiida"))) | from_entries' | # filters out every key that does not start with aiida
jq -c '. as $base |[to_entries[] |{"key": (.key|ascii_upcase|sub("-"; "_"; "g") + "_IMAGE"), "value": [(.value."image.name"|split(",")[0]),.value."containerimage.digest"]|join("@")}] |from_entries')
echo "images=$images"
