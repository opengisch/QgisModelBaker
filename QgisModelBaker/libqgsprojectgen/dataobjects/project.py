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
from typing import List

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsProject,
                       QgsEditorWidgetSetup,
                       QgsFieldConstraints)
from qgis.PyQt.QtCore import QObject, pyqtSignal

from QgisModelBaker.libqgsprojectgen.dataobjects.layers import Layer
from QgisModelBaker.libqgsprojectgen.dataobjects.legend import LegendGroup
from QgisModelBaker.libqgsprojectgen.dataobjects.relations import Relation

ENUM_THIS_CLASS_COLUMN = "thisclass"


class Project(QObject):
    layer_added = pyqtSignal(str)

    def __init__(self, auto_transaction=True, evaluate_default_values=True):
        QObject.__init__(self)
        self.crs = None
        self.name = 'Not set'
        self.layers = List[Layer]
        self.legend = LegendGroup()
        self.auto_transaction = auto_transaction
        self.evaluate_default_values = evaluate_default_values
        self.relations = List[Relation]

        # {Layer_class_name: {dbattribute: {Layer_class, cardinality, Layer_domain, key_field, value_field]}
        self.bags_of_enum = dict()

    def add_layer(self, layer):
        self.layers.append(layer)

    def dump(self):
        definition = dict()
        definition['crs'] = self.crs.toWkt()
        definition['auto_transaction'] = self.auto_transaction
        definition['evaluate_default_values'] = self.evaluate_default_values

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
        self.evaluate_default_values = definition['evaluate_default_values']

        self.layers = list()
        for layer_definition in definition['layers']:
            layer = Layer()
            layer.load(layer_definition)
            self.layers.append(layer)

    def create(self, path: str, qgis_project: QgsProject):
        qgis_project.setAutoTransaction(self.auto_transaction)
        qgis_project.setEvaluateDefaultValues(self.evaluate_default_values)
        qgis_layers = list()
        for layer in self.layers:
            qgis_layer = layer.create()
            self.layer_added.emit(qgis_layer.id())
            if not self.crs and qgis_layer.isSpatial():
                self.crs = qgis_layer.crs()

            qgis_layers.append(qgis_layer)

        qgis_project.addMapLayers(qgis_layers, not self.legend)

        if self.crs:
            if isinstance(self.crs, QgsCoordinateReferenceSystem):
                qgis_project.setCrs(self.crs)
            else:
                crs = QgsCoordinateReferenceSystem.fromEpsgId(self.crs)
                if not crs.isValid():
                    crs = QgsCoordinateReferenceSystem(self.crs)  # Fallback
                qgis_project.setCrs(crs)

        qgis_relations = list(
            qgis_project.relationManager().relations().values())
        dict_domains = {
            layer.layer.id(): layer.is_domain for layer in self.layers}
        for relation in self.relations:
            rel = relation.create(qgis_project, qgis_relations)
            assert rel.isValid()
            qgis_relations.append(rel)

            referencing_layer = rel.referencingLayer()
            referencing_field_constraints = referencing_layer.fieldConstraints(rel.referencingFields()[0])
            allow_null = not bool(referencing_field_constraints & QgsFieldConstraints.ConstraintNotNull)

            # If we have an extended ili2db domain, we need to filter its values
            filter_expression = "\"{}\" = '{}'".format(ENUM_THIS_CLASS_COLUMN,
                                                       relation.child_domain_name) if relation.child_domain_name else ''

            if rel.referencedLayerId() in dict_domains and dict_domains[rel.referencedLayerId()]:
                editor_widget_setup = QgsEditorWidgetSetup('RelationReference', {
                    'Relation': rel.id(),
                    'ShowForm': False,
                    'OrderByValue': True,
                    'ShowOpenFormButton': False,
                    'AllowNULL': allow_null,
                    'FilterExpression': filter_expression,
                    'FilterFields': list()
                }
                )
            else:
                editor_widget_setup = QgsEditorWidgetSetup('RelationReference', {
                    'Relation': rel.id(),
                    'ShowForm': False,
                    'OrderByValue': True,
                    'ShowOpenFormButton': False,
                    'AllowAddFeatures': True,
                    'AllowNULL': allow_null
                }
                )

            referencing_layer = rel.referencingLayer()
            referencing_layer.setEditorWidgetSetup(
                rel.referencingFields()[0], editor_widget_setup)

        qgis_project.relationManager().setRelations(qgis_relations)

        # Set Bag of Enum widget
        for layer_name, bag_of_enum in self.bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]

                minimal_selection = cardinality.startswith('1')

                current_layer = layer_obj.create()

                field_widget = 'ValueRelation'
                field_widget_config = {
                    'AllowMulti': True,
                    'UseCompleter': False,
                    'Value': value_field,
                    'OrderByValue': False,
                    'AllowNull': True,
                    'Layer': domain_table.create().id(),
                    'FilterExpression': '',
                    'Key': key_field,
                    'NofColumns': 1
                }
                field_idx = current_layer.fields().indexOf(attribute)
                setup = QgsEditorWidgetSetup(field_widget, field_widget_config)
                current_layer.setEditorWidgetSetup(field_idx, setup)
                if minimal_selection:
                    constraint_expression = 'array_length("{}")>0'.format(attribute)
                    current_layer.setConstraintExpression(field_idx, constraint_expression, self.tr('The minimal selection is 1'))

        for layer in self.layers:
            layer.create_form(self)

        if self.legend:
            self.legend.create(qgis_project)

        if path:
            qgis_project.write(path)

    def post_generate(self):
        for layer in self.layers:
            layer.post_generate(self)
