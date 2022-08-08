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
import shutil
from enum import Enum
from typing import Union

import yaml
from qgis.core import (
    QgsLayerDefinition,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
)

from .utils import slugify


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
        file_dirs: list() = [],
        path_resolver=None,
    ):
        self.projectname = projectname
        self.main_dir = main_dir
        self.sub_dir = sub_dir
        self.file_dirs = file_dirs
        self.path_resolver = path_resolver

        if not path_resolver:
            self.path_resolver = default_path_resolver

        self.toppingfileinfo_list = []

    def create_dirs(self):
        for file_dir in self.file_dirs:
            absolute_path, _ = self.filedir_path(file_dir)
            if not os.path.exists(absolute_path):
                os.makedirs(absolute_path)

    def filedir_path(self, file_dir):
        relative_path = os.path.join(self.sub_dir, file_dir)
        absolute_path = os.path.join(self.main_dir, relative_path)
        return absolute_path, relative_path

    def relative_file_dir(self, file_dir):
        return os.path.join(self.sub_dir, file_dir)


def default_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)

    toppingfile = {"path": os.path.join(relative_filedir_path, name), "type": type}
    target.toppingfileinfo_list.append(toppingfile)

    return os.path.join(relative_filedir_path, name)


class ExportSettings(object):
    """
    The requested export settings of each node.
    The usual structure is using QgsLayerTreeNode as key and then export True/False

    {
        <QgsLayerTreeNode(Node1)>: {
                export: False
            }
        <QgsLayerTreeNode(Node2)>: {
                export: True
            }
        <QgsLayerTreeNode(Node3)>: {
                export: False
            }
        <QgsLayerTreeNode(Node4)>: {
                export: True
            }
    }

    But alternatively the layername can be used as key. In ProjectTopping it first looks up the node and if not available looking up the name.
    Using the node is much more consistent, since one can use layers with the same name, but for nodes you need the project already in advance.
    With name you can use kind of fix settings to pass e.g. in automated workflows.

    {
        "Node1": {
                export: False
            }
        "Node2":: {
                export: True
            }
        "Node3":: {
                export: False
            }
        "Node4":: {
                export: True
            }
    }

    For some settings we have additional info. Like in qmlstyle_nodes <QgsMapLayer.StyleCategories>. These are Flags, and can be constructed manually as well.

    qmlstyle_nodes =
    {
        <QgsLayerTreeNode(Node1)>: {
                export: False
            }
        <QgsLayerTreeNode(Node2)>: {
                export: True
                categories: <QgsMapLayer.StyleCategories>
            }
        <QgsLayerTreeNode(Node3)>: {
                export: False
            }
        <QgsLayerTreeNode(Node4)>: {
                export: True
                categories: <QgsMapLayer.StyleCategories>
            }
    }
    """

    class ToppingType(Enum):
        QMLSTYLE = 1
        DEFINITION = 2
        SOURCE = 3

    def __init__(self):
        self.qmlstyle_setting_nodes = {}
        self.definition_setting_nodes = {}
        self.source_setting_nodes = {}

    def set_setting_values(
        self,
        type: ToppingType,
        node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup] = None,
        name: str = None,
        export=True,
        categories=None,
    ) -> bool:
        """
        Appends the values (export, categories) to an existing setting
        """
        setting_nodes = self._setting_nodes(type)
        setting = self._get_setting(setting_nodes, node, name)
        setting["export"] = export
        if categories:
            setting["categories"] = categories
        return self._set_setting(setting_nodes, setting, node, name)

    def get_setting(
        self,
        type: ToppingType,
        node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup] = None,
        name: str = None,
    ) -> dict():
        """
        Returns an existing or an empty setting dict
        """
        setting_nodes = self._setting_nodes(type)
        return self._get_setting(setting_nodes, node, name)

    def _setting_nodes(self, type: ToppingType):
        if type == ExportSettings.ToppingType.QMLSTYLE:
            return self.qmlstyle_setting_nodes
        if type == ExportSettings.ToppingType.DEFINITION:
            return self.definition_setting_nodes
        if type == ExportSettings.ToppingType.SOURCE:
            return self.source_setting_nodes

    def _get_setting(self, setting_nodes, node=None, name=None) -> dict():
        if node:
            return setting_nodes.get(node, {})
        if name:
            return setting_nodes.get(name, {})
        return {}

    def _set_setting(self, setting_nodes, setting, node=None, name=None) -> bool:
        if node:
            setting_nodes[node] = setting
            return True
        if name:
            setting_nodes[name] = setting
            return True
        return False


