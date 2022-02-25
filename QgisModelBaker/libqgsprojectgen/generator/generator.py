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

from qgis.core import QgsApplication, QgsRelation, QgsWkbTypes
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QObject, pyqtSignal

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libqgsprojectgen.dataobjects.fields import Field
from QgisModelBaker.libqgsprojectgen.dataobjects.layers import Layer
from QgisModelBaker.libqgsprojectgen.dataobjects.legend import LegendGroup
from QgisModelBaker.libqgsprojectgen.dataobjects.relations import Relation
from QgisModelBaker.utils.qt_utils import slugify

from ..db_factory.db_simple_factory import DbSimpleFactory
from .config import BASKET_FIELDNAMES, IGNORED_FIELDNAMES, READONLY_FIELDNAMES
from .domain_relations_generator import DomainRelationGenerator


class Generator(QObject):
    """Builds Model Baker objects from data extracted from databases."""

    stdout = pyqtSignal(str)
    new_message = pyqtSignal(int, str)

    def __init__(
        self,
        tool,
        uri,
        inheritance,
        schema=None,
        pg_estimated_metadata=False,
        parent=None,
        mgmt_uri=None,
        consider_basket_handling=False,
    ):
        """
        Creates a new Generator objects.
        :param uri: The uri that should be used in the resulting project. If authcfg is used, make sure the mgmt_uri is set as well.
        :param mgmt_uri: The uri that should be used to create schemas, tables and query meta information. Does not support authcfg.
        :consider_basket_handling: Makes the specific handling of basket tables depending if schema is created with createBasketCol.
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
        self.basket_handling = consider_basket_handling and self.get_basket_handling()

        self._additional_ignored_layers = (
            []
        )  # List of layers to ignore set by 3rd parties

        self.collected_print_messages = []

    def print_info(self, text):
        self.stdout.emit(text)

    def print_messages(self):
        for message in self.collected_print_messages:
            self.new_message.emit(message["level"], message["text"])
        self.collected_print_messages.clear()

    def append_print_message(self, level, text):
        message = {"level": level, "text": text}

        if message not in self.collected_print_messages:
            self.collected_print_messages.append(message)

    def layers(self, filter_layer_list=[]):
        ignore_basket_tables = not self.basket_handling
        tables_info = self.get_tables_info_without_ignored_tables(ignore_basket_tables)
        layers = list()

        db_factory = self.db_simple_factory.create_factory(self.tool)

        layer_uri = db_factory.get_layer_uri(self.uri)
        layer_uri.pg_estimated_metadata = self.pg_estimated_metadata

        # When a table has multiple geometry columns, it will be loaded multiple times (supported e.g. by PostGIS).
        table_appearance_count = {}

        for record in tables_info:
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue
            if filter_layer_list and record["tablename"] not in filter_layer_list:
                continue
            table_appearance_count[record["tablename"]] = (
                table_appearance_count.get(record["tablename"], 0) + 1
            )

        for record in tables_info:
            # When in PostGIS mode, leaving schema blank should load tables from
            # all schemas, except the ignored ones
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue

            if filter_layer_list and record["tablename"] not in filter_layer_list:
                continue

            is_domain = (
                record.get("kind_settings") == "ENUM"
                or record.get("kind_settings") == "CATALOGUE"
            )
            is_attribute = bool(record.get("attribute_name"))
            is_structure = record.get("kind_settings") == "STRUCTURE"
            is_nmrel = record.get("kind_settings") == "ASSOCIATION"
            # when the basket handling is not considered we do not consider tables named as basket tables consider as basket tables
            is_basket_table = self.basket_handling and (
                record.get("tablename") == self._db_connector.basket_table_name
            )
            is_dataset_table = self.basket_handling and (
                record.get("tablename") == self._db_connector.dataset_table_name
            )

            alias = record["table_alias"] if "table_alias" in record else None
            if not alias:
                short_name = None
                if is_domain and is_attribute:
                    short_name = ""
                    if "ili_name" in record and record["ili_name"]:
                        short_name = (
                            record["ili_name"].split(".")[-2]
                            + "_"
                            + record["ili_name"].split(".")[-1]
                        )
                else:
                    if (
                        table_appearance_count[record["tablename"]] > 1
                        and "geometry_column" in record
                    ):
                        # multiple layers for this table - append geometry column to name
                        fields_info = self.get_fields_info(record["tablename"])
                        for field_info in fields_info:
                            if field_info["column_name"] == record["geometry_column"]:
                                if (
                                    "fully_qualified_name" in field_info
                                    and field_info["fully_qualified_name"]
                                ):
                                    short_name = (
                                        field_info["fully_qualified_name"].split(".")[
                                            -2
                                        ]
                                        + " ("
                                        + field_info["fully_qualified_name"].split(".")[
                                            -1
                                        ]
                                        + ")"
                                    )
                                else:
                                    short_name = record["tablename"]
                    elif "ili_name" in record and record["ili_name"]:
                        match = re.search(r"([^\(]*).*", record["ili_name"])
                        if match.group(0) == match.group(1):
                            short_name = match.group(1).split(".")[-1]
                        else:
                            # additional brackets in the the name - extended layer in geopackage
                            short_name = (
                                match.group(1).split(".")[-2]
                                + " ("
                                + match.group(1).split(".")[-1]
                                + ")"
                            )
                alias = short_name

            model_topic_name = ""
            if "ili_name" in record and record["ili_name"]:
                if record["ili_name"].count(".") > 1:
                    model_topic_name = f"{record['ili_name'].split('.')[0]}.{record['ili_name'].split('.')[1]}"

            display_expression = ""
            if is_basket_table:
                display_expression = "coalesce(attribute(get_feature('{dataset_layer_name}', '{tid}', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('{dataset_layer_name}', '{tid}', dataset), 'datasetname'), {tilitid}))".format(
                    tid=self._db_connector.tid,
                    tilitid=self._db_connector.tilitid,
                    dataset_layer_name=self._db_connector.dataset_table_name,
                )
            elif "ili_name" in record and record["ili_name"]:
                meta_attrs = self.get_meta_attrs(record["ili_name"])
                for attr_record in meta_attrs:
                    if attr_record["attr_name"] == "dispExpression":
                        display_expression = attr_record["attr_value"]

            coord_decimals = (
                record["coord_decimals"] if "coord_decimals" in record else None
            )
            coordinate_precision = None
            if coord_decimals:
                coordinate_precision = 1 / (10 ** coord_decimals)

            layer = Layer(
                layer_uri.provider,
                layer_uri.get_data_source_uri(record),
                record["tablename"],
                record["srid"],
                record["extent"] if "extent" in record else None,
                record["geometry_column"],
                QgsWkbTypes.parseType(record["type"]) or QgsWkbTypes.Unknown,
                alias,
                is_domain,
                is_structure,
                is_nmrel,
                display_expression,
                coordinate_precision,
                is_basket_table,
                is_dataset_table,
                model_topic_name,
            )

            # Configure fields for current table
            fields_info = self.get_fields_info(record["tablename"])
            min_max_info = self.get_min_max_info(record["tablename"])
            value_map_info = self.get_value_map_info(record["tablename"])
            re_iliname = re.compile(r".*\.(.*)$")

            for fielddef in fields_info:
                column_name = fielddef["column_name"]
                fully_qualified_name = (
                    fielddef["fully_qualified_name"]
                    if "fully_qualified_name" in fielddef
                    else None
                )
                m = (
                    re_iliname.match(fully_qualified_name)
                    if fully_qualified_name
                    else None
                )

                alias = None
                if "column_alias" in fielddef:
                    alias = fielddef["column_alias"]
                if m and not alias:
                    alias = m.group(1)

                field = Field(column_name)
                field.alias = alias

                # Should we hide the field?
                hide_attribute = False

                if "fully_qualified_name" in fielddef:
                    fully_qualified_name = fielddef["fully_qualified_name"]
                    if fully_qualified_name:
                        meta_attrs_column = self.get_meta_attrs(fully_qualified_name)

                        for attr_record in meta_attrs_column:
                            if attr_record["attr_name"] == "hidden":
                                if attr_record["attr_value"] == "True":
                                    hide_attribute = True
                                    break

                if column_name in IGNORED_FIELDNAMES:
                    hide_attribute = True

                if not self.basket_handling and column_name in BASKET_FIELDNAMES:
                    hide_attribute = True

                field.hidden = hide_attribute

                if column_name in READONLY_FIELDNAMES:
                    field.read_only = True

                if column_name in min_max_info:
                    field.widget = "Range"
                    field.widget_config["Min"] = min_max_info[column_name][0]
                    field.widget_config["Max"] = min_max_info[column_name][1]
                    if "numeric_scale" in fielddef:
                        field.widget_config["Step"] = pow(
                            10, -1 * fielddef["numeric_scale"]
                        )
                    # field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''
                    if "unit" in fielddef and fielddef["unit"] is not None:
                        field.alias = "{alias} [{unit}]".format(
                            alias=alias or column_name, unit=fielddef["unit"]
                        )

                if column_name in value_map_info:
                    field.widget = "ValueMap"
                    field.widget_config["map"] = [
                        {val: val} for val in value_map_info[column_name]
                    ]

                if "attr_mapping" in fielddef and fielddef["attr_mapping"] == "ARRAY":
                    field.widget = "List"

                if "texttype" in fielddef and fielddef["texttype"] == "MTEXT":
                    field.widget = "TextEdit"
                    field.widget_config["IsMultiline"] = True

                data_type = self._db_connector.map_data_types(fielddef["data_type"])
                if "time" in data_type or "date" in data_type:
                    field.widget = "DateTime"
                    field.widget_config["calendar_popup"] = True

                    dateFormat = QLocale(QgsApplication.instance().locale()).dateFormat(
                        QLocale.ShortFormat
                    )
                    timeFormat = QLocale(QgsApplication.instance().locale()).timeFormat(
                        QLocale.ShortFormat
                    )
                    dateTimeFormat = QLocale(
                        QgsApplication.instance().locale()
                    ).dateTimeFormat(QLocale.ShortFormat)

                    if data_type == self._db_connector.QGIS_TIME_TYPE:
                        field.widget_config["display_format"] = timeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TIME_TYPE:
                        field.widget_config["display_format"] = dateTimeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TYPE:
                        field.widget_config["display_format"] = dateFormat

                db_factory.customize_widget_editor(field, data_type)

                if "default_value_expression" in fielddef:
                    field.default_value_expression = fielddef[
                        "default_value_expression"
                    ]

                if self.basket_handling and column_name in BASKET_FIELDNAMES:
                    if self.tool in [
                        DbIliMode.pg,
                        DbIliMode.ili2pg,
                        DbIliMode.mssql,
                        DbIliMode.ili2mssql,
                    ]:
                        schema_topic_identificator = slugify(
                            f"{layer.source().host()}_{layer.source().database()}_{layer.source().schema()}_{model_topic_name}"
                        )
                        field.default_value_expression = (
                            f"@{schema_topic_identificator}"
                        )
                    elif self.tool in [DbIliMode.ili2gpkg, DbIliMode.gpkg]:
                        schema_topic_identificator = slugify(
                            f"@{layer.source().uri().split('|')[0].strip()}_{model_topic_name}"
                        )
                        field.default_value_expression = (
                            f"@{schema_topic_identificator}"
                        )

                if "enum_domain" in fielddef and fielddef["enum_domain"]:
                    field.enum_domain = fielddef["enum_domain"]

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

        classname_info = [
            record["iliname"] for record in self.get_iliname_dbname_mapping()
        ]

        for record in relations_info:
            if (
                record["referencing_table"] in layer_map.keys()
                and record["referenced_table"] in layer_map.keys()
            ):
                for referencing_layer in layer_map[record["referencing_table"]]:
                    for referenced_layer in layer_map[record["referenced_table"]]:
                        relation = Relation()
                        relation.referencing_layer = referencing_layer
                        relation.referenced_layer = referenced_layer
                        relation.referencing_field = record["referencing_column"]
                        relation.referenced_field = record["referenced_column"]
                        relation.name = record["constraint_name"]
                        relation.strength = (
                            QgsRelation.Composition
                            if "strength" in record
                            and record["strength"] == "COMPOSITE"
                            else QgsRelation.Association
                        )

                        # For domain-class relations, if we have an extended domain, get its child name
                        child_name = None
                        if referenced_layer.is_domain:
                            # Get child name (if domain is extended)
                            fields = [
                                field
                                for field in referencing_layer.fields
                                if field.name == record["referencing_column"]
                            ]
                            if fields:
                                field = fields[0]
                                if (
                                    field.enum_domain
                                    and field.enum_domain not in classname_info
                                ):
                                    child_name = field.enum_domain
                        relation.child_domain_name = child_name

                        relations.append(relation)

        if self._db_connector.ili_version() == 3:
            # Used for ili2db version 3 relation creation
            domain_relations_generator = DomainRelationGenerator(
                self._db_connector, self.inheritance
            )
            (
                domain_relations,
                bags_of_enum,
            ) = domain_relations_generator.get_domain_relations_info(layers)
            relations = relations + domain_relations
        else:
            # Create the bags_of_enum structure
            bags_of_info = self.get_bags_of_info()
            bags_of_enum = {}
            for record in bags_of_info:
                for layer in layers:
                    if record["current_layer_name"] == layer.name:
                        new_item_list = [
                            layer,
                            record["cardinality_min"]
                            + ".."
                            + record["cardinality_max"],
                            layer_map[record["target_layer_name"]][0],
                            self._db_connector.tid,
                            self._db_connector.dispName,
                        ]
                        unique_current_layer_name = "{}_{}".format(
                            record["current_layer_name"], layer.geometry_column
                        )
                        if unique_current_layer_name in bags_of_enum.keys():
                            bags_of_enum[unique_current_layer_name][
                                record["attribute"]
                            ] = new_item_list
                        else:
                            bags_of_enum[unique_current_layer_name] = {
                                record["attribute"]: new_item_list
                            }
        return (relations, bags_of_enum)

    def full_node(self, layers, item):
        current_node = None
        if item and isinstance(item, dict):
            current_node_name = next(iter(item))
            item_properties = item[current_node_name]
            if (
                item_properties
                and "group" in item_properties
                and item_properties["group"]
            ):
                current_node = LegendGroup(
                    QCoreApplication.translate("LegendGroup", current_node_name),
                    static_sorting=True,
                )
                current_node.expanded = (
                    False
                    if "expanded" in item_properties and not item_properties["expanded"]
                    else True
                )
                current_node.checked = (
                    False
                    if "checked" in item_properties and not item_properties["checked"]
                    else True
                )
                current_node.mutually_exclusive = (
                    True
                    if "mutually-exclusive" in item_properties
                    and item_properties["mutually-exclusive"]
                    else False
                )
                if current_node.mutually_exclusive:
                    current_node.mutually_exclusive_child = (
                        item_properties["mutually-exclusive-child"]
                        if "mutually-exclusive-child" in item_properties
                        else -1
                    )

                if "child-nodes" in item_properties:
                    for child_item in item_properties["child-nodes"]:
                        node = self.full_node(layers, child_item)
                        if node:
                            current_node.append(node)
            else:
                for layer in layers:
                    if layer.alias == current_node_name:
                        current_node = layer
                        if item_properties:
                            current_node.expanded = (
                                False
                                if "expanded" in item_properties
                                and not item_properties["expanded"]
                                else True
                            )
                            current_node.checked = (
                                False
                                if "checked" in item_properties
                                and not item_properties["checked"]
                                else True
                            )
                            current_node.featurecount = (
                                True
                                if "featurecount" in item_properties
                                and item_properties["featurecount"]
                                else False
                            )
                        break
        return current_node

    def legend(self, layers, ignore_node_names=None, layertree_structure=None):
        legend = LegendGroup(
            QCoreApplication.translate("LegendGroup", "root"),
            ignore_node_names=ignore_node_names,
            static_sorting=layertree_structure is not None,
        )
        if layertree_structure:
            for item in layertree_structure:
                node = self.full_node(layers, item)
                if node:
                    legend.append(node)
        else:
            tables = LegendGroup(QCoreApplication.translate("LegendGroup", "tables"))
            domains = LegendGroup(QCoreApplication.translate("LegendGroup", "domains"))
            domains.expanded = False
            system = LegendGroup(QCoreApplication.translate("LegendGroup", "system"))
            system.expanded = False

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
                    elif layer.name in [
                        self._db_connector.basket_table_name,
                        self._db_connector.dataset_table_name,
                    ]:
                        system.append(layer)
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
            if not system.is_empty():
                legend.append(system)

        return legend

    def db_or_schema_exists(self):
        return self._db_connector.db_or_schema_exists()

    def metadata_exists(self):
        return self._db_connector.metadata_exists()

    def set_additional_ignored_layers(self, layer_list):
        self._additional_ignored_layers = layer_list

    def get_ignored_layers(self, ignore_basket_tables=True):
        return (
            self._db_connector.get_ignored_layers(ignore_basket_tables)
            + self._additional_ignored_layers
        )

    def get_tables_info(self):
        return self._db_connector.get_tables_info()

    def get_meta_attrs_info(self):
        return self._db_connector.get_meta_attrs_info()

    def get_meta_attrs(self, ili_name):
        return self._db_connector.get_meta_attrs(ili_name)

    def get_fields_info(self, table_name):
        return self._db_connector.get_fields_info(table_name)

    def get_tables_info_without_ignored_tables(self, ignore_basket_tables=True):
        tables_info = self.get_tables_info()
        ignored_layers = self.get_ignored_layers(ignore_basket_tables)
        new_tables_info = []
        for record in tables_info:
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue

            if ignored_layers and record["tablename"] in ignored_layers:
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

    def get_basket_handling(self):
        return self._db_connector.get_basket_handling()
