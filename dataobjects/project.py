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
from dataobjects import Layer
from qgis.core import QgsCoordinateReferenceSystem


class Project(object):

    def __init__(self):
        self.crs = None
        self.name = 'Not set'
        self.layers = list()

    def add_layer(self, layer):
        self.layers.append(layer)

    def dump(self):
        definition = dict()
        definition['crs'] = self.crs

        legend = list()
        for layer in self.layers:
            pass
            

    def load(self, definition):
        self.crs = definition['crs']

        self.layers=list()
        for layer_definition in definition['layers']:
            layer = Layer()
            layer.load(layer_definition)
            self.layers.append(layer)

    def create(self, path, qgis_project):
        for layer in self.layers:
            qgis_layer = layer.create()
            if not self.crs and qgis_layer.isSpatial():
                self.crs = qgis_layer.crs()

            qgis_project.addMapLayer(qgis_layer)

        if isinstance(self.crs, QgsCoordinateReferenceSystem):
            qgis_project.setCrs(self.crs)
        else:
            qgis_project.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(self.crs))

        qgis_project.write(path)
        print('Project written to {}'.format(path))