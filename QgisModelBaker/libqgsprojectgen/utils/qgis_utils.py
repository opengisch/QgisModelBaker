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

from qgis.core import Qgis, QgsLayerTreeNode, QgsMapLayer, QgsWkbTypes

layer_order = [
    "point",  # QgsWkbTypes.PointGeometry
    "line",  # QgsWkbTypes.LineGeometry
    "polygon",  # QgsWkbTypes.PolygonGeometry
    "raster",  # QgsMapLayer.RasterLayer
    "table",  # QgsWkbTypes.NullGeometry
    "unknown",
]  # Anything else like geometry collections or plugin layers


def get_first_index_for_layer_type(layer_type, group, ignore_node_names=None):
    """
    Finds the first index (from top to bottom) in the layer tree where a
    specific layer type is found. This function works only for the given group.
    """
    if ignore_node_names is None:
        ignore_node_names = []

    tree_nodes = group.children()

    for current, tree_node in enumerate(tree_nodes):
        if tree_node.name() in ignore_node_names:
            # Some groups (e.g., validation errors) might be useful on a
            # specific position (e.g., at the top), so, skip it to get indices
            continue
        if (
            tree_node.nodeType() == QgsLayerTreeNode.NodeGroup
            and layer_type != "unknown"
        ):
            return None
        elif (
            tree_node.nodeType() == QgsLayerTreeNode.NodeGroup
            and layer_type == "unknown"
        ):
            # We've reached the lowest index in the layer tree before a group
            return current

        layer = tree_node.layer()
        if get_layer_type(layer) == layer_type:
            return current

    return None


def get_suggested_index_for_layer(layer, group, ignore_node_names=None):
    """
    Returns the index where a layer can be inserted, taking other layer types
    into account. For instance, if a line layer is given, this function will
    return the index of the first line layer in the layer tree (if above it
    there are no lower-ordered layers like tables, otherwise this returns that
    table index), and if there are no line layers in it, it will continue with
    the first index of polygons , rasters, tables, or groups. Always following
    the order given in the global layer_order variable.
    """
    indices = []
    index = None
    for layer_type in layer_order[
        layer_order.index(get_layer_type(layer)) :
    ]:  # Slice from current until last
        index = get_first_index_for_layer_type(layer_type, group, ignore_node_names)
        if index is not None:
            indices.append(index)

    if indices:
        index = min(indices)
    if index is None:
        return -1  # Send it to the last position in layer tree
    else:
        return index


def get_layer_type(layer):
    """
    To deal with all layer types, map their types to known values
    """
    if layer.type() == QgsMapLayer.VectorLayer:
        if layer.isSpatial():
            if layer.geometryType() == QgsWkbTypes.UnknownGeometry:
                return "unknown"
            else:
                return layer_order[layer.geometryType()]  # Point, Line or Polygon
        else:
            return "table"
    elif layer.type() == QgsMapLayer.RasterLayer:
        return "raster"
    else:
        return "unknown"


def get_group_non_recursive(group, group_name):
    groups = (
        group.findGroups(False)
        if Qgis.QGIS_VERSION_INT >= 31800
        else group.findGroups()
    )
    for group in groups:
        if group.name() == group_name:
            return group

    return None
