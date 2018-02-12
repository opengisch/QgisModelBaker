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

from projectgenerator.libqgsprojectgen.dataobjects import Field
from projectgenerator.libqgsprojectgen.dataobjects import LegendGroup
from projectgenerator.libqgsprojectgen.dataobjects.layers import Layer
from projectgenerator.libqgsprojectgen.dataobjects.relations import Relation
from ..dbconnector import pg_connector, gpkg_connector
from .config import IGNORED_SCHEMAS, IGNORED_TABLES, IGNORED_FIELDNAMES, READONLY_FIELDNAMES


class Generator:
    """Builds Project Generator objects from data extracted from databases."""

    def __init__(self, tool_name, uri, inheritance, schema=None):
        self.tool_name = tool_name
        self.uri = uri
        self.inheritance = inheritance
        self.schema = schema or None
        if self.tool_name == 'ili2pg':
            self._db_connector = pg_connector.PGConnector(uri, schema)
        elif self.tool_name == 'ili2gpkg':
            self._db_connector = gpkg_connector.GPKGConnector(uri, None)

    def layers(self, filter_layer_list=[]):
        tables_info = self._get_tables_info()
        layers = list()

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

            if self.tool_name == 'ili2pg':
                provider = 'postgres'
                if record['geometry_column']:
                    data_source_uri = '{uri} key={primary_key} estimatedmetadata=true srid={srid} type={type} table="{schema}"."{table}" ({geometry_column})'.format(
                        uri=self.uri,
                        primary_key=record['primary_key'],
                        srid=record['srid'],
                        type=record['type'],
                        schema=record['schemaname'],
                        table=record['tablename'],
                        geometry_column=record['geometry_column']
                    )
                else:
                    data_source_uri = '{uri} key={primary_key} table="{schema}"."{table}"'.format(
                        uri=self.uri,
                        primary_key=record['primary_key'],
                        schema=record['schemaname'],
                        table=record['tablename']
                    )
            elif self.tool_name == 'ili2gpkg':
                provider = 'ogr'
                data_source_uri = '{uri}|layername={table}'.format(
                    uri=self.uri,
                    table=record['tablename']
                )

            alias = record['table_alias'] if 'table_alias' in record else ''
            is_domain = record['is_domain'] == 'ENUM' or record[
                'is_domain'] == 'CATALOGUE' if 'is_domain' in record else False
            layer = Layer(provider,
                          data_source_uri,
                          record['tablename'],
                          record['geometry_column'],
                          QgsWkbTypes.parseType(
                              record['type']) or QgsWkbTypes.Unknown,
                          alias,
                          is_domain)

            # Configure fields for current table
            fields_info = self._get_fields_info(record['tablename'])
            constraints_info = self._get_constraints_info(record['tablename'])
            re_iliname = re.compile('^@iliname (.*)$')

            for fielddef in fields_info:
                column_name = fielddef['column_name']
                comment = fielddef['comment']
                m = re_iliname.match(comment) if comment else None
                alias = fielddef['column_alias']
                if m and not alias:
                    alias = m.group(1)

                field = Field(column_name)
                field.alias = alias

                if column_name in IGNORED_FIELDNAMES:
                    field.widget = 'Hidden'

                if column_name in READONLY_FIELDNAMES:
                    field.read_only = True

                if column_name in constraints_info:
                    field.widget = 'Range'
                    field.widget_config[
                        'Min'] = constraints_info[column_name][0]
                    field.widget_config[
                        'Max'] = constraints_info[column_name][1]
                    # field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''
                    if 'unit' in fielddef:
                        field.alias = '{alias} [{unit}]'.format(
                            alias=alias, unit=fielddef['unit'])

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

                layer.fields.append(field)

            layers.append(layer)

        return layers

    def relations(self, layers, filter_layer_list=[]):
        relations_info = self._get_relations_info(filter_layer_list)
        mapped_layers = {layer.name: layer for layer in layers}
        relations = list()

        for record in relations_info:
            if record['referencing_table'] in mapped_layers.keys() and record[
                    'referenced_table'] in mapped_layers.keys():
                relation = Relation()
                relation.referencing_layer = mapped_layers[
                    record['referencing_table']]
                relation.referenced_layer = mapped_layers[
                    record['referenced_table']]
                relation.referencing_field = record['referencing_column']
                relation.referenced_field = record['referenced_column']
                relation.name = record['constraint_name']
                relations.append(relation)

        # TODO: Remove these 3 lines when
        # https://github.com/claeis/ili2db/issues/19 is solved!
        domain_relations_generator = DomainRelationGenerator(
            self._db_connector, self.inheritance)
        domain_relations = domain_relations_generator.get_domain_relations_info(
            layers)
        relations = relations + domain_relations

        return relations

    def legend(self, layers):
        legend = LegendGroup(QCoreApplication.translate('LegendGroup', 'root'))
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

        for l in point_layers:
            legend.append(l)
        for l in line_layers:
            legend.append(l)
        for l in polygon_layers:
            legend.append(l)

        if not tables.is_empty():
            legend.append(tables)
        if not domains.is_empty():
            legend.append(domains)

        return legend

    def _metadata_exists(self):
        return self._db_connector.metadata_exists()

    def _get_tables_info(self):
        return self._db_connector.get_tables_info()

    def _get_fields_info(self, table_name):
        return self._db_connector.get_fields_info(table_name)

    def _get_constraints_info(self, table_name):
        return self._db_connector.get_constraints_info(table_name)

    def _get_relations_info(self, filter_layer_list=[]):
        return self._db_connector.get_relations_info(filter_layer_list)


