# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
                              (C) 2016 by OPENGIS.ch
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
import re

from qgis.core import QgsProviderRegistry, QgsWkbTypes, QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QLocale

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libqgsprojectgen.dataobjects import Field
from QgisModelBaker.libqgsprojectgen.dataobjects import LegendGroup
from QgisModelBaker.libqgsprojectgen.dataobjects.layers import Layer
from QgisModelBaker.libqgsprojectgen.dataobjects.relations import Relation
from ..dbconnector import pg_connector, gpkg_connector
from .domain_relations_generator import DomainRelationGenerator
from .config import IGNORED_SCHEMAS, IGNORED_TABLES, IGNORED_FIELDNAMES, READONLY_FIELDNAMES
from ..db_factory.db_simple_factory import DbSimpleFactory

class Generator:
    """Builds Model Baker objects from data extracted from databases."""

    def __init__(self, tool, uri, inheritance, schema=None, pg_estimated_metadata=False):
        self.tool = tool
        self.uri = uri
        self.inheritance = inheritance
        self.schema = schema or None
        self.pg_estimated_metadata = pg_estimated_metadata

        self.db_simple_factory = DbSimpleFactory()
        db_factory = self.db_simple_factory.create_factory(self.tool)
        self._db_connector = db_factory.get_db_connector(uri, schema)

    def layers(self, filter_layer_list=[]):
        tables_info = self.get_tables_info()
        layers = list()

        db_factory = self.db_simple_factory.create_factory(self.tool)

        layer_uri = db_factory.get_layer_uri(self.uri)
        layer_uri.pg_estimated_metadata = self.pg_estimated_metadata

        for record in tables_info:
            # When in PostGIS mode, leaving schema blank should load tables from
            # all schemas, except the ignored ones
            if self.schema:
                if record['schemaname'] != self.schema:
                    continue
            elif record['schemaname'] in IGNORED_SCHEMAS:
                continue

            if record['tablename'] in IGNORED_TABLES:
                continue

            if filter_layer_list and record['tablename'] not in filter_layer_list:
                continue

            alias = record['table_alias'] if 'table_alias' in record else ''
            is_domain = record['kind_settings'] == 'ENUM' or record[
                'kind_settings'] == 'CATALOGUE' if 'kind_settings' in record else False
            is_structure = record['kind_settings'] == 'STRUCTURE' if 'kind_settings' in record else False
            is_nmrel = record['kind_settings'] == 'ASSOCIATION' if 'kind_settings' in record else False

            display_expression = ''
            if 'ili_name' in record:
                meta_attrs = self.get_meta_attrs(record['ili_name'])
                for attr_record in meta_attrs:
                    if attr_record['attr_name'] == 'dispExpression':
                        display_expression = attr_record['attr_value']

            layer = Layer(layer_uri.provider,
                          layer_uri.get_data_source_uri(record),
                          record['tablename'],
                          record['srid'],
                          record['extent'] if 'extent' in record else None,
                          record['geometry_column'],
                          QgsWkbTypes.parseType(
                              record['type']) or QgsWkbTypes.Unknown,
                          alias,
                          is_domain,
                          is_structure,
                          is_nmrel,
                          display_expression)

            # Configure fields for current table
            fields_info = self.get_fields_info(record['tablename'])
            constraints_info = self.get_constraints_info(record['tablename'])
            re_iliname = re.compile(r'^@iliname (.*)$')

            for fielddef in fields_info:
                column_name = fielddef['column_name']
                comment = fielddef['comment']
                m = re_iliname.match(comment) if comment else None

                alias = None
                if 'column_alias' in fielddef:
                    alias = fielddef['column_alias']
                if m and not alias:
                    alias = m.group(1)

                field = Field(column_name)
                field.alias = alias

                # Should we hide the field?
                hide_attribute = False

                if 'fully_qualified_name' in fielddef:
                    fully_qualified_name = fielddef['fully_qualified_name']
                    if fully_qualified_name:
                        meta_attrs_column = self.get_meta_attrs(fully_qualified_name)

                        for attr_record in meta_attrs_column:
                            if attr_record['attr_name'] == 'hidden':
                                if attr_record['attr_value'] == 'True':
                                    hide_attribute = True
                                    break

                if column_name in IGNORED_FIELDNAMES:
                    hide_attribute = True

                field.hidden = hide_attribute

                if column_name in READONLY_FIELDNAMES:
                    field.read_only = True

                if column_name in constraints_info:
                    field.widget = 'Range'
                    field.widget_config['Min'] = constraints_info[column_name][0]
                    field.widget_config['Max'] = constraints_info[column_name][1]
                    if 'numeric_scale' in fielddef:
                        field.widget_config['Step'] = pow(10, -1 * fielddef['numeric_scale'])
                    # field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''
                    if 'unit' in fielddef and fielddef['unit'] is not None:
                        field.alias = '{alias} [{unit}]'.format(
                            alias=alias or column_name, unit=fielddef['unit'])

                if 'texttype' in fielddef and fielddef['texttype'] == 'MTEXT':
                    field.widget = 'TextEdit'
                    field.widget_config['IsMultiline'] = True

                data_type = self._db_connector.map_data_types(
                    fielddef['data_type'])
                if 'time' in data_type or 'date' in data_type:
                    field.widget = 'DateTime'
                    field.widget_config['calendar_popup'] = True

                    dateFormat = QLocale(QgsApplication.instance(
                    ).locale()).dateFormat(QLocale.ShortFormat)
                    timeFormat = QLocale(QgsApplication.instance(
                    ).locale()).timeFormat(QLocale.ShortFormat)
                    dateTimeFormat = QLocale(QgsApplication.instance(
                    ).locale()).dateTimeFormat(QLocale.ShortFormat)

                    if data_type == self._db_connector.QGIS_TIME_TYPE:
                        field.widget_config['display_format'] = timeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TIME_TYPE:
                        field.widget_config['display_format'] = dateTimeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TYPE:
                        field.widget_config['display_format'] = dateFormat

                if 'default_value_expression' in fielddef:
                    field.default_value_expression = fielddef['default_value_expression']

                layer.fields.append(field)

            layers.append(layer)

        return layers

    def relations(self, layers, filter_layer_list=[]):
        relations_info = self.get_relations_info(filter_layer_list)
        layer_map = dict()
        for layer in layers:
            if layer.name not in layer_map.keys():
                layer_map[layer.name] = list()
            layer_map[layer.name].append(layer)
        relations = list()

        for record in relations_info:
            if record['referencing_table'] in layer_map.keys() and record['referenced_table'] in layer_map.keys():
                for referencing_layer in layer_map[record['referencing_table']]:
                    for referenced_layer in layer_map[record['referenced_table']]:
                        relation = Relation()
                        relation.referencing_layer = referencing_layer
                        relation.referenced_layer = referenced_layer
                        relation.referencing_field = record['referencing_column']
                        relation.referenced_field = record['referenced_column']
                        relation.name = record['constraint_name']
                        relations.append(relation)

        # TODO: Remove these 3 lines when
        # https://github.com/claeis/ili2db/issues/19 is solved!
        domain_relations_generator = DomainRelationGenerator(
            self._db_connector, self.inheritance)
        domain_relations, bags_of_enum = domain_relations_generator.get_domain_relations_info(
            layers)
        relations = relations + domain_relations

        return (relations, bags_of_enum)

    def legend(self, layers, ignore_node_names=None):
        legend = LegendGroup(QCoreApplication.translate('LegendGroup', 'root'), ignore_node_names=ignore_node_names)
        tables = LegendGroup(
            QCoreApplication.translate('LegendGroup', 'tables'))
        domains = LegendGroup(QCoreApplication.translate(
            'LegendGroup', 'domains'), False)

        point_layers = []
        line_layers = []
        polygon_layers = []

        for layer in layers:
            if layer.geometry_column:
                geometry_type = QgsWkbTypes.geometryType(layer.wkb_type)
                if geometry_type == QgsWkbTypes.PointGeometry:
                    point_layers.append(layer)
                elif geometry_type == QgsWkbTypes.LineGeometry:
                    line_layers.append(layer)
                elif geometry_type == QgsWkbTypes.PolygonGeometry:
                    polygon_layers.append(layer)
            else:
                if layer.is_domain:
                    domains.append(layer)
                else:
                    tables.append(layer)

        for l in polygon_layers:
            legend.append(l)
        for l in line_layers:
            legend.append(l)
        for l in point_layers:
            legend.append(l)

        if not tables.is_empty():
            legend.append(tables)
        if not domains.is_empty():
            legend.append(domains)

        return legend

    def db_or_schema_exists(self):
        return self._db_connector.db_or_schema_exists()

    def metadata_exists(self):
        return self._db_connector.metadata_exists()

    def get_tables_info(self):
        return self._db_connector.get_tables_info()

    def get_meta_attrs(self, ili_name):
        return self._db_connector.get_meta_attrs(ili_name)

    def get_fields_info(self, table_name):
        return self._db_connector.get_fields_info(table_name)

    def get_tables_info_without_ignored_tables(self):
        tables_info = self.get_tables_info()
        new_tables_info = []
        for record in tables_info:
            if self.schema:
                if record['schemaname'] != self.schema:
                    continue
            elif record['schemaname'] in IGNORED_SCHEMAS:
                continue

            if record['tablename'] in IGNORED_TABLES:
                continue

            new_tables_info.append(record)

        return new_tables_info

    def get_constraints_info(self, table_name):
        return self._db_connector.get_constraints_info(table_name)

    def get_relations_info(self, filter_layer_list=[]):
        return self._db_connector.get_relations_info(filter_layer_list)
