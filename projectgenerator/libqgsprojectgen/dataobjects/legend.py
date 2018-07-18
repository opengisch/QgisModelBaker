# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2016-12-21
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
        email                : info@opengis.ch
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

from qgis.core import QgsProject

from projectgenerator.utils.qgis_utils import get_suggested_index_for_layer



class LegendGroup(object):

    def __init__(self, name=None, expanded=True, ignore_node_names=[]):
        self.name = name
        self.items = list()
        self.expanded = expanded

        # When adding layers in order, one could want to ignore nodes (e.g.,
        # groups that should be always on top)
        self.ignore_node_names = ignore_node_names

    def dump(self):
        definition = list()
        for item in self.items:
            definition.append(item.dump())
        return definition

    def append(self, item):
        self.items.append(item)

    def __getitem__(self, item):
        for i in self.items:
            try:
                if i.name == item:
                    return i
            except AttributeError:
                if i.table_name == item:
                    return i

        raise KeyError(item)

    def load(self, definition):
        self.items = definition

    def create(self, qgis_project: QgsProject, group=None):
        if not group:
            group = qgis_project.layerTreeRoot()

        for item in self.items:
            if isinstance(item, LegendGroup):
                subgroup = group.findGroup(item.name)
                if subgroup is None:
                    subgroup = group.addGroup(item.name)
                    subgroup.setExpanded(item.expanded)
                item.create(qgis_project, subgroup)
            else:
                layer = item.layer
                index = get_suggested_index_for_layer(layer, group, self.ignore_node_names) if layer.isSpatial() else 0
                group.insertLayer(index, layer)

    def is_empty(self):
        return not bool(self.items)
