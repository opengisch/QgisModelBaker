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
import os
import re
import sqlite3
import qgis.utils
from .db_connector import DBConnector
from ..generator.config import GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX

GPKG_METADATA_TABLE = 'T_ILI2DB_TABLE_PROP'
GPKG_METAATTRS_TABLE = 'T_ILI2DB_META_ATTRS'

class GPKGConnector(DBConnector):

    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)
        self.conn = qgis.utils.spatialite_connect(uri)
        self.conn.row_factory = sqlite3.Row
        self.uri = uri
        self._bMetadataTable = self._metadata_exists()
        self._tables_info = self._get_tables_info()
        self.iliCodeName = 'iliCode'
        self.dispName = 'dispName'

    def map_data_types(self, data_type):
        '''GPKG date/time types correspond to QGIS date/time types'''
        return data_type.lower()

    def db_or_schema_exists(self):
        return os.path.isfile(self.uri)

    def create_db_or_schema(self, usr):
        '''Create the DB (for GPKG).'''
        raise NotImplementedError

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT count(name)
            FROM sqlite_master
            WHERE name = '{}';
                    """.format(GPKG_METADATA_TABLE))
        return cursor.fetchone()[0] == 1

    def _table_exists(self, tablename):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT count(name)
            FROM sqlite_master
            WHERE name = '{}';
                    """.format(tablename))
        return cursor.fetchone()[0] == 1

    def get_tables_info(self):
        return self._tables_info

    def _get_tables_info(self):
        cursor = self.conn.cursor()
        interlis_fields = ''
        interlis_joins = ''

        if self.metadata_exists():
            interlis_fields = """p.setting AS kind_settings,
                alias.setting AS table_alias,
                c.iliname AS ili_name,
                (
                SELECT GROUP_CONCAT("setting", ';') FROM (
                    SELECT tablename, setting
                    FROM T_ILI2DB_COLUMN_PROP AS cprop
                    LEFT JOIN gpkg_geometry_columns g
                    ON cprop.tablename == g.table_name
                        WHERE cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                         'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                    ORDER BY CASE TAG
                        WHEN 'ch.ehi.ili2db.c1Min' THEN 1
                        WHEN 'ch.ehi.ili2db.c2Min' THEN 2
                        WHEN 'ch.ehi.ili2db.c1Max' THEN 3
                        WHEN 'ch.ehi.ili2db.c2Max' THEN 4
                        END ASC
                    ) WHERE g.geometry_type_name IS NOT NULL
                    GROUP BY tablename
                ) AS extent,
                substr(c.iliname, 0, instr(c.iliname, '.')) AS model,"""
            interlis_joins = """LEFT JOIN T_ILI2DB_TABLE_PROP p
                   ON p.tablename = s.name
                      AND p.tag = 'ch.ehi.ili2db.tableKind'
                LEFT JOIN t_ili2db_table_prop alias
                   ON alias.tablename = s.name
                      AND alias.tag = 'ch.ehi.ili2db.dispName'
                LEFT JOIN t_ili2db_classname c
                   ON s.name == c.sqlname """

        try:
            cursor.execute("""
                SELECT NULL AS schemaname,
                    s.name AS tablename,
                    NULL AS primary_key,
                    g.column_name AS geometry_column,
                    g.srs_id AS srid,
                    {interlis_fields}
                    g.geometry_type_name AS type
                FROM sqlite_master s
                LEFT JOIN gpkg_geometry_columns g
                   ON g.table_name = s.name
                {interlis_joins}
                WHERE s.type='table';
            """.format(interlis_fields=interlis_fields, interlis_joins=interlis_joins))
            records = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If the geopackage is empty, geometry_columns table does not exist
            return []

        # Use prefix-suffix pairs defined in config to filter out matching tables
        filtered_records = records[:]
        for prefix_suffix in GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX:
            suffix_regexp = '(' + '|'.join(prefix_suffix['suffix'] ) + ')$' if prefix_suffix['suffix'] else ''
            regexp = r'{}[\W\w]+{}'.format(prefix_suffix['prefix'], suffix_regexp)

            p = re.compile(regexp) # e.g., 'rtree_[\W\w]+_(geometry|geometry_node|geometry_parent|geometry_rowid)$'
            for record in records:
                if p.match(record['tablename']):
                    if record in filtered_records:
                        filtered_records.remove(record)

        # Get pk info and update each record storing it in a list of dicts
        complete_records = list()
        for record in filtered_records:
            cursor.execute("""
                PRAGMA table_info({})
                """.format(record['tablename']))
            table_info = cursor.fetchall()

            primary_key_list = list()
            for table_record in table_info:
                if table_record['pk'] > 0:
                    primary_key_list.append(table_record['name'])
            primary_key = ",".join(primary_key_list) or None

            dict_record = dict(zip(record.keys(), tuple(record)))
            dict_record['primary_key'] = primary_key
            complete_records.append(dict_record)

        cursor.close()
        return complete_records

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(GPKG_METAATTRS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute("""
                        SELECT
                          attr_name,
                          attr_value
                        FROM {meta_attr_table}
                        WHERE ilielement='{ili_name}'
        """.format(meta_attr_table=GPKG_METAATTRS_TABLE, ili_name=ili_name))
        records = cursor.fetchall()
        cursor.close()
        return records

    def get_fields_info(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info({});".format(table_name))
        columns_info = cursor.fetchall()

        columns_prop = list()
        columns_full_name = list()

        if self.metadata_exists():
            cursor.execute("""
                SELECT *
                FROM t_ili2db_column_prop
                WHERE tablename = '{}'
                """.format(table_name))
            columns_prop = cursor.fetchall()

        if self.metadata_exists():
            cursor.execute("""
                SELECT SqlName, IliName
                FROM t_ili2db_attrname
                WHERE owner = '{}'
                """.format(table_name))
            columns_full_name = cursor.fetchall()

        complete_records = list()
        for column_info in columns_info:
            record = {}
            record['column_name'] = column_info['name']
            record['data_type'] = column_info['type']
            record['comment'] = None
            record['unit'] = None
            record['texttype'] = None
            record['column_alias'] = None

            if record['column_name'] == 'T_Id':
                # The default value needs to be calculated client side,
                # sqlite doesn't provide the means to pre-evaluate serials
                record['default_value_expression'] = "sqlite_fetch_and_increment(@layer, 'T_KEY_OBJECT', 'T_LastUniqueId', 'T_Key', 'T_Id', map('T_LastChange','date(''now'')','T_CreateDate','date(''now'')','T_User','''' || @user_account_name || ''''))"

            for column_full_name in columns_full_name:
                if column_full_name['sqlname'] == column_info['name']:
                    record['fully_qualified_name'] = column_full_name['iliname']
                    break

            for column_prop in columns_prop:
                if column_prop['columnname'] == column_info['name']:
                    if column_prop['tag'] == 'ch.ehi.ili2db.unit':
                        record['unit'] = column_prop['setting']
                    elif column_prop['tag'] == 'ch.ehi.ili2db.textKind':
                        record['texttype'] = column_prop['setting']
                    elif column_prop['tag'] == 'ch.ehi.ili2db.dispName':
                        record['column_alias'] = column_prop['setting']

            complete_records.append(record)

        cursor.close()
        return complete_records

    def get_constraints_info(self, table_name):
        constraint_mapping = dict()
        cursor = self.conn.cursor()
        cursor.execute("""SELECT sql
                          FROM sqlite_master
                          WHERE name = '{}' AND type = 'table'
                       """.format(table_name))

        # Create a mapping in the form of
        #
        # fieldname: (min, max)
        res1 = re.findall(r'CHECK\((.*)\)', cursor.fetchone()[0])
        for res in res1:
            res2 = re.search(r'(\w+) BETWEEN ([-?\d\.]+) AND ([-?\d\.]+)', res)
            if res2:
                constraint_mapping[res2.group(1)] = (
                    res2.group(2), res2.group(3))

        return constraint_mapping

    def get_relations_info(self, filter_layer_list=[]):
        # We need to get the PK for each table, so first get tables_info
        # and then build something more searchable
        tables_info_dict = dict()
        for table_info in self._tables_info:
            tables_info_dict[table_info['tablename']] = table_info

        cursor = self.conn.cursor()
        complete_records = list()
        for table_info_name, table_info in tables_info_dict.items():
            cursor.execute(
                "PRAGMA foreign_key_list({});".format(table_info_name))
            foreign_keys = cursor.fetchall()

            for foreign_key in foreign_keys:
                record = {}
                record['referencing_table'] = table_info['tablename']
                record['referencing_column'] = foreign_key['from']
                record['referenced_table'] = foreign_key['table']
                record['referenced_column'] = tables_info_dict[
                    foreign_key['table']]['primary_key']
                record['constraint_name'] = '{}_{}_{}_{}'.format(record['referencing_table'],
                                                                 record[
                                                                     'referencing_column'],
                                                                 record[
                                                                     'referenced_table'],
                                                                 record['referenced_column'])
                complete_records.append(record)

        cursor.close()
        return complete_records

    def get_iliname_dbname_mapping(self, sqlnames):
        """TODO: remove when ili2db issue #19 is solved"""
        # Map domain ili name with its correspondent pg name
        cursor = self.conn.cursor()
        names = "'" + "','".join(sqlnames) + "'"
        cursor.execute("""SELECT iliname, sqlname
                          FROM t_ili2db_classname
                          WHERE sqlname IN ({names})
                       """.format(names=names))
        return cursor

    def get_models(self):
        """TODO: remove when ili2db issue #19 is solved"""
        """Needed for exportmodels"""
        # Get MODELS
        cursor = self.conn.cursor()
        cursor.execute("""SELECT modelname, content
                          FROM t_ili2db_model """)
        return cursor

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """TODO: remove when ili2db issue #19 is solved"""
        cursor = self.conn.cursor()
        class_names = "'" + \
            "','".join(list(models_info.keys()) +
                       list(extended_classes.keys())) + "'"
        cursor.execute("""SELECT *
                          FROM t_ili2db_classname
                          WHERE iliname IN ({class_names})
                       """.format(class_names=class_names))
        return cursor

    def get_attrili_attrdb_mapping(self, attrs_list):
        """TODO: remove when ili2db issue #19 is solved"""
        cursor = self.conn.cursor()
        attr_names = "'" + "','".join(attrs_list) + "'"
        cursor.execute("""SELECT iliname, sqlname, owner
                          FROM t_ili2db_attrname
                          WHERE iliname IN ({attr_names})
                       """.format(attr_names=attr_names))
        return cursor

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """TODO: remove when ili2db issue #19 is solved"""
        cursor = self.conn.cursor()
        owner_names = "'" + "','".join(owners) + "'"
        cursor.execute("""SELECT iliname, sqlname, owner
                          FROM t_ili2db_attrname
                          WHERE owner IN ({owner_names})
                       """.format(owner_names=owner_names))
        return cursor
