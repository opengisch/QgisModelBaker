# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
        email                : david at opengis ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os


class Target(object):
    """
    Where to store topping files and ilidata.xml.

    If there is no subdir it will look like:
    <maindir>
    ├── projecttopping
    │  └── <projectname>.yaml
    ├── layerstyle
    │  ├── <projectname>_<layername>.qml
    │  └── <projectname>_<layername>.qml
    └── layerdefinition
    │  └── <projectname>_<layername>.qlr

    With subdir:
    <maindir>
    ├── <subdir>
    │  ├── projecttopping
    │  │  └── <projectname>.yaml
    │  ├── layerstyle
    │  │  ├── <projectname>_<layername>.qml
    │  │  └── <projectname>_<layername>.qml
    │  └── layerdefinition
    │  │  └── <projectname>_<layername>.qlr

    And the usabilityhub specific dirs:
    .
    ├── metaconfig
    ├── referencedata
    ├── sql
    └── metaattributes
    """

    def __init__(
        self,
        projectname: str = "project",
        main_dir: str = None,
        sub_dir: str = None,
        path_resolver=None,
    ):
        self.projectname = projectname
        self.main_dir = main_dir
        self.sub_dir = sub_dir
        self.path_resolver = path_resolver

        if not path_resolver:
            self.path_resolver = default_path_resolver

        self.toppingfileinfo_list = []

    def filedir_path(self, file_dir):
        relative_path = os.path.join(self.sub_dir, file_dir)
        absolute_path = os.path.join(self.main_dir, relative_path)
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)
        return absolute_path, relative_path


def default_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)

    toppingfile = {"path": os.path.join(relative_filedir_path, name), "type": type}
    target.toppingfileinfo_list.append(toppingfile)

    return os.path.join(relative_filedir_path, name)


# - [ ] can this go to target
