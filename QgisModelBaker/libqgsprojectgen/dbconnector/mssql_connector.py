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
        kind_settings_field = ''
        domain_left_join = ''
        schema_where = ''
        table_alias = ''
        ili_name = ''
        extent = ''
        alias_left_join = ''
        model_name = ''
        model_where = ''
        

        if self.schema:
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

        res = []
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
