#!/bin/bash

set -euo pipefail

# Extract image names together with their digests
# to uniquely identify newly built images in subsequent steps.

# TODO: Make these examples specific to aiida-core
#
# The input to this script is a JSON string passed via BAKE_METADATA env variable
# Here's example input (trimmed to relevant bits):
# BAKE_META: {
#    "base": {
#      "buildx.build.ref": "builder-9dc30f03-42f5-4fd5-8c9a-0d54be5ad996/builder-9dc30f03-42f5-4fd5-8c9a-0d54be5ad9960/jex1w6zvslbbomtkedn4no62l",
#      "containerimage.config.digest": "sha256:b76dc61672dd0efbd586d56393d3a57f6309654e6903d738168892bc09017e8b",
#      "containerimage.descriptor": {
#        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
#        "digest": "sha256:8e57a52b924b67567314b8ed3c968859cad99ea13521e60bbef40457e16f391d",
#        "size": 6170,
#        "platform": {
#          "architecture": "amd64",
#          "os": "linux"
#        }
#      },
#      "containerimage.digest": "sha256:8e57a52b924b67567314b8ed3c968859cad99ea13521e60bbef40457e16f391d",
#      "image.name": "ghcr.io/aiidalab/base:pr-439,ghcr.io/aiidalab/base:sha-a0cd2be"
#    },
#    "base-with-services": {
#       "containerimage.digest": "sha256:6753a809b5b2675bf4c22408e07c1df155907a465b33c369ef93ebcb1c4fec26",
#       "...": ""
#    }
#    "full-stack": {
#       "containerimage.digest": "sha256:85ee91f61be1ea601591c785db038e5899d68d5fb89e07d66d9efbe8f352ee48",
#       "...": ""
#    }
#  }
#
# Example output (real output is on one line):
#
# images={
#   "BASE_IMAGE":"ghcr.io/aiidalab/base:pr-439@sha256:8e57a52b924b67567314b8ed3c968859cad99ea13521e60bbef40457e16f391d",
#   "BASE_WITH_SERVICES_IMAGE":"ghcr.io/aiidalab/base-with-services:pr-439@sha256:6753a809b5b2675bf4c22408e07c1df155907a465b33c369ef93ebcb1c4fec26",
#   "FULL_STACK_IMAGE":"ghcr.io/aiidalab/full-stack:pr-439@sha256:85ee91f61be1ea601591c785db038e5899d68d5fb89e07d66d9efbe8f352ee48",
#   "LAB_IMAGE":"ghcr.io/aiidalab/lab:pr-439@sha256:4d9be090da287fcdf2d4658bb82f78bad791ccd15dac9af594fb8306abe47e97"
# }

if [[ -z ${BAKE_METADATA-} ]];then
    echo "ERROR: Environment variable BAKE_METADATA is not set!"
    exit 1
fi

images=$(echo "${BAKE_METADATA}" | jq -c '. as $base |[to_entries[] |{"key": (.key|ascii_upcase|sub("-"; "_"; "g") + "_IMAGE"), "value": [(.value."image.name"|split(",")[0]),.value."containerimage.digest"]|join("@")}] |from_entries')
echo "images=$images"
