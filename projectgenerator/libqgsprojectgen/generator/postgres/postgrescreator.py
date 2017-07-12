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
import re

from projectgenerator.libqgsprojectgen.dataobjects import Field
from projectgenerator.libqgsprojectgen.dataobjects import LegendGroup
from projectgenerator.libqgsprojectgen.dataobjects.layers import Layer
from qgis.core import QgsProviderRegistry, QgsWkbTypes
from .config import IGNORED_SCHEMAS, IGNORED_TABLES, IGNORED_FIELDNAMES, READONLY_FIELDNAMES
from .relations import PostgresRelation
from .domain_relations import DomainRelation


class PostgresCreator:
    def __init__(self, uri, schema):
        assert 'postgres' in QgsProviderRegistry.instance().providerList(), 'postgres provider not found in {}. Is the QGIS_PREFIX_PATH properly set?'.format(
            QgsProviderRegistry.instance().providerList())
        self.uri = uri
        self.schema = schema
        self.conn = psycopg2.connect(uri)

    def layers(self):
        bMetadataTable = False
        is_domain_field = ''
        domain_left_join = ''
        schema_where = ''

        if self.schema:
            # Do we have t_ili2db_table_prop
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                        SELECT
                          count(tablename)
                        FROM pg_catalog.pg_tables
                        WHERE schemaname = '{}' and tablename = 't_ili2db_table_prop'
            """.format(self.schema))
            bMetadataTable = bool(cur.fetchone()[0])

            if bMetadataTable:
                is_domain_field = "p.setting AS is_domain,"
                domain_left_join = """LEFT JOIN {}.t_ili2db_table_prop p
                              ON p.tablename = tbls.tablename
                              AND p.tag = 'ch.ehi.ili2db.tableKind'""".format(self.schema)
            schema_where = "AND schemaname = '{}'".format(self.schema)

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
                    SELECT
                      tbls.schemaname AS schemaname,
                      tbls.tablename AS tablename,
                      a.attname AS primary_key,
                      g.f_geometry_column AS geometry_column,
                      g.srid AS srid,
                      {is_domain_field}
                      g.type AS type
                    FROM pg_catalog.pg_tables tbls
                    LEFT JOIN pg_index i
                      ON i.indrelid = CONCAT(tbls.schemaname, '.', tbls.tablename)::regclass
                    LEFT JOIN pg_attribute a
                      ON a.attrelid = i.indrelid
                      AND a.attnum = ANY(i.indkey)
                    {domain_left_join}
                    LEFT JOIN public.geometry_columns g
                      ON g.f_table_schema = tbls.schemaname
                      AND g.f_table_name = tbls.tablename
                    WHERE i.indisprimary {schema_where}
        """.format(is_domain_field = is_domain_field, domain_left_join = domain_left_join, schema_where = schema_where))

        layers = list()

        for record in cur:
            # When in PostGIS mode, leaving schema blank should load tables from
            # all schemas, except the ignored ones
            if self.schema:
                if record['schemaname'] != self.schema:
                    continue
            elif record['schemaname'] in IGNORED_SCHEMAS:
                continue

            if record['tablename'] in IGNORED_TABLES:
                continue

            if record['geometry_column']:
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
            else:
                data_source_uri = '{uri} key={primary_key} table="{schema}"."{table}"'.format(
                    uri=self.uri,
                    primary_key=record['primary_key'],
                    schema=record['schemaname'],
                    table=record['tablename']
                )

            layer = Layer('postgres', data_source_uri, record['is_domain'] == 'ENUM' or record['is_domain'] == 'CATALOGUE' if 'is_domain' in record else False)

            # Get all fields for this table
            fields_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            fields_cur.execute("""
                SELECT
                  c.column_name,
                  pgd.description AS comment,
                  unit.setting AS unit,
                  txttype.setting AS texttype
                FROM pg_catalog.pg_statio_all_tables st
                LEFT JOIN information_schema.columns c ON c.table_schema=st.schemaname AND c.table_name=st.relname
                LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid=st.relid AND pgd.objsubid=c.ordinal_position
                LEFT JOIN {schema}.t_ili2db_column_prop unit ON c.table_name=unit.tablename AND c.column_name=unit.columname AND unit.tag = 'ch.ehi.ili2db.unit'
                LEFT JOIN {schema}.t_ili2db_column_prop txttype ON c.table_name=txttype.tablename AND c.column_name=txttype.columname AND txttype.tag = 'ch.ehi.ili2db.textKind'
                WHERE st.relid = '{schema}.{table}'::regclass;
            """.format(schema=record['schemaname'], table=record['tablename']))


            # Get all 'c'heck constraints for this table
            constraints_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            constraints_cur.execute("""
            SELECT
              consrc,
              regexp_matches(consrc, '\(\((.*) >= ([\d\.]+)\) AND \((.*) <= ([\d\.]+)\)\)') AS check_details
            FROM pg_constraint
            WHERE conrelid = '{schema}.{table}'::regclass
            AND contype = 'c'
            """.format(schema=record['schemaname'], table=record['tablename']))

            # Create a mapping in the form of
            #
            # fieldname: (min, max)
            constraint_mapping = dict()
            for constraint in constraints_cur:
                constraint_mapping[constraint['check_details'][0]] = (constraint['check_details'][1], constraint['check_details'][3])

            re_iliname = re.compile('^@iliname (.*)$')
            for fielddef in fields_cur:
                column_name = fielddef['column_name']
                comment = fielddef['comment']
                m = re_iliname.match(comment) if comment else None
                alias = None
                if m:
                    alias = m.group(1)

                field = Field(column_name)
                field.alias = alias

                if column_name in IGNORED_FIELDNAMES:
                    field.widget = 'Hidden'

                if column_name in READONLY_FIELDNAMES:
                    field.read_only = True

                if column_name in constraint_mapping:
                    field.widget = 'Range'
                    field.widget_config['Min'] = constraint_mapping[column_name][0]
                    field.widget_config['Max'] = constraint_mapping[column_name][1]
                    field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''

                if 'texttype' in fielddef and fielddef['texttype'] == 'MTEXT':
                    field.widget = 'TextEdit'
                    field.widget_config['IsMultiline'] = True

                layer.fields.append(field)

            layers.append(layer)

        return layers

    def relations(self, layers):
        relations =  PostgresRelation.find_relations(layers, self.conn, self.schema)
        # Automatic domain generation
        # We won't need this when https://github.com/claeis/ili2db/issues/19 is solved!
        domainRelation = DomainRelation()
        domain_relations = domainRelation.find_domain_relations(layers, self.conn, self.schema)

        return relations + domain_relations

    def legend(self, layers):
        legend = LegendGroup('root')
        tables = LegendGroup('tables')
        domains = LegendGroup('domains', False)

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

        legend.append(tables)
        if not domains.is_empty():
            legend.append(domains)

        return legend
