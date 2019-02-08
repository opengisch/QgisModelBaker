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
