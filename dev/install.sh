#!/bin/bash -e

# Install kayobe and its dependencies in a virtual environment.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${PARENT}/functions


function main {
    config_init
    install_dependencies
    install_venv
}

main
