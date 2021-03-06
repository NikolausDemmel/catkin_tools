# Copyright 2014 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module implements a class for representing a catkin workspace context"""

from __future__ import print_function

import os

from .color import clr

from .common import remove_ansi_escape


# TODO: extend builtin prototype to handle locking
class Context(object):
    """Encapsulates a catkin workspace's settings which affect build results.

    This class will validate some of the settings on assignment using the
    filesystem, but it will never modify the filesystem. For instance, it will
    raise an exception if the source space does not exist, but it will not
    create a folder for the build space if it does not already exist.

    This context can be locked, so that changing the members is prevented.
    """
    def __init__(
        self,
        workspace=None,
        source_space=None,
        build_space=None,
        devel_space=None,
        install_space=None,
        isolate_devel=False,
        install=False,
        isolate_install=False,
        cmake_args=None,
        make_args=None,
        catkin_make_args=None,
        space_suffix=None
    ):
        """Creates a new Context object, optionally initializing with parameters

        :param workspace: root of the workspace, defaults to '.'
        :type workspace: str
        :param source_space: location of source space, defaults to '<workspace>/src'
        :type source_space: str
        :param build_space: target location of build space, defaults to '<workspace>/build'
        :type build_space: str
        :param devel_space: target location of devel space, defaults to '<workspace>/devel'
        :type devel_space: str
        :param install_space: target location of install space, defaults to '<workspace>/install'
        :type install_space: str
        :param isolate_devel: each package will have its own develspace if True, default is False
        :type isolate_devel: bool
        :param install: packages will be installed by invoking ``make install``, defaults to False
        :type install: bool
        :param isolate_install: packages will be installed to separate folders if True, defaults to False
        :type isolate_install: bool
        :param cmake_args: extra cmake arguments to be passed to cmake for each package
        :type cmake_args: list
        :param make_args: extra make arguments to be passed to make for each package
        :type make_args: list
        :param catkin_make_args: extra make arguments to be passed to make for each catkin package
        :type catkin_make_args: list
        :param space_suffix: suffix for build, devel, and install spaces which are not explicitly set.
        :type space_suffix: str
        :raises: ValueError if workspace or source space does not exist
        """
        self.__locked = False
        ss = '' if space_suffix is None else space_suffix
        # Validation is done on assignment
        # Handle *space assignment and defaults
        self.workspace = '.' if workspace is None else workspace
        self.source_space = os.path.join(self.workspace, 'src') if source_space is None else source_space
        self.build_space = os.path.join(self.workspace, 'build' + ss) if build_space is None else build_space
        self.devel_space = os.path.join(self.workspace, 'devel' + ss) if devel_space is None else devel_space
        self.install_space = os.path.join(self.workspace, 'install' + ss) if install_space is None else install_space
        self.destdir = os.environ['DESTDIR'] if 'DESTDIR' in os.environ else None
        # Handle build options
        self.isolate_devel = isolate_devel
        self.install = install
        self.isolate_install = isolate_install
        # Handle additional cmake and make arguments
        self.cmake_args = cmake_args or []
        self.make_args = make_args or []
        self.catkin_make_args = catkin_make_args or []
        # List of packages in the workspace is set externally
        self.packages = []

    def summary(self):
        summary = [
            [
                clr("@{cf}Workspace:@|                   @{yf}{_Context__workspace}@|"),
                clr("@{cf}Buildspace:@|                  @{yf}{_Context__build_space}@|"),
                clr("@{cf}Develspace:@|                  @{yf}{_Context__devel_space}@|"),
                clr("@{cf}Installspace:@|                @{yf}{_Context__install_space}@|"),
                clr("@{cf}DESTDIR:@|                     @{yf}{_Context__destdir}@|"),
            ],
            [
                clr("@{cf}Isolate Develspaces:@|         @{yf}{_Context__isolate_devel}@|"),
                clr("@{cf}Install Packages:@|            @{yf}{_Context__install}@|"),
                clr("@{cf}Isolate Installs:@|            @{yf}{_Context__isolate_install}@|"),
            ],
            [
                clr("@{cf}Additional CMake Args:@|       @{yf}{cmake_args}@|"),
                clr("@{cf}Additional Make Args:@|        @{yf}{make_args}@|"),
                clr("@{cf}Additional catkin Make Args:@| @{yf}{catkin_make_args}@|"),
            ]
        ]
        subs = {
            'cmake_args': ', '.join(self.__cmake_args or ['None']),
            'make_args': ', '.join(self.__make_args or ['None']),
            'catkin_make_args': ', '.join(self.__catkin_make_args or ['None'])
        }
        subs.update(**self.__dict__)
        max_length = 0
        groups = []
        for group in summary:
            for index, line in enumerate(group):
                group[index] = line.format(**subs)
                max_length = max(max_length, len(remove_ansi_escape(group[index])))
            groups.append("\n".join(group))
        divider = clr('@{pf}' + ('-' * max_length) + '@|')
        return divider + "\n" + ("\n" + divider + "\n").join(groups) + "\n" + divider

    @property
    def workspace(self):
        return self.__workspace

    @workspace.setter
    def workspace(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        # Validate Workspace
        if not os.path.exists(value):
            raise ValueError("Workspace path '{0}' does not exist.".format(value))
        self.__workspace = os.path.abspath(value)

    @property
    def source_space(self):
        return self.__source_space

    @source_space.setter
    def source_space(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        # Check that the source space exists
        if not os.path.exists(value):
            raise ValueError("Could not find source space: {0}".format(value))
        self.__source_space = os.path.abspath(value)

    @property
    def build_space(self):
        return self.__build_space

    @build_space.setter
    def build_space(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        # TODO: check that build space was not run with a different context before
        self.__build_space = value

    @property
    def devel_space(self):
        return self.__devel_space

    @devel_space.setter
    def devel_space(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        # TODO: check that devel space was not run with a different context before
        self.__devel_space = value

    @property
    def install_space(self):
        return self.__install_space

    @install_space.setter
    def install_space(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        # TODO: check that install space was not run with a different context before
        self.__install_space = value

    @property
    def destdir(self):
        return self.__destdir

    @destdir.setter
    def destdir(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__destdir = value

    @property
    def isolate_devel(self):
        return self.__isolate_devel

    @isolate_devel.setter
    def isolate_devel(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__isolate_devel = value

    @property
    def install(self):
        return self.__install

    @install.setter
    def install(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__install = value

    @property
    def isolate_install(self):
        return self.__isolate_install

    @isolate_install.setter
    def isolate_install(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__isolate_install = value

    @property
    def cmake_args(self):
        return self.__cmake_args

    @cmake_args.setter
    def cmake_args(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__cmake_args = value

    @property
    def make_args(self):
        return self.__make_args

    @make_args.setter
    def make_args(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__make_args = value

    @property
    def catkin_make_args(self):
        return self.__catkin_make_args

    @catkin_make_args.setter
    def catkin_make_args(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__catkin_make_args = value

    @property
    def packages(self):
        return self.__packages

    @packages.setter
    def packages(self, value):
        if self.__locked:
            raise RuntimeError("Setting of context members is not allowed while locked.")
        self.__packages = value
