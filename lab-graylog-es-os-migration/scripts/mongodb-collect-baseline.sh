#!/usr/bin/env bash

set -o nounset
set -o pipefail

################################################################################
# MongoDB Baseline Collection
################################################################################

readonly SCRIPT_NAME="$(basename "$0")"

readonly EXPECTED_REPLICA_SET="${EXPECTED_REPLICA_SET:-rs0}"
readonly EXPECTED_MEMBERS="${EXPECTED_MEMBERS:-3}"
readonly EXPECTED_SECONDARIES="${EXPECTED_SECONDARIES:-2}"

CHECK_RESULTS=()
FAILED_CHECKS=0

usage() {
    cat <<EOF
Usage:

  Export the MongoDB connection URI:

    export MONGODB_URI="mongodb://gl01:27017,gl02:27017,gl03:27017/admin?replicaSet=rs0"

  Then execute:

    ${SCRIPT_NAME}

Optional environment variables:

    EXPECTED_REPLICA_SET="rs0"
    EXPECTED_MEMBERS="3"
    EXPECTED_SECONDARIES="2"

Example without authentication:

    export MONGODB_URI="mongodb://gl01:27017,gl02:27017,gl03:27017/admin?replicaSet=rs0"

Example with authentication:

    export MONGODB_URI="mongodb://user:password@gl01:27017,gl02:27017,gl03:27017/admin?replicaSet=rs0&authSource=admin"

Description:

  Collects baseline information from a MongoDB Replica Set and validates
  its topology and member health.

Collected information:

  - MongoDB Ping
  - MongoDB Version
  - Replica Set Status
  - Replica Set Configuration
  - Replica Set Validation Summary

EOF
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

banner() {
    cat <<EOF

===============================================================================
 MongoDB Baseline Collection
===============================================================================

Date                     : $(date --iso-8601=seconds)
Expected Replica Set     : ${EXPECTED_REPLICA_SET}
Expected Members         : ${EXPECTED_MEMBERS}
Expected Secondaries     : ${EXPECTED_SECONDARIES}

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

mongodb_eval() {
    local javascript="$1"

    mongosh \
        "${MONGODB_URI}" \
        --quiet \
        --eval "${javascript}"
}

run_mongodb_check() {
    local title="$1"
    local description="$2"
    local javascript="$3"
    local response

    section "${title}"

    if response="$(mongodb_eval "${javascript}")"; then
        printf '%s\n' "${response}" | jq .
        record_ok "${description}"
    else
        echo "Unable to execute MongoDB check." >&2
        record_fail "${description}"
    fi
}

validate_replica_set() {
    local status_json="$1"

    section "5. Replica Set Validation"

    local replica_set_name
    local member_count
    local primary_count
    local secondary_count
    local unhealthy_count

    replica_set_name="$(
        printf '%s\n' "${status_json}" |
            jq --raw-output '.set // empty'
    )"

    member_count="$(
        printf '%s\n' "${status_json}" |
            jq '.members | length'
    )"

    primary_count="$(
        printf '%s\n' "${status_json}" |
            jq '[.members[]? | select(.stateStr == "PRIMARY")] | length'
    )"

    secondary_count="$(
        printf '%s\n' "${status_json}" |
            jq '[.members[]? | select(.stateStr == "SECONDARY")] | length'
    )"

    unhealthy_count="$(
        printf '%s\n' "${status_json}" |
            jq '[.members[]? | select(.health != 1)] | length'
    )"

    echo "Replica Set Name : ${replica_set_name}"
    echo "Members          : ${member_count}"
    echo "Primary          : ${primary_count}"
    echo "Secondaries      : ${secondary_count}"
    echo "Unhealthy Members: ${unhealthy_count}"
    echo

    if [[ "${replica_set_name}" == "${EXPECTED_REPLICA_SET}" ]]; then
        record_ok "Replica Set name is '${EXPECTED_REPLICA_SET}'"
    else
        record_fail \
            "Replica Set name is '${EXPECTED_REPLICA_SET}' (found '${replica_set_name}')"
    fi

    if [[ "${member_count}" -eq "${EXPECTED_MEMBERS}" ]]; then
        record_ok "Replica Set has ${EXPECTED_MEMBERS} members"
    else
        record_fail \
            "Replica Set has ${EXPECTED_MEMBERS} members (found ${member_count})"
    fi

    if [[ "${primary_count}" -eq 1 ]]; then
        record_ok "Replica Set has one PRIMARY"
    else
        record_fail \
            "Replica Set has one PRIMARY (found ${primary_count})"
    fi

    if [[ "${secondary_count}" -eq "${EXPECTED_SECONDARIES}" ]]; then
        record_ok "Replica Set has ${EXPECTED_SECONDARIES} SECONDARY members"
    else
        record_fail \
            "Replica Set has ${EXPECTED_SECONDARIES} SECONDARY members (found ${secondary_count})"
    fi

    if [[ "${unhealthy_count}" -eq 0 ]]; then
        record_ok "All Replica Set members are healthy"
    else
        record_fail \
            "All Replica Set members are healthy (${unhealthy_count} unhealthy)"
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
        echo "MongoDB baseline collection completed successfully."
        return 0
    fi

    echo "MongoDB baseline collection completed with ${FAILED_CHECKS} failure(s)."
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

: "${MONGODB_URI:?MONGODB_URI is not defined.}"

command -v mongosh >/dev/null 2>&1 ||
    die "mongosh is not installed."

command -v jq >/dev/null 2>&1 ||
    die "jq is not installed."

if ! mongodb_eval \
    'EJSON.stringify(db.adminCommand({ ping: 1 }), null, 2)' \
    >/dev/null; then

    die "Unable to connect to MongoDB."
fi

banner

run_mongodb_check \
    "1. MongoDB Ping" \
    "MongoDB connection successful" \
    'EJSON.stringify(db.adminCommand({ ping: 1 }), null, 2)'

run_mongodb_check \
    "2. MongoDB Version" \
    "MongoDB version collected" \
    'EJSON.stringify({ version: db.version() }, null, 2)'
    
REPLICA_SET_STATUS=""

section "3. Replica Set Status"

if REPLICA_SET_STATUS="$(
    mongodb_eval 'EJSON.stringify(rs.status(), null, 2)'
)"; then
    printf '%s\n' "${REPLICA_SET_STATUS}" | jq .
    record_ok "Replica Set status collected"
else
    echo "Unable to retrieve Replica Set status." >&2
    record_fail "Replica Set status collected"
fi

run_mongodb_check \
    "4. Replica Set Configuration" \
    "Replica Set configuration collected" \
    'EJSON.stringify(rs.conf(), null, 2)'

if [[ -n "${REPLICA_SET_STATUS}" ]]; then
    validate_replica_set "${REPLICA_SET_STATUS}"
else
    section "5. Replica Set Validation"
    echo "Validation skipped because Replica Set status could not be collected."
    record_fail "Replica Set topology validated"
fi

summary