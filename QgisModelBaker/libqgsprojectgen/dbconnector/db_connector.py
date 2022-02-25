# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
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

from qgis.PyQt.QtCore import QObject, pyqtSignal

from .config import BASKET_TABLES, IGNORED_ILI_ELEMENTS, IGNORED_SCHEMAS, IGNORED_TABLES


class DBConnector(QObject):
    """SuperClass for all DB connectors."""

    stdout = pyqtSignal(str)
    new_message = pyqtSignal(int, str)

    def __init__(self, uri, schema, parent=None):
        QObject.__init__(self, parent)
        self.QGIS_DATE_TYPE = "date"
        self.QGIS_TIME_TYPE = "time"
        self.QGIS_DATE_TIME_TYPE = "datetime"
        self.iliCodeName = ""  # For Domain-Class relations, specific for each DB
        self.tid = ""  # For BAG OF config and basket handling, specific for each DB
        self.tilitid = ""  # For basket handling, specific for each DB
        self.dispName = ""  # For BAG OF config, specific for each DB
        self.basket_table_name = ""  # For basket handling, specific for each DB
        self.dataset_table_name = ""  # For basket handling, specific for each DB

    def map_data_types(self, data_type):
        """Map provider date/time types to QGIS date/time types"""
        return None

    def db_or_schema_exists(self):
        """Whether the DB (for GPKG) or schema (for PG) exists or not."""
        raise NotImplementedError

    def create_db_or_schema(self, usr):
        """Create the DB (for GPKG) or schema (for PG)"""
        raise NotImplementedError

    def metadata_exists(self):
        """Whether t_ili2db_table_prop table exists or not.
        In other words... Does the DB/Schema hold an Interlis model?
        """
        return False

    def get_tables_info(self):
        """
        Info about tables found in the database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                schemaname
                tablename
                primary_key
                geometry_column
                srid
                type  (Geometry Type)
                kind_settings
                ili_name
                extent [a string: "xmin;ymin;xmax;ymax"]
                table_alias
                model
        """
        return []

    def get_meta_attrs_info(self):
        """
        Info about meta attributes

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                ilielement
                attr_name
                attr_value
        """
        raise NotImplementedError

    def get_meta_attr(self, ili_name):
        """
        Info about meta attributes of a given ili element

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                attr_name
                attr_value
        """
        return []

    def get_fields_info(self, table_name):
        """
        Info about fields of a given table in the database.

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                column_name
                data_type
                comment
                unit
                texttype
                column_alias
                fully_qualified_name
        """
        return []

    def get_min_max_info(self, table_name):
        """
        Info about range constraints found in a given table.

        Return:
            Dictionary with keys corresponding to column names and values
            corresponding to tuples in the form (min_value, max_value)
        """
        return {}

    def get_value_map_info(self, table_name):
        """
        Info about value map constraints found in a given table.

        Return:
            Dictionary with keys corresponding to column names and values
            with lists of allowed values
        """
        return {}

    def get_relations_info(self, filter_layer_list=[]):
        """
        Info about relations found in a database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                constraint_name
                referencing_table_name
                referencing_column_name
                constraint_schema
                referenced_table_name
                referenced_column_name
                strength
        """
        return []

    def get_bags_of_info(self):
        """
        Info about bags_of found in a database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                current_layer_name
                attribute
                target_layer_name
                cardinality_max
                cardinality_min
        """
        return []

    def get_ignored_layers(self, ignore_basket_tables=True):
        """
        The ignored layers according to the ignored schemas and ignored tables and the ignored ili elements
        listed in the config.py.
        Additionally all the ili elements that have the attribute name ili2db.mapping in the meta attribute
        table.
        """
        tables_info = self.get_tables_info()
        relations_info = self.get_relations_info()
        meta_attrs_info = self.get_meta_attrs_info()
        mapping_ili_elements = []
        static_tables = []
        detected_tables = []
        referencing_detected_tables = []
        for record in meta_attrs_info:
            if record["attr_name"] == "ili2db.mapping":
                mapping_ili_elements.append(record["ilielement"])

        for record in tables_info:
            if "ili_name" in record:
                if (
                    record["ili_name"] in mapping_ili_elements
                    or record["ili_name"] in IGNORED_ILI_ELEMENTS
                ):
                    detected_tables.append(record["tablename"])
                    continue
            if "schemaname" in record:
                if record["schemaname"] in IGNORED_SCHEMAS:
                    static_tables.append(record["tablename"])
                    continue
            if "tablename" in record:
                if record["tablename"] in IGNORED_TABLES and (
                    ignore_basket_tables or record["tablename"] not in BASKET_TABLES
                ):
                    static_tables.append(record["tablename"])
                    continue

        for record in relations_info:
            if record["referenced_table"] in detected_tables:
                referencing_detected_tables.append(record["referencing_table"])

        return static_tables + detected_tables + referencing_detected_tables

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """Used for ili2db version 3"""
        return {}

    def get_attrili_attrdb_mapping(self, attrs_list):
        """Used for ili2db version 3"""
        return {}

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """Used for ili2db version 3"""
        return {}

    def get_models(self):
        return {}

    def ili_version(self):
        """
        Returns the version of the ili2db application that was used to create the schema
        """
        return None

    def get_basket_handling(self):
        """
        Returns `True` if a basket handling is enabled according to the settings table.
        Means when the database has been created with `--createBasketCol`.
        """
        return False

    def get_baskets_info(self):
        """
        Info about baskets found in the basket table and the related datasetname
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                basket_t_id
                basket_t_ili_tid
                topic
                dataset_t_id
                datasetname
        """
        return {}

    def get_datasets_info(self):
        """
        Info about datasets found in the dataset table
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                t_id
                datasetname
        """
        return {}

    def create_dataset(self, datasetname):
        """
        Returns the state and the errormessage
        """
        return False, None

    def rename_dataset(self, tid, datasetname):
        """
        Returns the state and the errormessage
        """
        return False, None

    def get_topics_info(self):
        """
        Returns all the topics found in the table t_ili2db_classname
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                model
                topic
        """
        return {}

    def create_basket(self, dataset_tid, topic):
        """
        Returns the state and the errormessage
        """
        return False, None

    def get_tid_handling(self):
        """
        Returns `True` if a tid handling is enabled according to the settings table (when the database has been created with `--createTidCol`).
        If t_ili_tids are used only because of a stable id definition in the model (with `OID as` in the topic or the class definition), this parameter is not set and this function will return `False`.
        """
        return False


class DBConnectorError(Exception):
    """This error is raised when DbConnector could not connect to database.

    This exception wraps different database exceptions to unify them in a single exception.
    """

    def __init__(self, message, base_exception=None):
        super().__init__(message)
        self.base_exception = base_exception
