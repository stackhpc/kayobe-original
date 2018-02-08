import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_custom_config_dir(host):
    d = host.file('/etc/kolla/config')

    assert d.exists
    assert d.is_directory
    assert d.user == 'root'
    assert d.group == 'root'


def test_keystone_dir(host):
    d = host.file('/etc/kolla/config/keystone')

    assert d.exists
    assert d.is_directory
    assert d.user == 'root'
    assert d.group == 'root'


def test_fluent_custom_filters(host):
    d = host.file('/etc/kolla/config/fluentd/filter')

    assert d.exists
    assert d.is_directory
    assert d.user == 'root'
    assert d.group == 'root'


def test_fluent_custom_outputs(host):
    d = host.file('/etc/kolla/config/fluentd/output')

    assert d.exists
    assert d.is_directory
    assert d.user == 'root'
    assert d.group == 'root'
