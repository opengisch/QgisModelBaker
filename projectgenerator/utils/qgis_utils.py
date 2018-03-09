# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    05/03/18
    git sha              :    :%H$
    copyright            :    (C) 2018 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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

from qgis.core import QgsLayerTreeNode, QgsProject, QgsWkbTypes

layer_order = [QgsWkbTypes.PointGeometry,
               QgsWkbTypes.LineGeometry,
               QgsWkbTypes.PolygonGeometry,
               QgsWkbTypes.UnknownGeometry]

def get_first_index_for_geometry_type(geometry_type, group=QgsProject.instance().layerTreeRoot()):
    tree_nodes = group.children()

    for current, tree_node in enumerate(tree_nodes):
        if tree_node.nodeType() == QgsLayerTreeNode.NodeGroup and geometry_type != QgsWkbTypes.UnknownGeometry:
            return None
        elif tree_node.nodeType() == QgsLayerTreeNode.NodeGroup and geometry_type == QgsWkbTypes.UnknownGeometry:
            return current

        layer = tree_node.layer()
        if layer.geometryType() == geometry_type:
            return current

    return None

def get_suggested_index_for_layer(layer):
    for geometry_type in layer_order[layer_order.index(layer.geometryType()):]: # slice from current until last
        index = get_first_index_for_geometry_type(geometry_type)
        if index is not None:
            break

    return -1 if index is None else index # Send it to the last position in layer tree
