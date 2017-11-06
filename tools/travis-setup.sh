#!/bin/bash

# Script for running a TravisCI job to test use of kayobe.
# Deploys a single host control plane in the job's VM.

set -e

# Clone the development kayobe configuration.
mkdir -p config/src
git clone https://github.com/stackhpc/dev-kayobe-config \
  -b dev-config-mk-1 \
  config/src/kayobe-config

# Use a bridge with no external interfaces.
sed -i \
  -e 's/aio_interface\: breth1/aio_interface: braio/g' \
  -e 's/aio_bridge_ports\:/aio_bridge_ports: []/g' \
  -e '/  \- eth1/d' \
  config/src/kayobe-config/etc/kayobe/inventory/group_vars/controllers/network-interfaces

# Create the bridge, assign it the default development environment IP.
sudo ip l add braio type bridge
sudo ip l set braio up
sudo ip a add 192.168.33.3/24 dev braio

# Generate and authorise an SSH key.
ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys

# Set the bootstrap user to the current user.
sed -i \
  -e "s/controller_bootstrap_user\: vagrant/controller_bootstrap_user: $USER/g" \
  config/src/kayobe-config/etc/kayobe/controllers.yml
