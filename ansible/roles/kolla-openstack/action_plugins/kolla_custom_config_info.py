from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
import os
from collections import defaultdict
import pathlib

from wcmatch import glob

def _dedup(xs):
    # Deduplicate a list whilst maintaining order
    seen = set()
    result = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

class ConfigCollector(object):
    def __init__(self, *args, **kwargs):
        self.files_in_source = defaultdict(list)
        self.files_in_destination = set()
        self.include_globs = kwargs.get("include_globs", [])
        self.ignore_globs = kwargs.get("ignore_globs", [])
        self.merge_ini_globs = kwargs.get("merge_ini_globs", [])
        self.merge_yml_globs = kwargs.get("merge_yml_globs", [])
        self.template_exclude_globs = kwargs.get("template_exclude_globs", [])
        self.destination = kwargs.get("destination", [])
        self.search_paths = kwargs.get("search_paths", [])
        self.collection_has_run_already = False

    def filter_files_in_destination(self):
        ignored = set()
        for f in self.files_in_destination:
            for item in self.ignore_globs:
                if glob.globmatch(f, item, flags=glob.GLOBSTAR):
                    ignored.add(f)
        result = set(self.files_in_destination) - ignored
        # Convert relative paths to absolute
        return {os.path.join(self.destination, x) for x in result }

    def partition_into_actions(self):
        actions = {
            "merge_yaml": [],
            "merge_ini": [],
            "template": [],
            "copy": [],
            "create_dir": [],
            "delete": []
        }
        missing_directories = set()
        files_to_delete = self.filter_files_in_destination()
        for relative_path, sources in self.files_in_source.items():
            found_match = False
            destination = os.path.join(self.destination, relative_path)
            # Don't delete any files we are templating
            files_to_delete.discard(destination)

            dirname = os.path.dirname(destination)
            if not os.path.exists(dirname):
                missing_directories.add(dirname)

            for glob_ in self.template_exclude_globs:
                if glob.globmatch(relative_path, glob_,
                        flags=glob.GLOBSTAR):
                    copy = {
                        "src": sources[0],
                        "dest": destination
                    }
                    actions["copy"].append(copy)
                    found_match = True
                    break

            if found_match:
                continue

            for glob_ in self.merge_yml_globs:
                if glob.globmatch(relative_path, glob_["glob"],
                        flags=glob.GLOBSTAR):
                    merge_yaml = {
                        "sources": sources,
                        "dest": destination
                        # TODO: options
                    }
                    actions["merge_yaml"].append(merge_yaml)
                    found_match = True
                    break

            if found_match:
                continue

            for glob_ in self.merge_ini_globs:
                if glob.globmatch(relative_path, glob_["glob"],
                        flags=glob.GLOBSTAR):
                    merge_ini = {
                        "sources": sources,
                        "dest": destination
                    }
                    actions["merge_ini"].append(merge_ini)
                    found_match = True
                    break

            if found_match:
                continue

            template = {
                "src": sources[0],
                "dest": destination
            }
            actions["template"].append(template)

        actions["create_dir"] = list(missing_directories)
        # Sort by length so that subdirectories are created after the parent
        actions["create_dir"].sort(key=len)

        actions["delete"] = list(files_to_delete)
        return actions

    def collect(self):
        if self.collection_has_run_already:
            return
        for item in self.include_globs:
            self._collect_source(item)
            self._collect_destination(item)
        self.collection_has_run_already = True

    def _collect_source(self, item):
        enabled = item.get("enabled", False)
        if not isinstance(enabled, bool):
            raise ValueError("Expecting a boolean: %s" % item)
        if not enabled:
            return
        for search_path in self.search_paths:
            abs_glob = os.path.join(search_path, item["glob"])
            files = glob.glob(abs_glob, flags=glob.GLOBSTAR)
            for abs_path in files:
                if not os.path.isfile(abs_path):
                    continue
                relative_path = os.path.relpath(abs_path, search_path)
                self.files_in_source[relative_path].append(abs_path)

    def _collect_destination(self, item):
            abs_glob = os.path.join(self.destination, item["glob"])
            files = glob.glob(abs_glob, flags=glob.GLOBSTAR)
            for abs_path in files:
                if not os.path.isfile(abs_path):
                    continue
                relative_path = os.path.relpath(abs_path, self.destination)
                self.files_in_destination.add(relative_path)

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        # This class never changes anything. We only collect the extra config
        # files and group by action.
        result['changed'] = False

        args = self._task.args

        collector = ConfigCollector(
            destination=args.get("destination"),
            ignore_globs=args.get("ignore_globs"),
            include_globs=args.get("include_globs"),
            merge_yml_globs=args.get("merge_yml_globs"),
            merge_ini_globs=args.get("merge_ini_globs"),
            template_exclude_globs=args.get("template_exclude_globs"),
            search_paths=_dedup(args["search_paths"])
        )

        collector.collect()

        result.update(collector.partition_into_actions())

        return result