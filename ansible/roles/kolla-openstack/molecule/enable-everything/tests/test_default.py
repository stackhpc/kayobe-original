# Copyright (c) 2018 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import os.path

from kayobe.tests.molecule import utils

import pytest
import testinfra.utils.ansible_runner


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.mark.parametrize(
    'path',
    ['ceph',
     'cinder',
     'designate',
     'fluentd/filter',
     'fluentd/output',
     'glance',
     'grafana',
     'heat',
     'horizon',
     'ironic',
     'keystone',
     'magnum',
     'manila',
     'murano',
     'neutron',
     'nova',
     'sahara',
     'swift',
     'zookeeper'])
def test_service_config_directory(host, path):
    path = os.path.join('/etc/kolla/config', path)
    utils.test_directory(host, path)


@pytest.mark.parametrize(
    'path',
    ['ceph.conf',
     'cinder.conf',
     'designate.conf',
     'glance.conf',
     'grafana.ini',
     'heat.conf',
     'ironic.conf',
     'ironic-inspector.conf',
     'magnum.conf',
     'neutron/ml2_conf.ini',
     'murano.conf',
     'neutron.conf',
     'nova.conf',
     'sahara.conf',
     'zookeeper.cfg'])
def test_service_ini_file(host, path):
    # TODO(mgoddard): Check more of config file contents.
    path = os.path.join('/etc/kolla/config', path)
    extra_section = 'extra-%s' % os.path.basename(path)
    expected = {extra_section: {'foo': 'bar'}}
    utils.test_ini_file(host, path, expected=expected)


@pytest.mark.parametrize(
    'path',
    ['ironic/ironic-agent.initramfs',
     'ironic/ironic-agent.kernel',
     'ironic/ironic-dnsmasq.conf',
     'ironic/pxelinux.default'])
def test_service_non_ini_file(host, path):
    # TODO(mgoddard): Check config file contents.
    path = os.path.join('/etc/kolla/config', path)
    utils.test_file(host, path)
