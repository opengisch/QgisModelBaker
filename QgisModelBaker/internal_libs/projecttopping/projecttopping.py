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


from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject


class Target(object):
    """
    Where to store topping files and ilidata.xml.

    If there is no subdir it will look like:
    <maindir>
    ├── projecttopping
    │  └── <name>.yaml
    ├── layerstyle
    │  ├── <name>_<layer1>.qml
    │  └── <name>_<layer2>.qml
    └── layerdefinition
    │  └── <name>_<layer3>.qlr

    With subdir:
    <maindir>
    ├── <subdir>
    │  ├── projecttopping
    │  │  └── <name>.yaml
    │  ├── layerstyle
    │  │  ├── <name>_<layer1>.qml
    │  │  └── <name>_<layer2>.qml
    │  └── layerdefinition
    │  │  └── <name>_<layer3>.qlr

    And the usabilityhub specific dirs:
    .
    ├── metaconfig
    ├── referencedata
    ├── sql
    └── metaattributes
    """

    def __init__(self):
        self.name = None
        self.maindir = None
        self.subdir = None

    def create_dirs(self):
        pass


class ProjectTopping(object):
    """
    What needs to go to the project topping yaml file.
    - layertree
    - layerorder
    - project variables (future)
    - print layout (future)
    - map themes (future)
    """

    class TreeItemSettings(object):
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

            # not sure when they should be loaded from the layer
            self.provider = None
            self.uri = None
            self.qmlstylefile = None
            self.definitionfil = None

            self.use_source = True
            self.use_qmlstylefile = True
            self.use_definitionfile = False

    class LayerTreeItem(object):
        def __init__(self):
            self.items = [ProjectTopping.LayerTreeItem]
            self.layer = None
            self.settings = ProjectTopping.TreeItemSettings()

        def make_item(self, node):
            # settings for every kind of nodes
            self.settings.checked = node.itemVisibilityChecked()
            self.settings.expanded = node.isExpanded()

            if isinstance(node, QgsLayerTreeLayer):
                # it's a layer
                self.layer = node.layer()
                self.settings.featurecount = node.customProperty("showFeatureCount")
            elif isinstance(node, QgsLayerTreeGroup):
                # it's a group
                self.settings.group = True
                self.settings.mutually_exclusive = node.isMutuallyExclusive()

                for child in node.children():
                    item = ProjectTopping.LayerTreeItem()
                    item.make_item(child)
                    # set the first checked item as mutually exclusive child
                    self.settings.mutually_exclusive_child = item.settings.checked
                    self.items.append(item)
            else:
                print(
                    "here we have the problem with the LayerTreeNode similar to https://github.com/opengisch/QgisModelBaker/pull/514 - this needs a fix..."
                )

    def __init__(self):
        self.layertree = self.LayerTreeItem()
        self.layerorder = []

    def load_project(self, project: QgsProject):
        root = project.layerTreeRoot()
        if root:
            self.layertree.make_item(project.layerTreeRoot())
            self.layerorder = (
                root.customLayerOrder() if root.hasCustomLayerOrder() else []
            )
        else:
            print("could not load the project...")

    def generate_file(self, target: Target) -> str:
        return None

    def generate_project(self, target: Target) -> QgsProject:
        """
        Not yet implemented.
        """
        return QgsProject()
