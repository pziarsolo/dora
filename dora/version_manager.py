#!/usr/bin/env python3
#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#

# import os
import subprocess
import sys
from pathlib import Path


class VersionManager:
    # version_fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '__version__.py')
    version_path = Path(__file__).parent / '__version__.py'
    path = Path(__file__).parent.absolute()

    def _run_git_command(self, args):
        prefix = ['git', '-C', self.path]
        try:
            return subprocess.check_output(prefix + args).decode().strip()
        except subprocess.CalledProcessError:
            return None

    def get_git_version(self):
        git_version = self._run_git_command(['describe', '--tags', '--dirty=.dirty'])
        # git_version = self._run_git_command(['describe', '--tags'])
        return git_version

    def get_file_version(self):
        with self.version_path.open() as fhand:
            return fhand.readline().strip()

    @property
    def version(self):
        git_version = self.get_git_version()
        file_version = self.get_file_version()
        if git_version != file_version:
            self.version = git_version
        return git_version

    @version.setter
    def version(self, new_version):
        with open(self.version_path, 'w') as fhand:
            fhand.write(f'{new_version}\n')
            fhand.flush()

    def update_version(self, pre_commit=True):
        git_version = self.get_git_version()
        self.version = git_version
        # items = git_version.split('-')
        #
        # if pre_commit:
        #     git_version = items[0][1:]
        #     commit_num = int(items[1]) + 1
        #     git_version += f'.dev{commit_num}'
        # else:
        #     git_version = git_version.replace('-', '.dev', 1).replace('-', '+')[1:]
        # self.version = git_version


if __name__ == '__main__':
    if sys.argv[1] == 'update_version':
        manager = VersionManager()
        manager.update_version(pre_commit=True)
