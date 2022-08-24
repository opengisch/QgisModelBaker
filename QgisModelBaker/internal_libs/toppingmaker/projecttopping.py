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
from typing import Union

import yaml
from qgis.core import (
    QgsLayerDefinition,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
)

from .exportsettings import ExportSettings
from .target import Target
from .utils import slugify, toppingfile_link


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
            export_settings: ExportSettings,
        ):
            # properties for every kind of nodes
            self.name = node.name()
            self.properties.checked = node.itemVisibilityChecked()
            self.properties.expanded = node.isExpanded()

            if isinstance(node, QgsLayerTreeLayer):
                self.properties.featurecount = node.customProperty("showFeatureCount")
                source_setting = export_settings.get_setting(
                    ExportSettings.ToppingType.SOURCE, node, node.name()
                )
                if source_setting.get("export", False):
                    if node.layer().dataProvider():
                        self.properties.provider = node.layer().dataProvider().name()
                        self.properties.uri = (
                            node.layer().dataProvider().dataSourceUri()
                        )
                qml_setting = export_settings.get_setting(
                    ExportSettings.ToppingType.QMLSTYLE, node, node.name()
                )
                if qml_setting.get("export", False):
                    self.properties.qmlstylefile = self._temporary_qmlstylefile(
                        node,
                        QgsMapLayer.StyleCategory(
                            qml_setting.get(
                                "categories",
                                QgsMapLayer.StyleCategory.AllStyleCategories,
                            )
                        ),
                    )
            elif isinstance(node, QgsLayerTreeGroup):
                # it's a group
                self.properties.group = True
                self.properties.mutually_exclusive = node.isMutuallyExclusive()

                index = 0
                for child in node.children():
                    item = ProjectTopping.LayerTreeItem()
                    item.make_item(child, export_settings)
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

            definition_setting = export_settings.get_setting(
                ExportSettings.ToppingType.DEFINITION, node, node.name()
            )
            if definition_setting.get("export", False):
                self.properties.definitionfile = self._temporary_definitionfile(node)

        def _temporary_definitionfile(
            self, node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup]
        ):
            filename_slug = f"{slugify(self.name)}.qlr"
            os.makedirs(self.temporary_toppingfile_dir, exist_ok=True)
            temporary_toppingfile_path = os.path.join(
                self.temporary_toppingfile_dir, filename_slug
            )
            QgsLayerDefinition.exportLayerDefinition(temporary_toppingfile_path, [node])
            return temporary_toppingfile_path

        def _temporary_qmlstylefile(
            self,
            node: QgsLayerTreeLayer,
            categories: QgsMapLayer.StyleCategories = QgsMapLayer.StyleCategory.AllStyleCategories,
        ):
            filename_slug = f"{slugify(self.name)}.qml"
            os.makedirs(self.temporary_toppingfile_dir, exist_ok=True)
            temporary_toppingfile_path = os.path.join(
                self.temporary_toppingfile_dir, filename_slug
            )
            node.layer().saveNamedStyle(temporary_toppingfile_path, categories)
            return temporary_toppingfile_path

    def __init__(self):
        self.layertree = self.LayerTreeItem()
        self.layerorder = []

    def parse_project(
        self, project: QgsProject, export_settings: ExportSettings = ExportSettings()
    ):
        """
        Parses a project into the ProjectTopping structure. Means the LayerTreeNodes are loaded into the layertree variable and the CustomLayerOrder into the layerorder. The project is not keeped as member variable.

        :param QgsProject project: the project to parse.
        :param ExportSettings settings: defining if the node needs a source or style / definitionfiles.
        """
        root = project.layerTreeRoot()
        if root:
            self.layertree.make_item(project.layerTreeRoot(), export_settings)
            self.layerorder = (
                root.customLayerOrder() if root.hasCustomLayerOrder() else []
            )
        else:
            print("could not load the project...")
            return False
        return True

    def generate_files(self, target: Target) -> str:
        # set the current target here and append project topping specific file directories and create them
        """
        Creates a projecttopping file (yaml) and the linked toppigfiles (qml, qlr) into the given main and sub directories.

        :param Target target: the target defining the directories to write the files into.
        :return: projecttopping file (yaml) path
        """
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
        - [ ] Not yet implemented.
        """

    def generate_project(self, target: Target) -> QgsProject:
        """
        - [ ] Not yet implemented.
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
                item_properties_dict["qmlstylefile"] = toppingfile_link(
                    target, ProjectTopping.LAYERSTYLE_TYPE, item.properties.qmlstylefile
                )
            if item.properties.provider and item.properties.uri:
                item_properties_dict["provider"] = item.properties.provider
                item_properties_dict["uri"] = item.properties.uri

        item_properties_dict["checked"] = item.properties.checked
        item_properties_dict["expanded"] = item.properties.expanded

        if item.properties.definitionfile:
            item_properties_dict["definitionfile"] = toppingfile_link(
                target,
                ProjectTopping.LAYERDEFINITION_TYPE,
                item.properties.definitionfile,
            )

        if item.items:
            child_item_dict_list = self._item_dict_list(target, item.items)
            item_properties_dict["child-nodes"] = child_item_dict_list

        item_dict[item.name] = item_properties_dict
        return item_dict
