#!/usr/bin/env bash
# Enforce ADR-001: analytics/ must not import db/api/collection/services/tasks.
set -e
cd "$(dirname "$0")/../backend"
lint-imports
