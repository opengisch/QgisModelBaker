# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 8.11.2016
        git sha              : $Format:%H$
        copyright            : (C) 2016 by OPENGIS.ch
        email                : matthias@opengis.ch
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

import psycopg2
import psycopg2.extras
from .config import IGNORED_SCHEMAS, IGNORED_TABLES

from dataobjects.layers import Layer


class PostgresCreator:

    def __init__(self, uri):
        self.uri = uri
        self.conn = psycopg2.connect(uri)

    def layers(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
                    SELECT
                      tbls.schemaname AS schemaname,
                      tbls.tablename AS tablename,
                      a.attname AS primary_key,
                      g.f_geometry_column AS geometry_column,
                      g.srid AS srid,
                      g.type AS type
                    FROM pg_catalog.pg_tables tbls
                    LEFT JOIN pg_index i
                      ON i.indrelid = CONCAT(tbls.schemaname, '.', tbls.tablename)::regclass
                    LEFT JOIN pg_attribute a
                      ON a.attrelid = i.indrelid
                      AND a.attnum = ANY(i.indkey)
                    LEFT JOIN public.geometry_columns g
                      ON g.f_table_schema = tbls.schemaname
                      AND g.f_table_name = tbls.tablename
                    WHERE i.indisprimary
        """)

        layers = list()

        for record in cur:
            if record['schemaname'] in IGNORED_SCHEMAS:
                continue

            if record['tablename'] in IGNORED_TABLES:
                continue

            # 'service=\'pg_qgep\' key=\'obj_id\' srid=21781 type=CompoundCurve table="qgep"."vw_qgep_reach" (progression_geometry) sql='
            data_source_uri = '{uri} key={primary_key} estimatedmetadata=true srid={srid} type={type} table="{schema}"."{table}" ({geometry_column})'.format(
                uri=self.uri,
                primary_key=record['primary_key'],
                srid=record['srid'],
                type=record['type'],
                schema=record['schemaname'],
                table=record['tablename'],
                geometry_column=record['geometry_column']
            )

            layers.append(Layer('postgres', data_source_uri))

        return layers
