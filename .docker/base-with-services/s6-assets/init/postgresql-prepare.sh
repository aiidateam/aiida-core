#!/bin/bash

PG_ISREADY=1
while [ "$PG_ISREADY" != "0"  ]; do
  sleep 1
  ${MAMBA_RUN} pg_isready --quiet
  PG_ISREADY=$?
done
