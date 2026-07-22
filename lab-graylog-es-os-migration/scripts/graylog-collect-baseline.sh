#!/usr/bin/env bash

set -o nounset
set -o pipefail

################################################################################
# Graylog Baseline Collection
################################################################################

readonly SCRIPT_NAME="$(basename "$0")"

readonly EXPECTED_INDEX_SET="${EXPECTED_INDEX_SET:-Migration Test}"
readonly EXPECTED_STREAM="${EXPECTED_STREAM:-Migration Test}"

CHECK_RESULTS=()
FAILED_CHECKS=0

usage() {
    cat <<EOF
Usage:

  Export the Graylog URL and API token:

    export GRAYLOG_URL="http://gl01:9000"
    export GRAYLOG_TOKEN="<api-token>"

  Then execute:

    ${SCRIPT_NAME}

Optional environment variables:

    EXPECTED_INDEX_SET="Migration Test"
    EXPECTED_STREAM="Migration Test"

Example:

    GRAYLOG_URL="http://gl01:9000" \\
    GRAYLOG_TOKEN="<api-token>" \\
    ${SCRIPT_NAME}

Description:

  Collects baseline information from Graylog and validates that the
  migration test Index Set and Stream exist.

Collected information:

  - Graylog System Overview
  - Cluster Nodes
  - Indexer Overview
  - Index Sets
  - Streams
  - Validation Summary

EOF
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

banner() {
    cat <<EOF

===============================================================================
 Graylog Baseline Collection
===============================================================================

Endpoint           : ${GRAYLOG_API_URL}
Date               : $(date --iso-8601=seconds)
Expected Index Set : ${EXPECTED_INDEX_SET}
Expected Stream    : ${EXPECTED_STREAM}

EOF
}

section() {
    echo
    echo "-------------------------------------------------------------------------------"
    echo "$1"
    echo "-------------------------------------------------------------------------------"
}

record_ok() {
    CHECK_RESULTS+=("[OK] $1")
}

record_fail() {
    CHECK_RESULTS+=("[FAIL] $1")
    ((FAILED_CHECKS += 1))
}

api_get() {
    local path="$1"

    curl \
        --silent \
        --show-error \
        --fail \
        --user "${GRAYLOG_TOKEN}:token" \
        --header "Accept: application/json" \
        --header "X-Requested-By: ${SCRIPT_NAME}" \
        "${GRAYLOG_API_URL}${path}"
}

run_api_check() {
    local title="$1"
    local description="$2"
    local path="$3"
    local response

    section "${title}"

    if response="$(api_get "${path}")"; then
        printf '%s\n' "${response}" | jq .
        record_ok "${description}"
    else
        echo "Unable to retrieve ${path}" >&2
        record_fail "${description}"
    fi
}

validate_named_resource() {
    local title="$1"
    local resource_type="$2"
    local expected_name="$3"
    local path="$4"
    local jq_filter="$5"
    local response

    section "${title}"

    if ! response="$(api_get "${path}")"; then
        echo "Unable to retrieve ${path}" >&2
        record_fail "${resource_type} list collected"
        record_fail "${resource_type} '${expected_name}' found"
        return
    fi

    printf '%s\n' "${response}" | jq .
    record_ok "${resource_type} list collected"

    if printf '%s\n' "${response}" |
        jq --exit-status \
            --arg expected "${expected_name}" \
            "${jq_filter}" >/dev/null; then

        record_ok "${resource_type} '${expected_name}' found"
    else
        echo
        echo "${resource_type} not found: ${expected_name}" >&2
        record_fail "${resource_type} '${expected_name}' found"
    fi
}

summary() {
    echo
    echo "==============================================================================="
    echo " Validation Summary"
    echo "==============================================================================="

    local result

    for result in "${CHECK_RESULTS[@]}"; do
        echo "${result}"
    done

    echo

    if ((FAILED_CHECKS == 0)); then
        echo "Graylog baseline collection completed successfully."
        return 0
    fi

    echo "Graylog baseline collection completed with ${FAILED_CHECKS} failure(s)."
    return 1
}

################################################################################
# Main
################################################################################

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

[[ $# -eq 0 ]] || {
    usage
    exit 1
}

: "${GRAYLOG_URL:?GRAYLOG_URL is not defined.}"
: "${GRAYLOG_TOKEN:?GRAYLOG_TOKEN is not defined.}"

command -v curl >/dev/null 2>&1 ||
    die "curl is not installed."

command -v jq >/dev/null 2>&1 ||
    die "jq is not installed."

GRAYLOG_API_URL="${GRAYLOG_URL%/}"

if [[ "${GRAYLOG_API_URL}" != */api ]]; then
    GRAYLOG_API_URL="${GRAYLOG_API_URL}/api"
fi

if ! api_get "/system" >/dev/null; then
    die "Unable to authenticate or connect to ${GRAYLOG_API_URL}"
fi

banner

run_api_check \
    "1. Graylog System Overview" \
    "Graylog system overview collected" \
    "/system"

run_api_check \
    "2. Cluster Nodes" \
    "Graylog cluster nodes collected" \
    "/cluster"

run_api_check \
    "3. Indexer Overview" \
    "Graylog indexer overview collected" \
    "/system/indexer/overview"

validate_named_resource \
    "4. Index Sets" \
    "Index Set" \
    "${EXPECTED_INDEX_SET}" \
    "/system/indices/index_sets" \
    '.index_sets[]? | select(.title == $expected)'

validate_named_resource \
    "5. Streams" \
    "Stream" \
    "${EXPECTED_STREAM}" \
    "/streams" \
    '.streams[]? | select(.title == $expected)'

summary