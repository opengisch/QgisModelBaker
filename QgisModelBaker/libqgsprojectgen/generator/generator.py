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
import sys

from qgis.core import QgsProviderRegistry, QgsWkbTypes, QgsApplication, QgsRelation
from qgis.PyQt.QtCore import QCoreApplication, QLocale

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libqgsprojectgen.dataobjects import Field
from QgisModelBaker.libqgsprojectgen.dataobjects import LegendGroup
from QgisModelBaker.libqgsprojectgen.dataobjects.layers import Layer
from QgisModelBaker.libqgsprojectgen.dataobjects.relations import Relation
from ..dbconnector import pg_connector, gpkg_connector
from .domain_relations_generator import DomainRelationGenerator
from .config import IGNORED_FIELDNAMES, READONLY_FIELDNAMES
from ..db_factory.db_simple_factory import DbSimpleFactory
from qgis.PyQt.QtCore import QObject, pyqtSignal


class Generator(QObject):
    """Builds Model Baker objects from data extracted from databases."""

    stdout = pyqtSignal(str)
    new_message = pyqtSignal(int, str)

    def __init__(self, tool, uri, inheritance, schema=None, pg_estimated_metadata=False, parent=None, mgmt_uri=None):
        """
        Creates a new Generator objects.
        :param uri: The uri that should be used in the resulting project. If authcfg is used, make sure the mgmt_uri is set as well.
        :param mgmt_uri: The uri that should be used to create schemas, tables and query meta information. Does not support authcfg.
        """
        QObject.__init__(self, parent)
        self.tool = tool
        self.uri = uri
        self.mgmt_uri = mgmt_uri
        self.inheritance = inheritance
        self.schema = schema or None
        self.pg_estimated_metadata = pg_estimated_metadata

        self.db_simple_factory = DbSimpleFactory()
        db_factory = self.db_simple_factory.create_factory(self.tool)
        self._db_connector = db_factory.get_db_connector(mgmt_uri or uri, schema)
        self._db_connector.stdout.connect(self.print_info)
        self._db_connector.new_message.connect(self.append_print_message)

        self._additional_ignored_layers = []  # List of layers to ignore set by 3rd parties

        self.collected_print_messages = []

    def print_info(self, text):
        self.stdout.emit(text)

    def print_messages(self):
        for message in self.collected_print_messages:
            self.new_message.emit(message["level"], message["text"])
        self.collected_print_messages.clear()

    def append_print_message(self, level, text):
        message = {'level': level, 'text': text}

        if message not in self.collected_print_messages:
            self.collected_print_messages.append(message)

    def layers(self, filter_layer_list=[]):
        ignored_layers = self.get_ignored_layers()
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

            if ignored_layers and record['tablename'] in ignored_layers:
                continue

            if filter_layer_list and record['tablename'] not in filter_layer_list:
                continue

            is_domain = record['kind_settings'] == 'ENUM' or record[
                'kind_settings'] == 'CATALOGUE' if 'kind_settings' in record else False
            is_attribute = bool(record['attribute_name']) if 'attribute_name' in record else False
            is_structure = record['kind_settings'] == 'STRUCTURE' if 'kind_settings' in record else False
            is_nmrel = record['kind_settings'] == 'ASSOCIATION' if 'kind_settings' in record else False

            alias = record['table_alias'] if 'table_alias' in record else None
            if not alias:
                if is_domain and is_attribute:
                    short_name = record['ili_name'].split('.')[-2] + '_' + record['ili_name'].split('.')[-1] if 'ili_name' in record else ''
                else:
                    short_name = record['ili_name'].split('.')[-1] if 'ili_name' in record else ''
                alias = short_name

            display_expression = ''
            if 'ili_name' in record:
                meta_attrs = self.get_meta_attrs(record['ili_name'])
                for attr_record in meta_attrs:
                    if attr_record['attr_name'] == 'dispExpression':
                        display_expression = attr_record['attr_value']

            coord_decimals = record['coord_decimals'] if 'coord_decimals' in record else None
            coordinate_precision = None
            if coord_decimals:
                coordinate_precision = 1 / (10 ** coord_decimals)

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
                display_expression,
                coordinate_precision )

            # Configure fields for current table
            fields_info = self.get_fields_info(record['tablename'])
            min_max_info = self.get_min_max_info(record['tablename'])
            value_map_info = self.get_value_map_info(record['tablename'])
            re_iliname = re.compile(r'.*\.(.*)$')

            for fielddef in fields_info:
                column_name = fielddef['column_name']
                fully_qualified_name = fielddef['fully_qualified_name'] if 'fully_qualified_name' in fielddef else None
                m = re_iliname.match(fully_qualified_name) if fully_qualified_name else None

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

                if column_name in min_max_info:
                    field.widget = 'Range'
                    field.widget_config['Min'] = min_max_info[column_name][0]
                    field.widget_config['Max'] = min_max_info[column_name][1]
                    if 'numeric_scale' in fielddef:
                        field.widget_config['Step'] = pow(10, -1 * fielddef['numeric_scale'])
                    # field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''
                    if 'unit' in fielddef and fielddef['unit'] is not None:
                        field.alias = '{alias} [{unit}]'.format(
                            alias=alias or column_name, unit=fielddef['unit'])

                if column_name in value_map_info:
                    field.widget = 'ValueMap'
                    field.widget_config['map'] = [{val: val} for val in value_map_info[column_name]]

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

                db_factory.customize_widget_editor(field, data_type)

                if 'default_value_expression' in fielddef:
                    field.default_value_expression = fielddef['default_value_expression']

                if 'enum_domain' in fielddef and fielddef['enum_domain']:
                    field.enum_domain = fielddef['enum_domain']

                layer.fields.append(field)

            layers.append(layer)

        self.print_messages()

        return layers

    def relations(self, layers, filter_layer_list=[]):
        relations_info = self.get_relations_info(filter_layer_list)
        layer_map = dict()
        for layer in layers:
            if layer.name not in layer_map.keys():
                layer_map[layer.name] = list()
            layer_map[layer.name].append(layer)
        relations = list()

        classname_info = [record['iliname'] for record in self.get_iliname_dbname_mapping()]

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
                        relation.strength = QgsRelation.Composition if 'strength' in record and record['strength'] == 'COMPOSITE' else QgsRelation.Association

                        # For domain-class relations, if we have an extended domain, get its child name
                        child_name = None
                        if referenced_layer.is_domain:
                            # Get child name (if domain is extended)
                            fields = [field for field in referencing_layer.fields if field.name == record['referencing_column']]
                            if fields:
                                field = fields[0]
                                if field.enum_domain and field.enum_domain not in classname_info:
                                    child_name = field.enum_domain
                        relation.child_domain_name = child_name

                        relations.append(relation)

        if self._db_connector.ili_version() == 3:
            # Used for ili2db version 3 relation creation
            domain_relations_generator = DomainRelationGenerator(
                self._db_connector, self.inheritance)
            domain_relations, bags_of_enum = domain_relations_generator.get_domain_relations_info(
                layers)
            relations = relations + domain_relations
        else:
            # Create the bags_of_enum structure
            bags_of_info = self.get_bags_of_info()
            bags_of_enum = {}
            for record in bags_of_info:
                for layer in layers:
                    if record['current_layer_name'] == layer.name:
                        new_item_list = [layer,
                                         record['cardinality_min'] + '..' + record['cardinality_max'],
                                         layer_map[record['target_layer_name']][0],
                                         self._db_connector.tid,
                                         self._db_connector.dispName]
                        unique_current_layer_name = '{}_{}'.format(record['current_layer_name'], layer.geometry_column)
                        if unique_current_layer_name in bags_of_enum.keys():
                            bags_of_enum[unique_current_layer_name][record['attribute']] = new_item_list
                        else:
                            bags_of_enum[unique_current_layer_name] = {record['attribute']: new_item_list}
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

    def set_additional_ignored_layers(self, layer_list):
        self._additional_ignored_layers = layer_list

    def get_ignored_layers(self):
        return self._db_connector.get_ignored_layers() + self._additional_ignored_layers

    def get_tables_info(self):
        return self._db_connector.get_tables_info()

    def get_meta_attrs_info(self):
        return self._db_connector.get_meta_attrs_info()

    def get_meta_attrs(self, ili_name):
        return self._db_connector.get_meta_attrs(ili_name)

    def get_fields_info(self, table_name):
        return self._db_connector.get_fields_info(table_name)

    def get_tables_info_without_ignored_tables(self):
        tables_info = self.get_tables_info()
        ignored_layers = self.get_ignored_layers()
        new_tables_info = []
        for record in tables_info:
            if self.schema:
                if record['schemaname'] != self.schema:
                    continue

            if ignored_layers and record['tablename'] in ignored_layers:
                continue

            new_tables_info.append(record)

        return new_tables_info

    def get_min_max_info(self, table_name):
        return self._db_connector.get_min_max_info(table_name)

    def get_value_map_info(self, table_name):
        return self._db_connector.get_value_map_info(table_name)

    def get_relations_info(self, filter_layer_list=[]):
        return self._db_connector.get_relations_info(filter_layer_list)

    def get_bags_of_info(self):
        return self._db_connector.get_bags_of_info()

    def get_iliname_dbname_mapping(self):
        return self._db_connector.get_iliname_dbname_mapping()
