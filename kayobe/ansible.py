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

import logging
import os
import os.path
import shutil
import subprocess
import sys
import tempfile

from kayobe import utils
from kayobe import vault


DEFAULT_CONFIG_PATH = "/etc/kayobe"

CONFIG_PATH_ENV = "KAYOBE_CONFIG_PATH"

LOG = logging.getLogger(__name__)


def add_args(parser):
    """Add arguments required for running Ansible playbooks to a parser."""
    default_config_path = os.getenv(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH)
    parser.add_argument("-b", "--become", action="store_true",
                        help="run operations with become (nopasswd implied)")
    parser.add_argument("-C", "--check", action="store_true",
                        help="don't make any changes; instead, try to predict "
                             "some of the changes that may occur")
    parser.add_argument("--config-path", default=default_config_path,
                        help="path to Kayobe configuration. "
                             "(default=$%s or %s)" %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-e", "--extra-vars", metavar="EXTRA_VARS",
                        action="append",
                        help="set additional variables as key=value or "
                             "YAML/JSON")
    parser.add_argument("-i", "--inventory", metavar="INVENTORY",
                        help="specify inventory host path "
                             "(default=$%s/inventory or %s/inventory) or "
                             "comma-separated host list" %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-l", "--limit", metavar="SUBSET",
                        help="further limit selected hosts to an additional "
                             "pattern")
    parser.add_argument("--skip-tags", metavar="TAGS",
                        help="only run plays and tasks whose tags do not match"
                             "these values")
    parser.add_argument("-t", "--tags", metavar="TAGS",
                        help="only run plays and tasks tagged with these "
                             "values")
    parser.add_argument("-lt", "--list-tasks",
                        action="store_true",
                        help="only print names of tasks, don't run them, "
                             "note this has no affect on kolla-ansible.")


def _get_inventory_path(parsed_args):
    """Return the path to the Kayobe inventory."""
    if parsed_args.inventory:
        return parsed_args.inventory
    else:
        return os.path.join(parsed_args.config_path, "inventory")


def _validate_args(parsed_args, playbooks):
    """Validate Kayobe Ansible arguments."""
    result = utils.is_readable_dir(parsed_args.config_path)
    if not result["result"]:
        LOG.error("Kayobe configuration path %s is invalid: %s",
                  parsed_args.config_path, result["message"])
        sys.exit(1)

    inventory = _get_inventory_path(parsed_args)
    result = utils.is_readable_dir(inventory)
    if not result["result"]:
        LOG.error("Kayobe inventory %s is invalid: %s",
                  inventory, result["message"])
        sys.exit(1)

    for playbook in playbooks:
        result = utils.is_readable_file(playbook)
        if not result["result"]:
            LOG.error("Kayobe playbook %s is invalid: %s",
                      playbook, result["message"])
            sys.exit(1)


def _get_vars_files(config_path):
    """Return a list of Kayobe Ansible configuration variable files."""
    vars_files = []
    for vars_file in os.listdir(config_path):
        abs_path = os.path.join(config_path, vars_file)
        if utils.is_readable_file(abs_path):
            root, ext = os.path.splitext(vars_file)
            if ext in (".yml", ".yaml", ".json"):
                vars_files.append(abs_path)
    return vars_files


def build_args(parsed_args, playbooks,
               extra_vars=None, limit=None, tags=None, verbose_level=None,
               check=None):
    """Build arguments required for running Ansible playbooks."""
    cmd = ["ansible-playbook"]
    if verbose_level:
        cmd += ["-" + "v" * verbose_level]
    if parsed_args.list_tasks:
        cmd += ["--list-tasks"]
    cmd += vault.build_args(parsed_args)
    inventory = _get_inventory_path(parsed_args)
    cmd += ["--inventory", inventory]
    vars_files = _get_vars_files(parsed_args.config_path)
    for vars_file in vars_files:
        cmd += ["-e", "@%s" % vars_file]
    if parsed_args.extra_vars:
        for extra_var in parsed_args.extra_vars:
            cmd += ["-e", extra_var]
    if extra_vars:
        for extra_var_name, extra_var_value in extra_vars.items():
            cmd += ["-e", "%s=%s" % (extra_var_name, extra_var_value)]
    if parsed_args.become:
        cmd += ["--become"]
    if check or (parsed_args.check and check is None):
        cmd += ["--check"]
    if parsed_args.limit or limit:
        limits = [l for l in [parsed_args.limit, limit] if l]
        cmd += ["--limit", ":&".join(limits)]
    if parsed_args.skip_tags:
        cmd += ["--skip-tags", parsed_args.skip_tags]
    if parsed_args.tags or tags:
        all_tags = [t for t in [parsed_args.tags, tags] if t]
        cmd += ["--tags", ",".join(all_tags)]
    cmd += playbooks
    return cmd


def run_playbooks(parsed_args, playbooks,
                  extra_vars=None, limit=None, tags=None, quiet=False,
                  verbose_level=None, check=None):
    """Run a Kayobe Ansible playbook."""
    _validate_args(parsed_args, playbooks)
    cmd = build_args(parsed_args, playbooks,
                     extra_vars=extra_vars, limit=limit, tags=tags,
                     verbose_level=verbose_level, check=check)
    try:
        utils.run_command(cmd, quiet=quiet)
    except subprocess.CalledProcessError as e:
        LOG.error("Kayobe playbook(s) %s exited %d",
                  ", ".join(playbooks), e.returncode)
        sys.exit(e.returncode)


def run_playbook(parsed_args, playbook, *args, **kwargs):
    """Run a Kayobe Ansible playbook."""
    return run_playbooks(parsed_args, [playbook], *args, **kwargs)


def config_dump(parsed_args, host=None, hosts=None, var_name=None,
                facts=None, extra_vars=None, tags=None, verbose_level=None):
    dump_dir = tempfile.mkdtemp()
    try:
        if not extra_vars:
            extra_vars = {}
        extra_vars["dump_path"] = dump_dir
        if host or hosts:
            extra_vars["dump_hosts"] = host or hosts
        if var_name:
            extra_vars["dump_var_name"] = var_name
        if facts is not None:
            extra_vars["dump_facts"] = facts
        # Don't use check mode for configuration dumps as we won't get any
        # results back.
        run_playbook(parsed_args, "ansible/dump-config.yml",
                     extra_vars=extra_vars, tags=tags, quiet=True,
                     verbose_level=verbose_level, check=False)
        hostvars = {}
        for path in os.listdir(dump_dir):
            LOG.debug("Found dump file %s", path)
            inventory_hostname, ext = os.path.splitext(path)
            if ext == ".yml":
                hvars = utils.read_yaml_file(os.path.join(dump_dir, path))
                if host:
                    return hvars
                else:
                    hostvars[inventory_hostname] = hvars
            else:
                LOG.warning("Unexpected extension on config dump file %s",
                            path)
        return hostvars
    finally:
        shutil.rmtree(dump_dir)
