#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

################################################################################
# Elasticsearch Baseline Collection
################################################################################

readonly SCRIPT_NAME="$(basename "$0")"

CHECK_RESULTS=()

usage() {
cat <<EOF
Usage:

  ${SCRIPT_NAME} <elasticsearch-url>

Example:

  ${SCRIPT_NAME} http://es01:9200

Description:

  Collect baseline information from an Elasticsearch cluster.

Collected information:

  - Cluster Health
  - Nodes
  - Indices
  - Aliases
  - Cluster Stats

EOF
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

banner() {
cat <<EOF

===============================================================================
 Elasticsearch Baseline Collection
===============================================================================

Endpoint : ${ENDPOINT}
Date     : $(date --iso-8601=seconds)

EOF
}

section() {
    echo
    echo "-------------------------------------------------------------------------------"
    echo "$1"
    echo "-------------------------------------------------------------------------------"
}

run_check() {

    local title="$1"
    local url="$2"

    section "$title"

    if curl --silent --fail "${url}"; then
        CHECK_RESULTS+=("[OK] ${title}")
    else
        CHECK_RESULTS+=("[FAIL] ${title}")
        return 1
    fi
}

summary() {

    echo
    echo "==============================================================================="
    echo " Validation Summary"
    echo "==============================================================================="

    for result in "${CHECK_RESULTS[@]}"; do
        echo "${result}"
    done

    echo
    echo "Baseline collection completed successfully."
}

################################################################################

[[ $# -eq 1 ]] || {
    usage
    exit 1
}

[[ "$1" == "-h" || "$1" == "--help" ]] && {
    usage
    exit 0
}

ENDPOINT="${1%/}"

command -v curl >/dev/null || die "curl is not installed."

curl --silent --fail "${ENDPOINT}" >/dev/null \
    || die "Unable to connect to ${ENDPOINT}"

banner

run_check "1. Cluster Health" "${ENDPOINT}/_cluster/health?pretty"

run_check "2. Nodes" "${ENDPOINT}/_cat/nodes?v"

run_check "3. Indices" "${ENDPOINT}/_cat/indices?v"

run_check "4. Aliases" "${ENDPOINT}/_cat/aliases?v"

run_check "5. Cluster Stats" "${ENDPOINT}/_cluster/stats?pretty"

summary