class ProjectTopping(object):
    """
    What needs to go to the project topping yaml file.
    - layertree
    - layerorder
    - project variables (future)
    - print layout (future)
    - map themes (future)
    """

    PROJECTTOPPING_TYPE = "projecttopping"
    LAYERDEFINITION_TYPE = "layerdefinition"
    LAYERSTYLE_TYPE = "layerstyle"

    class TreeItemProperties(object):
        def __init__(self):
            # if the node is a group
            self.group = False
            # if the node is visible
            self.checked = True
            # if the node is expanded
            self.expanded = True
            # if the (layer) node shows feature count
            self.featurecount = False
            # if the (group) node handles mutually-exclusive
            self.mutually_exclusive = False
            # if the (group) node handles mutually-exclusive, the index of the checked child
            self.mutually_exclusive_child = -1
            # the layers provider to create it from source
            self.provider = None
            # the layers uri to create it from source
            self.uri = None
            # the style file - if None then not requested
            self.qmlstylefile = None
            # the definition file - if None then not requested
            self.definitionfile = None

    class LayerTreeItem(object):
        def __init__(self):
            self.items = []
            self.name = None
            self.properties = ProjectTopping.TreeItemProperties()
            self.temporary_toppingfile_dir = os.path.expanduser("~/.temp_topping_files")

        def make_item(
            self,
            node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup],
            settings: ExportSettings,
        ):
            # properties for every kind of nodes
            self.name = node.name()
            self.properties.checked = node.itemVisibilityChecked()
            self.properties.expanded = node.isExpanded()

            if isinstance(node, QgsLayerTreeLayer):
                self.properties.featurecount = node.customProperty("showFeatureCount")
                if node in settings.nodes_using_source:
                    if node.layer().dataProvider():
                        self.properties.provider = node.layer().dataProvider().name()
                        self.properties.uri = (
                            node.layer().dataProvider().dataSourceUri()
                        )
                if node in settings.nodes_using_style:
                    self.properties.qmlstylefile = self._temporary_qmlstylefile(node)
            elif isinstance(node, QgsLayerTreeGroup):
                # it's a group
                self.properties.group = True
                self.properties.mutually_exclusive = node.isMutuallyExclusive()

                index = 0
                for child in node.children():
                    item = ProjectTopping.LayerTreeItem()
                    item.make_item(child, settings)
                    # set the first checked item as mutually exclusive child
                    if (
                        self.properties.mutually_exclusive
                        and self.properties.mutually_exclusive_child == -1
                    ):
                        if item.properties.checked:
                            self.properties.mutually_exclusive_child = index
                    self.items.append(item)
                    index += 1
            else:
                print(
                    f"here with {node.name()} we have the problem with the LayerTreeNode (it recognizes on QgsLayerTreeLayer QgsLayerTreeNode instead. Similar to https://github.com/opengisch/QgisModelBaker/pull/514 - this needs a fix..."
                )
                return

            if node in settings.nodes_using_definition:
                self.properties.definitionfile = self._temporary_definitionfile(node)

        def _temporary_definitionfile(
            self, node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup]
        ):
            nodename_slug = f"temp_definitionfile_{slugify(self.name)}.qlr"
            os.makedirs(self.temporary_toppingfile_dir, exist_ok=True)
            temporary_toppingfile_path = os.path.join(
                self.temporary_toppingfile_dir, nodename_slug
            )
            QgsLayerDefinition.exportLayerDefinition(temporary_toppingfile_path, node)
            return temporary_toppingfile_path

        def _temporary_qmlstylefile(self, node: QgsLayerTreeLayer):
            nodename_slug = f"temp_qmlstylefile_{slugify(self.name)}.qml"
            os.makedirs(self.temporary_toppingfile_dir, exist_ok=True)
            temporary_toppingfile_path = os.path.join(
                self.temporary_toppingfile_dir, nodename_slug
            )
            node.layer().saveNamedStyle(temporary_toppingfile_path)
            return temporary_toppingfile_path

    def __init__(self):
        self.layertree = self.LayerTreeItem()
        self.layerorder = []

    def parse_project(
        self, project: QgsProject, settings: ExportSettings = ExportSettings()
    ):
        """
        Parses a project into the ProjectTopping structure. Means the LayerTreeNodes are loaded into the layertree variable and the CustomLayerOrder into the layerorder. The project is not keeped as member variable.

        :param QgsProject project: the project to parse.
        :param ExportSettings settings: defining if the node needs a source or style / definitionfiles.
        """
        root = project.layerTreeRoot()
        if root:
            self.layertree.make_item(project.layerTreeRoot(), settings)
            self.layerorder = (
                root.customLayerOrder() if root.hasCustomLayerOrder() else []
            )
        else:
            print("could not load the project...")

    def generate_files(self, target: Target) -> str:
        # set the current target here and append project topping specific file directories and create them
        """
        Creates a projecttopping file (yaml) and the linked toppigfiles (qml, qlr) into the given main and sub directories.

        :param Target target: the target defining the directories to write the files into.
        :return: projecttopping file (yaml) path
        """

        # creating the directories
        target.file_dirs.extend(
            [
                ProjectTopping.PROJECTTOPPING_TYPE,
                ProjectTopping.LAYERSTYLE_TYPE,
                ProjectTopping.LAYERDEFINITION_TYPE,
            ]
        )
        target.create_dirs()

        # generate projecttopping as a dict
        projecttopping_dict = self._projecttopping_dict(target)

        # write the yaml
        projecttopping_slug = f"{slugify(target.projectname)}.yaml"
        absolute_filedir_path, relative_filedir_path = target.filedir_path(
            ProjectTopping.PROJECTTOPPING_TYPE
        )
        with open(
            os.path.join(absolute_filedir_path, projecttopping_slug), "w"
        ) as projecttopping_yamlfile:
            output = yaml.dump(projecttopping_dict, projecttopping_yamlfile)
            print(output)

        return target.path_resolver(
            target, projecttopping_slug, ProjectTopping.PROJECTTOPPING_TYPE
        )

    def load_files(self, target: Target):
        """
        Not yet implemented.
        """

    def generate_project(self, target: Target) -> QgsProject:
        """
        Not yet implemented.
        """
        return QgsProject()

    def _projecttopping_dict(self, target: Target):
        """
        Creates the layertree as a dict.
        Creates the layerorder as a list.
        And it generates and stores the toppingfiles.
        """
        projecttopping_dict = {}
        projecttopping_dict["layertree"] = self._item_dict_list(
            target, self.layertree.items
        )
        projecttopping_dict["layerorder"] = [layer.name() for layer in self.layerorder]
        return projecttopping_dict

    def _item_dict_list(self, target: Target, items):
        item_dict_list = []
        for item in items:
            item_dict = self._create_item_dict(target, item)
            item_dict_list.append(item_dict)
        return item_dict_list

    def _create_item_dict(self, target: Target, item: LayerTreeItem):
        item_dict = {}
        item_properties_dict = {}

        if item.properties.group:
            item_properties_dict["group"] = True
            if item.properties.mutually_exclusive:
                item_properties_dict["mutually-exclusive"] = True
                item_properties_dict[
                    "mutually-exclusive-child"
                ] = item.properties.mutually_exclusive_child
        else:
            if item.properties.featurecount:
                item_properties_dict["featurecount"] = True
            if item.properties.qmlstylefile:
                item_properties_dict["qmlstylefile"] = self._qmlstylefile_link(
                    target, item
                )
            if item.properties.provider and item.properties.uri:
                item_properties_dict["provider"] = item.properties.provider
                item_properties_dict["uri"] = item.properties.uri

        item_properties_dict["checked"] = item.properties.checked
        item_properties_dict["expanded"] = item.properties.expanded

        if item.properties.definitionfile:
            item_properties_dict["definitionfile"] = self._definitionfile_link(
                target, item
            )

        if item.items:
            child_item_dict_list = self._item_dict_list(target, item.items)
            item_properties_dict["child-nodes"] = child_item_dict_list

        item_dict[item.name] = item_properties_dict
        return item_dict

    def _definitionfile_link(self, target: Target, item: LayerTreeItem):
        nodename_slug = f"{slugify(target.projectname)}_{slugify(item.name)}.qlr"
        absolute_filedir_path, relative_filedir_path = target.filedir_path(
            ProjectTopping.LAYERDEFINITION_TYPE
        )
        shutil.copy(
            item.properties.definitionfile,
            os.path.join(absolute_filedir_path, nodename_slug),
        )
        return target.path_resolver(
            target, nodename_slug, ProjectTopping.LAYERDEFINITION_TYPE
        )

    def _qmlstylefile_link(self, target: Target, item: LayerTreeItem):
        nodename_slug = f"{slugify(target.projectname)}_{slugify(item.name)}.qml"
        absolute_filedir_path, relative_filedir_path = target.filedir_path(
            ProjectTopping.LAYERSTYLE_TYPE
        )
        shutil.copy(
            item.properties.qmlstylefile,
            os.path.join(absolute_filedir_path, nodename_slug),
        )
        return target.path_resolver(
            target, nodename_slug, ProjectTopping.LAYERSTYLE_TYPE
        )
