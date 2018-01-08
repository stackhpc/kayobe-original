# Copyright (c) 2017 StackHPC Ltd.
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

import unittest

import cliff.app
import cliff.commandmanager
import mock

from kayobe.cli import commands
from kayobe import utils


class TestApp(cliff.app.App):

    def __init__(self):
        super(TestApp, self).__init__(
            description='Test app',
            version='0.1',
            command_manager=cliff.commandmanager.CommandManager('kayobe.cli'))


class TestCase(unittest.TestCase):

    @mock.patch.object(utils, "galaxy_install", spec=True)
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_control_host_bootstrap(self, mock_run, mock_install):
        command = commands.ControlHostBootstrap(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        mock_install.assert_called_once_with("requirements.yml",
                                             "ansible/roles")
        expected_calls = [
            mock.call(mock.ANY, ["ansible/bootstrap.yml"]),
            mock.call(mock.ANY, ["ansible/kolla-ansible.yml"],
                      tags="install"),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(utils, "galaxy_install", spec=True)
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_control_host_upgrade(self, mock_run, mock_install):
        command = commands.ControlHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        mock_install.assert_called_once_with("requirements.yml",
                                             "ansible/roles", force=True)
        expected_calls = [
            mock.call(mock.ANY, ["ansible/bootstrap.yml"]),
            mock.call(mock.ANY, ["ansible/kolla-ansible.yml"],
                      tags="install"),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_network_connectivity_check(self, mock_run):
        command = commands.NetworkConnectivityCheck(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(mock.ANY, ["ansible/network-connectivity.yml"]),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_configure(self, mock_run):
        command = commands.SeedHypervisorHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/ip-allocation.yml",
                    "ansible/ssh-known-host.yml",
                    "ansible/kayobe-target-venv.yml",
                    "ansible/users.yml",
                    "ansible/yum.yml",
                    "ansible/dev-tools.yml",
                    "ansible/network.yml",
                    "ansible/sysctl.yml",
                    "ansible/ntp.yml",
                    "ansible/seed-hypervisor-libvirt-host.yml",
                ],
                limit="seed-hypervisor",
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_host_configure(self, mock_kolla_run, mock_run, mock_dump):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "seed": {"kayobe_ansible_user": "stack"}
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(mock.ANY, hosts="seed")
        ]
        self.assertEqual(expected_calls, mock_dump.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/ip-allocation.yml",
                    "ansible/ssh-known-host.yml",
                    "ansible/kayobe-ansible-user.yml",
                    "ansible/kayobe-target-venv.yml",
                    "ansible/users.yml",
                    "ansible/yum.yml",
                    "ansible/dev-tools.yml",
                    "ansible/disable-selinux.yml",
                    "ansible/network.yml",
                    "ansible/sysctl.yml",
                    "ansible/ip-routing.yml",
                    "ansible/snat.yml",
                    "ansible/disable-glean.yml",
                    "ansible/ntp.yml",
                    "ansible/lvm.yml",
                ],
                limit="seed",
            ),
            mock.call(
                mock.ANY,
                ["ansible/kolla-ansible.yml"],
                tags="config",
            ),
            mock.call(
                mock.ANY,
                [
                    "ansible/kolla-host.yml",
                    "ansible/docker.yml",
                ],
                limit="seed",
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={"ansible_user": "stack"},
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_host_configure_kayobe_venv(self, mock_kolla_run, mock_run,
                                             mock_dump):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "seed": {
                "ansible_python_interpreter": "/kayobe/venv/bin/python",
                "kayobe_ansible_user": "stack",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/kayobe/venv/bin/python",
                    "ansible_user": "stack",
                },
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_host_configure_kolla_venv(self, mock_kolla_run, mock_run,
                                            mock_dump):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "seed": {
                "kayobe_ansible_user": "stack",
                "kolla_ansible_target_venv": "/kolla/venv/bin/python",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/usr/bin/python",
                    "ansible_user": "stack",
                    "virtualenv": "/kolla/venv/bin/python",
                },
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_host_configure_both_venvs(self, mock_kolla_run, mock_run,
                                            mock_dump):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "seed": {
                "ansible_python_interpreter": "/kayobe/venv/bin/python",
                "kayobe_ansible_user": "stack",
                "kolla_ansible_target_venv": "/kolla/venv/bin/python",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/kayobe/venv/bin/python",
                    "ansible_user": "stack",
                    "virtualenv": "/kolla/venv/bin/python",
                },
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_container_image_build(self, mock_run):
        command = commands.SeedContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/container-image-builders-check.yml",
                    "ansible/kolla-build.yml",
                    "ansible/container-image-build.yml"
                ],
                extra_vars={
                    "container_image_sets": (
                        "{{ seed_container_image_sets }}"),
                    "push_images": False,
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_container_image_build_with_regex(self, mock_run):
        command = commands.SeedContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--push", "^regex1$", "^regex2$"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/container-image-builders-check.yml",
                    "ansible/kolla-build.yml",
                    "ansible/container-image-build.yml"
                ],
                extra_vars={
                    "container_image_regexes": "'^regex1$ ^regex2$'",
                    "push_images": True,
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_host_configure(self, mock_kolla_run, mock_run,
                                      mock_dump):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "controller0": {"kayobe_ansible_user": "stack"}
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(mock.ANY, hosts="overcloud")
        ]
        self.assertEqual(expected_calls, mock_dump.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/ip-allocation.yml",
                    "ansible/ssh-known-host.yml",
                    "ansible/kayobe-ansible-user.yml",
                    "ansible/kayobe-target-venv.yml",
                    "ansible/users.yml",
                    "ansible/yum.yml",
                    "ansible/dev-tools.yml",
                    "ansible/disable-selinux.yml",
                    "ansible/network.yml",
                    "ansible/sysctl.yml",
                    "ansible/disable-glean.yml",
                    "ansible/ntp.yml",
                    "ansible/lvm.yml",
                ],
                limit="overcloud",
            ),
            mock.call(
                mock.ANY,
                ["ansible/kolla-ansible.yml"],
                tags="config",
            ),
            mock.call(
                mock.ANY,
                [
                    "ansible/kolla-host.yml",
                    "ansible/docker.yml",
                ],
                limit="overcloud",
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={"ansible_user": "stack"},
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_host_configure_kayobe_venv(self, mock_kolla_run,
                                                  mock_run, mock_dump):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "controller0": {
                "ansible_python_interpreter": "/kayobe/venv/bin/python",
                "kayobe_ansible_user": "stack",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/kayobe/venv/bin/python",
                    "ansible_user": "stack",
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_host_configure_kolla_venv(self, mock_kolla_run,
                                                 mock_run, mock_dump):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "controller0": {
                "kayobe_ansible_user": "stack",
                "kolla_ansible_target_venv": "/kolla/venv/bin/python",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/usr/bin/python",
                    "ansible_user": "stack",
                    "virtualenv": "/kolla/venv/bin/python",
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_config_dump")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_host_configure_both_venvs(self, mock_kolla_run,
                                                 mock_run, mock_dump):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        mock_dump.return_value = {
            "controller0": {
                "ansible_python_interpreter": "/kayobe/venv/bin/python",
                "kayobe_ansible_user": "stack",
                "kolla_ansible_target_venv": "/kolla/venv/bin/python",
            }
        }

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                "bootstrap-servers",
                extra_vars={
                    "ansible_python_interpreter": "/kayobe/venv/bin/python",
                    "ansible_user": "stack",
                    "virtualenv": "/kolla/venv/bin/python",
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_container_image_build(self, mock_run):
        command = commands.OvercloudContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/container-image-builders-check.yml",
                    "ansible/kolla-build.yml",
                    "ansible/container-image-build.yml"
                ],
                extra_vars={
                    "container_image_sets": (
                        "{{ overcloud_container_image_sets }}"),
                    "push_images": False,
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_container_image_build_with_regex(self, mock_run):
        command = commands.OvercloudContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--push", "^regex1$", "^regex2$"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/container-image-builders-check.yml",
                    "ansible/kolla-build.yml",
                    "ansible/container-image-build.yml"
                ],
                extra_vars={
                    "container_image_regexes": "'^regex1$ ^regex2$'",
                    "push_images": True,
                }
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_inspect(self, mock_run):
        command = commands.BaremetalComputeInspect(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/baremetal-compute-inspect.yml",
                ],
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_manage(self, mock_run):
        command = commands.BaremetalComputeManage(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/baremetal-compute-manage.yml",
                ],
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_provide(self, mock_run):
        command = commands.BaremetalComputeProvide(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    "ansible/baremetal-compute-provide.yml",
                ],
            ),
        ]
        self.assertEqual(expected_calls, mock_run.call_args_list)
