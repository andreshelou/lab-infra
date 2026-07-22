#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

################################################################################
# Functions
################################################################################

usage() {
cat <<EOF

Graylog Migration Laboratory
Test Data Generator

Usage:
    $(basename "$0") <graylog_host> <port>

Arguments:

    graylog_host    Graylog hostname or IP address.
    port            Syslog UDP port.

Example:

    $(basename "$0") gl01 1514
    $(basename "$0") 192.168.1.100 1514

EOF
}

banner() {

cat <<EOF
============================================================
 Graylog Migration Laboratory
 Test Data Generator
============================================================

Target Host : ${GRAYLOG_HOST}
Target Port : ${GRAYLOG_PORT}
Hostname    : ${HOSTNAME}
Interval    : ${INTERVAL} second(s)

Press CTRL+C to stop.

EOF

}

cleanup() {

echo
echo "Stopping generator..."
exit 0

}

################################################################################
# Main
################################################################################

[[ $# -eq 1 && ( "$1" == "-h" || "$1" == "--help" ) ]] && {
    usage
    exit 0
}

if [[ $# -ne 2 ]]; then
    echo "Error: Missing required arguments." >&2
    usage
    exit 1
fi

readonly GRAYLOG_HOST="$1"
readonly GRAYLOG_PORT="$2"

readonly INTERVAL=1

SEQUENCE=1

trap cleanup SIGINT

banner

while true
do

    MESSAGE="LAB-MIGRATION sequence=${SEQUENCE} hostname=${HOSTNAME} timestamp=$(date --iso-8601=seconds)"

    logger \
        -n "${GRAYLOG_HOST}" \
        -P "${GRAYLOG_PORT}" \
        "${MESSAGE}"

    printf "%08d sent\r" "${SEQUENCE}"

    ((SEQUENCE++))

    sleep "${INTERVAL}"

done