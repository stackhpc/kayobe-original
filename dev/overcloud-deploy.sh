#!/bin/bash -e

# Simple script to stand up a kayobe development environment in a Vagrant VM.
# This should be executed from within the VM.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${PARENT}/functions


function main {
    config_init
    overcloud_deploy
}

main
