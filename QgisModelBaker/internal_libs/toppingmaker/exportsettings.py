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
from enum import Enum
from typing import Union

from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer


class ExportSettings(object):
    """
    The requested export settings of each node in the specific dicts:
    - qmlstyle_setting_nodes
    - definition_setting_nodes
    - source_setting_nodes

    The usual structure is using QgsLayerTreeNode as key and then export True/False
    {
        <QgsLayerTreeNode(Node1)>: { export: False }
        <QgsLayerTreeNode(Node2)>: { export: True }
    }

    But alternatively the layername can be used as key. In ProjectTopping it first looks up the node and if not available looking up the name.
    Using the node is much more consistent, since one can use layers with the same name, but for nodes you need the project already in advance.
    With name you can use prepared settings to pass (before the project exists) e.g. in automated workflows.
    {
        "Node1": { export: False }
        "Node2": { export: True }
    }

    For some settings we have additional info. Like in qmlstyle_nodes <QgsMapLayer.StyleCategories>. These are Flags, and can be constructed manually as well.
    qmlstyle_nodes =
    {
        <QgsLayerTreeNode(Node1)>: { export: False }
        <QgsLayerTreeNode(Node2)>: { export: True, categories: <QgsMapLayer.StyleCategories> }
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

    def _get_setting(self, setting_nodes, node=None, name=None):
        setting = {}
        if node:
            setting = setting_nodes.get(node, {})
        if not setting:
            setting = setting_nodes.get(name, {})
        return setting

    def _set_setting(self, setting_nodes, setting, node=None, name=None) -> bool:
        if node:
            setting_nodes[node] = setting
            return True
        if name:
            setting_nodes[name] = setting
            return True
        return False
