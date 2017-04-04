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

from .layers import Layer
from .legend import LegendGroup
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from qgis.PyQt.QtCore import QObject, pyqtSignal


class Project(QObject):
    layer_added = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)
        self.crs = None
        self.name = 'Not set'
        self.layers = list()
        self.legend = LegendGroup()
        self.auto_transaction = True

    def add_layer(self, layer):
        self.layers.append(layer)

    def dump(self):
        definition = dict()
        definition['crs'] = self.crs.toWkt()
        definition['auto_transaction'] = self.auto_transaction

        legend = list()
        for layer in self.layers:
            legend.append(layer.dump())

        relations = list()

        for relation in self.relations:
            relations.append(relation.dump())

        definition['legend'] = legend
        definition['relations'] = relations

        return definition

    def load(self, definition):
        self.crs = definition['crs']
        self.auto_transaction = definition['auto_transaction']

        self.layers = list()
        for layer_definition in definition['layers']:
            layer = Layer()
            layer.load(layer_definition)
            self.layers.append(layer)

    def create(self, path: str, qgis_project: QgsProject):
        qgis_project.setAutoTransaction(self.auto_transaction)
        qgis_layers = list()
        for layer in self.layers:
            qgis_layer = layer.create()
            self.layer_added.emit(qgis_layer.id())
            if not self.crs and qgis_layer.isSpatial():
                self.crs = qgis_layer.crs()

            qgis_layers.append(qgis_layer)

        qgis_project.addMapLayers(qgis_layers)

        if isinstance(self.crs, QgsCoordinateReferenceSystem):
            qgis_project.setCrs(self.crs)
        else:
            qgis_project.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(self.crs))

        qgis_relations = list()
        for relation in self.relations:
            rel = relation.create()
            assert rel.isValid()
            qgis_relations.append(rel)

        if qgis_project.relationManager().relations():
            for qgis_relation in qgis_relations:
                qgis_project.relationManager().addRelation(qgis_relation)
        else:
            qgis_project.relationManager().setRelations(qgis_relations)

        qgis_project.setCrs(self.crs)

        if self.legend:
            self.legend.create(qgis_project)

        if path:
            qgis_project.write(path)
