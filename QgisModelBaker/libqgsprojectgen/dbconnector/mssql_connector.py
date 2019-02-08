# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    01/02/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polanía (BSF-Swissphoto)
    email                :    yesidpol.3@gmail.com
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
import pyodbc
from .db_connector import DBConnector

METADATA_TABLE = 't_ili2db_table_prop'
METAATTRS_TABLE = 't_ili2db_meta_attrs'

class MssqlConnector(DBConnector):
    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)
        self.conn = pyodbc.connect(uri)
        self.schema = schema

        # TODO check dbo schema
        if self.schema is None:
            self.schema = 'dbo'
        
        self._bMetadataTable = self._metadata_exists()
        self.iliCodeName = 'iliCode'

    def map_data_types(self, data_type):
        data_type = data_type.lower()
        if 'timestamp' in data_type:
            return self.QGIS_DATE_TIME_TYPE
        elif 'date' in data_type:
            return self.QGIS_DATE_TYPE
        elif 'time' in data_type:
            return self.QGIS_TIME_TYPE

        return data_type.lower()

    def metadata_exists(self):
        return self._bMetadataTable
    
    def _metadata_exists(self):
        return self._table_exists(METADATA_TABLE)

    def _table_exists(self, tablename):
        if self.schema:
            cur = self.conn.cursor()
            cur.execute("""
            SELECT count(TABLE_NAME) as 'count'
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA = '{}'
                    AND TABLE_NAME = '{}'
            """.format(self.schema, tablename))

            return bool(cur.fetchone()[0])

        return False

    def get_tables_info(self):
        res = []
        
        if self.schema:
            kind_settings_field = ''
            domain_left_join = ''
            schema_where = ''
            table_alias = ''
            ili_name = ''
            extent = ''
            alias_left_join = ''
            model_name = ''
            model_where = ''

            if self.metadata_exists():
                kind_settings_field = "p.setting AS kind_settings,"
                table_alias = "alias.setting AS table_alias,"
                ili_name = "c.iliname AS ili_name,"
                extent = """STUFF((SELECT ';' + CAST(cp.setting AS VARCHAR(MAX))  
                    FROM {}.t_ili2db_column_prop cp
                        WHERE tbls.table_name = cp.tablename and clm.COLUMN_NAME = cp.columnname
                        and cp.tag IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                        'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                        order by case cp.tag WHEN 'ch.ehi.ili2db.c1Min' THEN 1
                             WHEN 'ch.ehi.ili2db.c2Min' THEN 2
                             WHEN 'ch.ehi.ili2db.c1Max' THEN 3
                             WHEN 'ch.ehi.ili2db.c2Max' THEN 4
                             END 
                    FOR XML PATH(''),TYPE).value('(./text())[1]','VARCHAR(MAX)'),1,1,''
                    ) AS extent,""".format(self.schema)
                model_name = "left(c.iliname, charindex('.', c.iliname)-1) AS model,"
                domain_left_join = """
                    LEFT JOIN        {}.T_ILI2DB_TABLE_PROP p
                        ON p.tablename = tbls.TABLE_NAME 
                        AND p.tag = 'ch.ehi.ili2db.tableKind' 
                              """.format(self.schema)
                alias_left_join = """
                    LEFT JOIN        {}.T_ILI2DB_TABLE_PROP as alias
                        on    alias.tablename = tbls.TABLE_NAME
                        AND alias.tag = 'ch.ehi.ili2db.dispName'
                               """.format(self.schema)
                model_where = """LEFT JOIN {}.t_ili2db_classname c
                      ON tbls.TABLE_NAME = c.sqlname""".format(self.schema)
                      
            schema_where = "AND tbls.TABLE_SCHEMA = '{}'".format(self.schema)

            cur = self.conn.cursor()

            query = """
                SELECT distinct
                    tbls.TABLE_SCHEMA AS schemaname,
                    tbls.TABLE_NAME AS tablename, 
                    Col.Column_Name AS primary_key,
                    clm.COLUMN_NAME AS geometry_column,
                    tsrid.setting as srid,
                    {kind_settings_field}
                    {table_alias}
                    {model_name}
                    {ili_name}
                    {extent}
                    tgeomtype.setting as simple_type,
                    null as formatted_type
                FROM
                INFORMATION_SCHEMA.TABLE_CONSTRAINTS Tab 
                INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE Col 
                    on Col.Constraint_Name = Tab.Constraint_Name
                    AND Col.Table_Name = Tab.Table_Name
                    AND Col.CONSTRAINT_SCHEMA = Tab.CONSTRAINT_SCHEMA
                RIGHT JOIN INFORMATION_SCHEMA.TABLES as tbls
                    on Tab.TABLE_NAME = tbls.TABLE_NAME 
                    AND Tab.CONSTRAINT_SCHEMA = tbls.TABLE_SCHEMA
                    AND Tab.Constraint_Type = 'PRIMARY KEY'
                {domain_left_join}
                {alias_left_join}
                {model_where}
                LEFT JOIN INFORMATION_SCHEMA.COLUMNS as clm
                    on clm.TABLE_NAME = tbls.TABLE_NAME
                    AND clm.TABLE_SCHEMA = tbls.TABLE_SCHEMA
                    AND clm.DATA_TYPE = 'geometry'
                LEFT JOIN {schema}.T_ILI2DB_COLUMN_PROP as tsrid
                    on tbls.TABLE_NAME = tsrid.tablename and clm.COLUMN_NAME = tsrid.columnname and tsrid.tag='ch.ehi.ili2db.srid'
                LEFT JOIN {schema}.T_ILI2DB_COLUMN_PROP as tgeomtype
                    on tbls.TABLE_NAME = tgeomtype.tablename and clm.COLUMN_NAME = tgeomtype.columnname and tgeomtype.tag= 'ch.ehi.ili2db.geomType' 
                WHERE tbls.TABLE_TYPE = 'BASE TABLE' {schema_where}
            """.format(kind_settings_field=kind_settings_field, table_alias=table_alias, model_name=model_name, ili_name=ili_name, extent=extent,
                    domain_left_join=domain_left_join, alias_left_join=alias_left_join, model_where=model_where,
                    schema_where=schema_where,schema=self.schema)
            cur.execute(query)

            columns = [column[0] for column in cur.description]

            for row in cur.fetchall():
                my_rec = dict(zip(columns, row))
                # TODO type != simple_type
                my_rec['type'] = my_rec['simple_type']
                res.append(my_rec)

        return res

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(METAATTRS_TABLE):
            return []

        if self.schema:
            cur = self.conn.cursor()
            cur.execute("""
                        SELECT
                          attr_name,
                          attr_value
                        FROM {schema}.{metaattrs_table}
                        WHERE ilielement='{ili_name}';
            """.format(schema=self.schema, metaattrs_table=METAATTRS_TABLE, ili_name=ili_name))

            return cur

        return []

    def get_fields_info(self, table_name):
        # Get all fields for this table
        if self.schema: 
            fields_cur = self.conn.cursor()
            
            unit_field = ''
            text_kind_field = ''
            full_name_field = ''
            column_alias = ''
            unit_join = ''
            text_kind_join = ''
            disp_name_join = ''
            full_name_join = ''
            
            # TODO falta la columna description
            if self.metadata_exists():
                unit_field = 'unit.setting AS unit,'
                text_kind_field = 'txttype.setting AS texttype,'
                column_alias = 'alias.setting AS column_alias,'
                full_name_field = 'full_name.iliname AS fully_qualified_name,'
                unit_join = """                
                LEFT JOIN {}.t_ili2db_column_prop unit ON c.table_name = unit.tablename
                    AND c.column_name = unit.columnname
                    AND unit.tag = 'ch.ehi.ili2db.unit'""".format(self.schema)
                text_kind_join = """
                LEFT JOIN {}.t_ili2db_column_prop txttype ON c.table_name = txttype.tablename
                    AND c.column_name = txttype.columnname
                    AND txttype.tag = 'ch.ehi.ili2db.textKind'""".format(self.schema)
                disp_name_join = """
                LEFT JOIN {}.t_ili2db_column_prop alias ON c.table_name = alias.tablename
                    AND c.column_name = alias.columnname
                    AND alias.tag = 'ch.ehi.ili2db.dispName'""".format(self.schema)
                full_name_join = """
                LEFT JOIN {}.t_ili2db_attrname full_name ON full_name.owner='{}'
                    AND c.column_name=full_name.sqlname""".format(self.schema, table_name)
            query = """
                SELECT c.column_name,
                    c.data_type,
                    c.numeric_scale,
                    {unit_field}
                    {text_kind_field}
                    {column_alias}
                    {full_name_field}
                    '------' AS comment
                FROM INFORMATION_SCHEMA.COLUMNS AS c
                {unit_join}
                {text_kind_join}
                {disp_name_join}
                {full_name_join}
                WHERE TABLE_NAME = '{table}'
                    AND TABLE_SCHEMA = '{schema}'
                """.format(schema=self.schema, table=table_name, unit_field=unit_field,
                            text_kind_field=text_kind_field, column_alias=column_alias,
                            full_name_field=full_name_field,unit_join=unit_join, text_kind_join=text_kind_join,
                            disp_name_join=disp_name_join,
                            full_name_join=full_name_join)
            print(query)
            fields_cur.execute(query)
            res = self._get_dict_result(fields_cur)
            return res

    def _get_dict_result(self, cur):
        columns = [column[0] for column in cur.description]

        res = []
        for row in cur.fetchall():
            my_rec = dict(zip(columns, row))
            res.append(my_rec)

        return res
