#!/bin/bash -e

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${PARENT}/functions


function main {
    config_init
    environment_setup
}

main