class DomainRelationGenerator:
    """TODO: remove when ili2db issue #19 is solved"""

    def __init__(self, db_connector, inheritance):
        self._db_connector = db_connector
        self.inheritance = inheritance
        self.debug = False

    def get_domain_relations_info(self, layers):
        domains = [layer.name for layer in layers if layer.is_domain]
        if self.debug:
            print("domains:", domains)
        if not domains:
            return []

        mapped_layers = {layer.name: layer for layer in layers}
        domainili_domaindb_mapping = self._get_domainili_domaindb_mapping(
            domains)
        domains_ili_pg = dict()
        for record in domainili_domaindb_mapping:
            domains_ili_pg[record['iliname']] = record['sqlname']
        if self.debug:
            print("domains_ili_pg:", domains_ili_pg)

        model_records = self._get_models()
        models = dict()
        models_info = dict()
        extended_classes = dict()
        for record in model_records:
            models[record['modelname'].split("{")[0]] = record['content']

        for k, v in models.items():
            parsed = self.parse_model(v, list(domains_ili_pg.keys()))
            models_info.update(parsed[0])
            extended_classes.update(parsed[1])
        if self.debug:
            print("Classes with domain attrs:", len(models_info))

        # Map class ili name with its correspondent pg name
        # Take into account classes with domain attrs and those that extend other classes,
        # because parent classes might have domain attrs that will be
        # transfered to children
        class_records = self._get_classili_classdb_mapping(
            models_info, extended_classes)
        classes_ili_pg = dict()
        for record in class_records:
            classes_ili_pg[record['iliname']] = record['sqlname']
        if self.debug:
            print("classes_ili_pg:", classes_ili_pg)

        # Now deal with extended classes
        models_info_with_ext = {}
        for iliclass in models_info:
            models_info_with_ext[iliclass] = self.get_ext_dom_attrs(iliclass, models_info, extended_classes,
                                                                    self.inheritance)
        for iliclass in extended_classes:
            if iliclass not in models_info_with_ext:
                # Take into account classes which only inherit attrs with domains, but don't have their own nor EXTEND attrs
                # Only relevant for smart2Inheritance, since for
                # smart1Inheritance this will return an empty dict {}
                models_info_with_ext[iliclass] = self.get_ext_dom_attrs(iliclass, models_info, extended_classes,
                                                                        self.inheritance)

        # Map attr ili name and owner (pg class name) with its correspondent
        # attr pg name
        attr_records = self._get_attrili_attrdb_mapping(models_info_with_ext)
        attrs_ili_pg_owner = dict()
        for record in attr_records:
            if record['owner'] in attrs_ili_pg_owner:
                attrs_ili_pg_owner[record['owner']].update(
                    {record['iliname']: record['sqlname']})
            else:
                attrs_ili_pg_owner[record['owner']] = {
                    record['iliname']: record['sqlname']}
        if self.debug:
            print("attrs_ili_pg_owner:", attrs_ili_pg_owner)

        # Create relations
        relations = list()
        attrs_ili = [k for v in attrs_ili_pg_owner.values() for k in v]
        for iliclass, dict_attr_domain in models_info_with_ext.items():
            for iliattr, ilidomain in dict_attr_domain.items():
                if iliclass in classes_ili_pg and ilidomain in domains_ili_pg and iliattr in attrs_ili:
                    if classes_ili_pg[iliclass] in mapped_layers and domains_ili_pg[ilidomain] in mapped_layers and \
                            classes_ili_pg[iliclass] in attrs_ili_pg_owner:
                        if iliattr in attrs_ili_pg_owner[classes_ili_pg[iliclass]]:
                            # Might be that due to ORM mapping, a class is not
                            # in mapped_layers
                            relation = Relation()
                            relation.referencing_layer = mapped_layers[
                                classes_ili_pg[iliclass]]
                            relation.referenced_layer = mapped_layers[
                                domains_ili_pg[ilidomain]]
                            relation.referencing_field = attrs_ili_pg_owner[
                                classes_ili_pg[iliclass]][iliattr]
                            relation.referenced_field = self._db_connector.iliCodeName
                            relation.name = "{}_{}_{}_{}".format(classes_ili_pg[iliclass],
                                                                 attrs_ili_pg_owner[
                                                                     classes_ili_pg[iliclass]][iliattr],
                                                                 domains_ili_pg[
                                                                     ilidomain],
                                                                 self._db_connector.iliCodeName)

                            if self.debug:
                                print("Relation:", relation.name)
                            relations.append(relation)

        if self.debug:
            print("final_models_info:", models_info_with_ext)
        if self.debug:
            print("extended_classes:", extended_classes)
        if self.debug:
            print("Num of Relations:", len(relations))

        return relations

    def parse_model(self, model_content, domains):
        # MODEL Catastro_COL_ES_V_2_0_20170331 (es)
        re_model = re.compile('\s*MODEL\s*([\w\d_-]+).*')
        # TOPIC Catastro_Registro [=]
        re_topic = re.compile('\s*TOPIC\s*([\w\d_-]+).*')
        re_class = re.compile(
            '\s*CLASS\s*([\w\d_-]+)\s*[EXTENDS]*\s*([\w\d_-]*).*')  # CLASS ClassName [EXTENDS] [BaseClassName] [=]
        re_class_extends = re.compile(
            '\s*EXTENDS\s*([\w\d_\-\.]+)\s*\=.*')  # EXTENDS BaseClassName =
        re_end_class = None  # END ClassName;
        re_end_topic = None  # END TopicName;
        re_end_model = None  # END ModelName;

        current_model = ''
        current_topic = ''
        current_class = ''
        attributes = dict()
        models_info = dict()
        extended_classes = dict()
        bClassJustFound = False  # Flag to search for EXTENDS classes
        local_names = dict()

        for line in model_content.splitlines():
            if not current_model:
                result = re_model.search(line)
                if result:
                    current_model = result.group(1)
                    re_end_model = re.compile(
                        '.*END\s*{}\..*'.format(current_model))  # END TopicName;
            else:  # The is a current_model
                if not current_topic:
                    result = re_topic.search(line)
                    if result:
                        current_topic = result.group(1)
                        if self.debug:
                            print("Topic encontrada", current_topic)
                        re_end_topic = re.compile(
                            '\s*END\s*{};.*'.format(current_topic))  # END TopicName;

                        local_names = self.extract_local_names_from_domains(
                            domains, current_model, current_topic)
                        domains_with_local = [name for name_list in local_names.values() for name in
                                              name_list] + domains
                        if self.debug:
                            print("domains_with_local:", domains_with_local)
                        continue
                else:  # There is a current_topic
                    if not current_class:  # Go for classes
                        result = re_class.search(line)
                        if result:
                            current_class = result.group(1)
                            if self.debug:
                                print("Class encontrada", current_class)
                            attributes = dict()
                            re_end_class = re.compile(
                                '\s*END\s*{};.*'.format(current_class))  # END ClassName;
                            bClassJustFound = True

                            # Possible EXTENDS
                            if len(result.groups()) > 1 and result.group(2):
                                extended_classes["{}.{}.{}".format(current_model, current_topic,
                                                                   current_class)] = self.make_full_qualified(
                                    result.group(2), 'class', current_model, current_topic)
                                if self.debug:
                                    print("EXTENDS->",
                                          self.make_full_qualified(result.group(2), 'class', current_model,
                                                                   current_topic))

                            continue
                    else:  # There is a current_class, go for attributes
                        if bClassJustFound:  # Search for extended classes
                            bClassJustFound = False
                            result = re_class_extends.search(line)
                            if result:
                                extended_classes["{}.{}.{}".format(current_model, current_topic,
                                                                   current_class)] = self.make_full_qualified(
                                    result.group(1), 'class', current_model, current_topic)
                                if self.debug:
                                    print("EXTENDS->",
                                          self.make_full_qualified(result.group(1), 'class', current_model,
                                                                   current_topic))
                                continue

                        attribute = {res.group(1): d for d in domains_with_local for res in
                                     [re.search('\s*([\w\d_-]+).*:.*\s{};.*'.format(d), line)] if res}

                        if attribute:
                            if self.debug:
                                print("MATCH:", attribute)
                            old_key = list(attribute.keys())[
                                0]  # Not qualified name
                            new_key = "{}.{}.{}.{}".format(current_model, current_topic, current_class,
                                                           old_key)  # Fully qualified name
                            attr_value = list(attribute.values())[0]
                            if attr_value not in domains:  # Match was vs. local name, find its corresponding qualified name
                                for k, v in local_names.items():
                                    if attr_value in v:
                                        attribute[old_key] = k
                                        break
                            attribute[new_key] = attribute.pop(old_key)
                            attributes.update(attribute)
                            continue

                        result = re_end_class.search(line)
                        if result:
                            if attributes:
                                models_info.update(
                                    {'{}.{}.{}'.format(current_model, current_topic, current_class): attributes})
                            if self.debug:
                                print("END Class encontrada", current_class)
                            current_class = ''
                            continue

                    result = re_end_topic.search(line)
                    if result:
                        current_topic = ''

                result = re_end_model.search(line)
                if result:
                    current_model = ''

        return [models_info, extended_classes]

    def extract_local_names_from_domains(self, domains, current_model, current_topic):
        """
        ili files may contain fully qualified domains assigned to attributes, but if
        domains are local (domain or topic-wise), domains might be assigned only
        with its name. This function builds local names (with no model and topic
        name, or without model name) for each domain name in 'domains' input. For
        instance: from a domain name "MODEL.TOPIC.DOMAIN", this function returns
        {MODEL: [DOMAIN, TOPIC.DOMAIN]} Order is relevant, since later matches in a
        search will overwrite previous ones (better to preserve more-qualified
        matches).
        """
        local_names = dict()
        for domain in domains:
            local_names_list = list()
            if domain.startswith('{}.'.format(current_model)) or domain.startswith(
                    '{}.{}.'.format(current_model, current_topic)):
                array = domain.split(".")
                if len(array) > 0:
                    local_names_list.append(array[-1])
                if len(array) > 1:
                    local_names_list.append(
                        '{}.{}'.format(array[-2], array[-1]))
                if local_names_list:
                    local_names[domain] = local_names_list
        return local_names

    def make_full_qualified(self, name, level, current_model, current_topic, current_class=None):
        parents = [current_model, current_topic, current_class]
        len_parents = len(parents)
        name_parts = name.split(".")
        # 3 levels (even 2, but not handling that case yet)
        if level == 'class':
            name_parts = parents[0:len_parents - len(name_parts)] + name_parts

        return ".".join(name_parts)

    def get_ext_dom_attrs(self, iliclass, models_info, extended_classes, inheritance):
        if inheritance == 'smart1':
            # Use smart 2 first to get domain attributes from parents (we
            # really need them) and only then use smart 1
            tmp_models_info = models_info
            if iliclass in tmp_models_info:
                tmp_models_info[iliclass].update(self.get_ext_dom_attrs_smart2(
                    iliclass, models_info, extended_classes))
            else:
                tmp_models_info[iliclass] = self.get_ext_dom_attrs_smart2(
                    iliclass, models_info, extended_classes)
            return self.get_ext_dom_attrs_smart1(iliclass, tmp_models_info, extended_classes)
        elif inheritance == 'smart2':
            return self.get_ext_dom_attrs_smart2(iliclass, models_info, extended_classes)
        else:  # No smart inheritance?
            return {}

    def get_ext_dom_attrs_smart1(self, iliclass, models_info, extended_classes):
        """
        Returns a dict for input iliclass with its original attr:domain pairs
        plus all attr:domain pairs from children classes
        """
        children_domain_attrS = dict()
        if iliclass in extended_classes.values():  # Does current class have children?
            for child, parent in extended_classes.items():  # Top-bottom, we might find several children
                if parent == iliclass:
                    children_domain_attrS.update(
                        self.get_ext_dom_attrs_smart1(child, models_info, extended_classes))  # Recursion
                    # In the last line, if two children share an atributte that
                    # is not in parent, the latest class visited will overwrite
                    # previously visited classes
        else:
            return models_info[iliclass] if iliclass in models_info else {}
        all_attrs = models_info[iliclass] if iliclass in models_info else {}

        for children_domain_attr, domain in children_domain_attrS.items():
            # smart1Inheritance: Pass child class attributes to parents, but
            # don't overwrite extended attrs
            if children_domain_attr not in all_attrs:
                all_attrs[children_domain_attr] = domain
        return all_attrs

    def get_ext_dom_attrs_smart2(self, iliclass, models_info, extended_classes):
        """
        Returns a dict for input iliclass with its original attr:domain pairs
        plus all inherited attr:domain pairs
        """
        if iliclass in extended_classes:  # Does current class have parents?
            parents_domain_attrS = self.get_ext_dom_attrs_smart2(extended_classes[iliclass], models_info,
                                                                 extended_classes)  # Recursion
        else:
            return models_info[iliclass] if iliclass in models_info else {}
        all_attrs = models_info[iliclass] if iliclass in models_info else {}

        unqualified_attrs = {k.split(".")[-1]: k for k in all_attrs.keys()}

        for parents_domain_attr, domain in parents_domain_attrS.items():
            # smart2Inheritance: Pass parent attributes to child if they are missing.
            # If they exist, overwrite keys (i.e., parent_domain_attr:
            # child_domain)
            parents_unqualified_attr = parents_domain_attr.split(".")[-1]

            if parents_unqualified_attr not in unqualified_attrs:
                all_attrs[parents_domain_attr] = domain
            else:  # Extended, use parent's attribute name with child domain name
                if unqualified_attrs[parents_unqualified_attr] in all_attrs:
                    tmpDomain = all_attrs[
                        unqualified_attrs[parents_unqualified_attr]]
                    del all_attrs[unqualified_attrs[parents_unqualified_attr]]
                    all_attrs[parents_domain_attr] = tmpDomain

        return all_attrs

    def _get_domainili_domaindb_mapping(self, domains):
        return self._db_connector.get_domainili_domaindb_mapping(domains)

    def _get_models(self):
        return self._db_connector.get_models()

    def _get_classili_classdb_mapping(self, models_info, extended_classes):
        return self._db_connector.get_classili_classdb_mapping(models_info, extended_classes)

    def _get_attrili_attrdb_mapping(self, models_info_with_ext):
        return self._db_connector.get_attrili_attrdb_mapping(models_info_with_ext)
