# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    10/10/17
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
import datetime
import shutil
import tempfile
import logging

from qgis.core import QgsProject
from qgis.testing import unittest, start_app

from QgisModelBaker.libqgsprojectgen.dataobjects import Project
from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import iliimporter_config, testdata_path, get_pg_connection_string
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from QgisModelBaker.libqgsprojectgen.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager

start_app()


class TestDomainClassRelation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_domain_class_relations_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    ),
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "t_id",
                                   "name": "avaluo_uso_fkey",
                                   "child_domain_name": None})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "t_id",
                                   "name": "derecho_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "t_id",
                                   "name": "persona_documento_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "t_id",
                                   "name": "persona_genero_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "t_id",
                                   "name": "persona_tipo_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "t_id",
                                   "name": "predio_tipo_fkey",
                                   "child_domain_name": None})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "ilicode",
                                   "name": "avaluo_uso_avaluo_usotipo_ilicode"})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "ilicode",
                                   "name": "derecho_tipo_col_derechotipo_ilicode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "ilicode",
                                   "name": "persona_documento_tipo_col_interesadodocumentotipo_ilicode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "ilicode",
                                   "name": "persona_genero_col_genero_ilicode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "ilicode",
                                   "name": "persona_tipo_la_interesadotipo_ilicode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "ilicode",
                                   "name": "predio_tipo_la_baunittipo_ilicode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_extended_domain_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'Colors'
        importer.configuration.dbschema = 'colors_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    ),
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 1 domain-class relation is expected
        expected_relations.append({'referencing_layer': 'childcolor',
                                   'referenced_layer': 'dombasecolortype',
                                   'referencing_field': 'colortype',
                                   'referenced_field': 't_id',
                                   'name': 'childcolor_colortype_fkey',
                                   'child_domain_name': 'Colors.DomChildColorType'})

        self.assertEqual(len(expected_relations), len(relations_dicts))

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == 'childcolor':
                config = layer.layer.fields().field('colortype').editorWidgetSetup().config()
                self.assertEqual(config['FilterExpression'], '"thisclass" = \'Colors.DomChildColorType\'')
                count += 1

        self.assertEqual(count, 1)

    def test_domain_class_relations_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    ),
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "T_Id",
                                   "name": "avaluo_uso_fkey",
                                   "child_domain_name": None})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "derecho_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "T_Id",
                                   "name": "persona_documento_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "T_Id",
                                   "name": "persona_genero_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "persona_tipo_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "predio_tipo_fkey",
                                   "child_domain_name": None})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "iliCode",
                                   "name": "avaluo_uso_avaluo_usotipo_iliCode"})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "derecho_tipo_col_derechotipo_iliCode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "iliCode",
                                   "name": "persona_documento_tipo_col_interesadodocumentotipo_iliCode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "iliCode",
                                   "name": "persona_genero_col_genero_iliCode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "persona_tipo_la_interesadotipo_iliCode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "predio_tipo_la_baunittipo_iliCode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_extended_domain_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'Colors'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_colors_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    ),
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 1 domain-class relation is expected
        expected_relations.append({'referencing_layer': 'childcolor',
                                   'referenced_layer': 'dombasecolortype',
                                   'referencing_field': 'colortype',
                                   'referenced_field': 'T_Id',
                                   'name': 'childcolor_colortype_fkey',
                                   'child_domain_name': 'Colors.DomChildColorType'})

        self.assertEqual(len(expected_relations), len(relations_dicts))

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == 'childcolor':
                config = layer.layer.fields().field('colortype').editorWidgetSetup().config()
                self.assertEqual(config['FilterExpression'], '"thisclass" = \'Colors.DomChildColorType\'')
                count += 1

        self.assertEqual(count, 1)

    def test_domain_class_relations_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri,
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)


        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name,
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "T_Id",
                                   "name": "avaluo_uso_fkey",
                                   "child_domain_name": None})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "derecho_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "T_Id",
                                   "name": "persona_documento_tipo_fkey",
                                   "child_domain_name": None})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "T_Id",
                                   "name": "persona_genero_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "persona_tipo_fkey",
                                   "child_domain_name": None})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "T_Id",
                                   "name": "predio_tipo_fkey",
                                   "child_domain_name": None})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri,
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)


        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 6 domain-class relations are expected
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "avaluo",
                                   "referenced_layer": "avaluo_usotipo",
                                   "referencing_field": "uso",
                                   "referenced_field": "iliCode",
                                   "name": "avaluo_uso_avaluo_usotipo_iliCode"})
        # Domain inherited from superclass and from another model
        expected_relations.append({"referencing_layer": "derecho",
                                   "referenced_layer": "col_derechotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "derecho_tipo_col_derechotipo_iliCode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_interesadodocumentotipo",
                                   "referencing_field": "documento_tipo",
                                   "referenced_field": "iliCode",
                                   "name": "persona_documento_tipo_col_interesadodocumentotipo_iliCode"})
        # Domain from another model
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "col_genero",
                                   "referencing_field": "genero",
                                   "referenced_field": "iliCode",
                                   "name": "persona_genero_col_genero_iliCode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "persona",
                                   "referenced_layer": "la_interesadotipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "persona_tipo_la_interesadotipo_iliCode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "predio",
                                   "referenced_layer": "la_baunittipo",
                                   "referencing_field": "tipo",
                                   "referenced_field": "iliCode",
                                   "name": "predio_tipo_la_baunittipo_iliCode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_extended_domain_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'Colors'
        importer.configuration.dbschema = 'colors_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri,
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name,
                                    "child_domain_name": relation.child_domain_name})

        expected_relations = list()  # 1 domain-class relation is expected
        expected_relations.append({'referencing_layer': 'childcolor',
                                   'referenced_layer': 'dombasecolortype',
                                   'referencing_field': 'colortype',
                                   'referenced_field': 'T_Id',
                                   'name': 'childcolor_colortype_fkey',
                                   'child_domain_name': 'Colors.DomChildColorType'})

        self.assertEqual(len(expected_relations), len(relations_dicts))

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == 'childcolor':
                config = layer.layer.fields().field('colortype').editorWidgetSetup().config()
                self.assertEqual(config['FilterExpression'], '"thisclass" = \'Colors.DomChildColorType\'')
                count += 1

        self.assertEqual(count, 1)

    def test_domain_class_relations_ZG_Abfallsammelstellen_ZEBA_V1_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        expected_relations = list()  # 8 domain-class relations are expected
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "oberirdische_sammelstelle",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "t_id",
                                   "name": "oberirdische_sammelstelle_abfallart_fkey"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "t_id",
                                   "name": "unterflurcontainer_abfallart_fkey"})
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "lagegenauigkeit",
                                   "referencing_field": "lagegenauigkeit",
                                   "referenced_field": "t_id",
                                   "name": "unterflurcontainer_lagegenauigkeit_fkey"})
        # Domains from inline ENUMs
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_eigentum",
                                   "referencing_field": "eigentum",
                                   "referenced_field": "t_id",
                                   "name": "abfallsammelstelle_eigentum_fkey"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_grundeigentum",
                                   "referencing_field": "grundeigentum",
                                   "referenced_field": "t_id",
                                   "name": "abfallsammelstelle_grundeigentum_fkey"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_oeffentlichesammelstelle",
                                   "referencing_field": "oeffentlichesammelstelle",
                                   "referenced_field": "t_id",
                                   "name": "abfallsammelstelle_oeffentlichesammelstelle_fkey"})
        # Domains from INTERLIS base model
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "halignment",
                                   "referencing_field": "texthali",
                                   "referenced_field": "t_id",
                                   "name": "sammelstelle_beschriftung_texthali_fkey"})
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "valignment",
                                   "referencing_field": "textvali",
                                   "referenced_field": "t_id",
                                   "name": "sammelstelle_beschriftung_textvali_fkey"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_ZG_Abfallsammelstellen_ZEBA_V1_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 8 domain-class relations are expected
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "oberirdische_sammelstelle",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "ilicode",
                                   "name": "oberirdische_sammelstelle_abfallart_abfallart_ilicode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "ilicode",
                                   "name": "unterflurcontainer_abfallart_abfallart_ilicode"})
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "lagegenauigkeit",
                                   "referencing_field": "lagegenauigkeit",
                                   "referenced_field": "ilicode",
                                   "name": "unterflurcontainer_lagegenauigkeit_lagegenauigkeit_ilicode"})
        # Domains from inline ENUMs
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_eigentum",
                                   "referencing_field": "eigentum",
                                   "referenced_field": "ilicode",
                                   "name": "abfallsammelstelle_eigentum_abfallsammelstelle_eigentum_ilicode"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_grundeigentum",
                                   "referencing_field": "grundeigentum",
                                   "referenced_field": "ilicode",
                                   "name": "abfallsammelstelle_grundeigentum_abfallsammelstelle_grundeigentum_ilicode"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_oeffentlichesammelstelle",
                                   "referencing_field": "oeffentlichesammelstelle",
                                   "referenced_field": "ilicode",
                                   "name": "abfallsammelstelle_oeffentlichesammelstelle_abfallsammelstelle_oeffentlichesammelstelle_ilicode"})
        # Domains from INTERLIS base model
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "halignment",
                                   "referencing_field": "texthali",
                                   "referenced_field": "ilicode",
                                   "name": "sammelstelle_beschriftung_texthali_halignment_ilicode"})
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "valignment",
                                   "referencing_field": "textvali",
                                   "referenced_field": "ilicode",
                                   "name": "sammelstelle_beschriftung_textvali_valignment_ilicode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_domain_class_relations_ZG_Abfallsammelstellen_ZEBA_V1_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg_2_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)
        
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        
        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        expected_relations = list()  # 8 domain-class relations are expected
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "oberirdische_sammelstelle",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "T_Id",
                                   "name": "oberirdische_sammelstelle_abfallart_fkey"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "T_Id",
                                   "name": "unterflurcontainer_abfallart_fkey"})
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "lagegenauigkeit",
                                   "referencing_field": "lagegenauigkeit",
                                   "referenced_field": "T_Id",
                                   "name": "unterflurcontainer_lagegenauigkeit_fkey"})
        # Domains from inline ENUMs
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_eigentum",
                                   "referencing_field": "eigentum",
                                   "referenced_field": "T_Id",
                                   "name": "abfallsammelstelle_eigentum_fkey"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_grundeigentum",
                                   "referencing_field": "grundeigentum",
                                   "referenced_field": "T_Id",
                                   "name": "abfallsammelstelle_grundeigentum_fkey"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_oeffentlichesammelstelle",
                                   "referencing_field": "oeffentlichesammelstelle",
                                   "referenced_field": "T_Id",
                                   "name": "abfallsammelstelle_oeffentlichesammelstelle_fkey"})
        # Domains from INTERLIS base model
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "halignment",
                                   "referencing_field": "texthali",
                                   "referenced_field": "T_Id",
                                   "name": "sammelstelle_beschriftung_texthali_fkey"})
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "valignment",
                                   "referencing_field": "textvali",
                                   "referenced_field": "T_Id",
                                   "name": "sammelstelle_beschriftung_textvali_fkey"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_ZG_Abfallsammelstellen_ZEBA_V1_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg_2_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 8 domain-class relations are expected
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "oberirdische_sammelstelle",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "iliCode",
                                   "name": "oberirdische_sammelstelle_abfallart_abfallart_iliCode"})
        # Domain inherited from abstract class
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "abfallart",
                                   "referencing_field": "abfallart",
                                   "referenced_field": "iliCode",
                                   "name": "unterflurcontainer_abfallart_abfallart_iliCode"})
        # Domain from the same model, out of the topic
        expected_relations.append({"referencing_layer": "unterflurcontainer",
                                   "referenced_layer": "lagegenauigkeit",
                                   "referencing_field": "lagegenauigkeit",
                                   "referenced_field": "iliCode",
                                   "name": "unterflurcontainer_lagegenauigkeit_lagegenauigkeit_iliCode"})
        # Domains from inline ENUMs
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_eigentum",
                                   "referencing_field": "eigentum",
                                   "referenced_field": "iliCode",
                                   "name": "abfallsammelstelle_eigentum_abfallsammelstelle_eigentum_iliCode"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_grundeigentum",
                                   "referencing_field": "grundeigentum",
                                   "referenced_field": "iliCode",
                                   "name": "abfallsammelstelle_grundeigentum_abfallsammelstelle_grundeigentum_iliCode"})
        expected_relations.append({"referencing_layer": "abfallsammelstelle",
                                   "referenced_layer": "abfallsammelstelle_oeffentlichesammelstelle",
                                   "referencing_field": "oeffentlichesammelstelle",
                                   "referenced_field": "iliCode",
                                   "name": "abfallsammelstelle_oeffentlichesammelstelle_abfallsammelstelle_oeffentlichesammelstelle_iliCode"})
        # Domains from INTERLIS base model
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "halignment",
                                   "referencing_field": "texthali",
                                   "referenced_field": "iliCode",
                                   "name": "sammelstelle_beschriftung_texthali_halignment_iliCode"})
        expected_relations.append({"referencing_layer": "sammelstelle_beschriftung",
                                   "referenced_layer": "valignment",
                                   "referencing_field": "textvali",
                                   "referenced_field": "iliCode",
                                   "name": "sammelstelle_beschriftung_textvali_valignment_iliCode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_domain_structure_relations_ZG_Naturschutz_und_Erholung_V1_0_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        # 7 domain-structure + 1 domain-class relations are expected
        expected_relations = list()

        expected_relations.append({'name': 'ns_bewirtschaftung_ns_bewirtschaftungen_fkey',
                                   'referenced_layer': 'ns_bewirtschaftungen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ns_bewirtschaftung',
                                   'referencing_field': 'ns_bewirtschaftungen'})

        expected_relations.append({'name': 'datenbestand_zustaendigestelle_fkey',
                                   'referenced_layer': 'zustaendige_stelle',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'datenbestand',
                                   'referencing_field': 'zustaendigestelle'})

        expected_relations.append({'name': 'ni_punkt_typ_ni_punkt_typen_fkey',
                                   'referenced_layer': 'ni_punkt_typen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ni_punkt_typ',
                                   'referencing_field': 'ni_punkt_typen'})

        expected_relations.append({'name': 'ei_linie_typ_ei_linie_typen_fkey',
                                   'referenced_layer': 'ei_linie_typen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ei_linie_typ',
                                   'referencing_field': 'ei_linie_typen'})

        expected_relations.append({'name': 'ei_bewirtschaftung_ei_bewirtschaftungen_fkey',
                                   'referenced_layer': 'ei_bewirtschaftungen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ei_bewirtschaftung',
                                   'referencing_field': 'ei_bewirtschaftungen'})

        expected_relations.append({'name': 'ei_punkt_typ_ei_punkt_typen_fkey',
                                   'referenced_layer': 'ei_punkt_typen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ei_punkt_typ',
                                   'referencing_field': 'ei_punkt_typen'})

        expected_relations.append({'name': 'ni_linie_typ_ni_linie_typen_fkey',
                                   'referenced_layer': 'ni_linie_typen',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'ni_linie_typ',
                                   'referencing_field': 'ni_linie_typen'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_typ_fkey',
                                   'referenced_layer': 'nro_typ',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'typ'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ei_punkt_typen', 't_id', 'dispname'],
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 't_id', 'dispname'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ei_linie_typen', 't_id', 'dispname'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 't_id', 'dispname'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ni_punkt_typen', 't_id', 'dispname'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 't_id', 'dispname'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ni_linie_typen', 't_id', 'dispname'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 't_id', 'dispname'],
            ['naturschutzrelevantes_objekt_ohne_schutzstatus_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 't_id', 'dispname']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 9)

    def test_ili2db3_domain_structure_relations_ZG_Naturschutz_und_Erholung_V1_0_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        # 7 domain-structure + 1 domain-class relations are expected
        expected_relations = list()

        expected_relations.append({'name': 'ns_bewirtschaftung_ns_bewirtschaftungen_ns_bewirtschaftungen_ilicode',
                                   'referenced_layer': 'ns_bewirtschaftungen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ns_bewirtschaftung',
                                   'referencing_field': 'ns_bewirtschaftungen'})

        expected_relations.append({'name': 'datenbestand_zustaendigestelle_fkey',
                                   'referenced_layer': 'zustaendige_stelle',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'datenbestand',
                                   'referencing_field': 'zustaendigestelle'})

        expected_relations.append({'name': 'ni_punkt_typ_ni_punkt_typen_ni_punkt_typen_ilicode',
                                   'referenced_layer': 'ni_punkt_typen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ni_punkt_typ',
                                   'referencing_field': 'ni_punkt_typen'})

        expected_relations.append({'name': 'ei_linie_typ_ei_linie_typen_ei_linie_typen_ilicode',
                                   'referenced_layer': 'ei_linie_typen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ei_linie_typ',
                                   'referencing_field': 'ei_linie_typen'})

        expected_relations.append({'name': 'ei_bewirtschaftung_ei_bewirtschaftungen_ei_bewirtschaftungen_ilicode',
                                   'referenced_layer': 'ei_bewirtschaftungen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ei_bewirtschaftung',
                                   'referencing_field': 'ei_bewirtschaftungen'})

        expected_relations.append({'name': 'ei_punkt_typ_ei_punkt_typen_ei_punkt_typen_ilicode',
                                   'referenced_layer': 'ei_punkt_typen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ei_punkt_typ',
                                   'referencing_field': 'ei_punkt_typen'})

        expected_relations.append({'name': 'ni_linie_typ_ni_linie_typen_ni_linie_typen_ilicode',
                                   'referenced_layer': 'ni_linie_typen',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'ni_linie_typ',
                                   'referencing_field': 'ni_linie_typen'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_typ_nro_typ_ilicode',
                                   'referenced_layer': 'nro_typ',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'typ'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ei_punkt_typen', 'ilicode', 'dispname'],
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'ilicode', 'dispname'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ei_linie_typen', 'ilicode', 'dispname'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'ilicode', 'dispname'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ni_punkt_typen', 'ilicode', 'dispname'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'ilicode', 'dispname'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ni_linie_typen', 'ilicode', 'dispname'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'ilicode', 'dispname'],
            ['naturschutzrelevantes_objekt_ohne_schutzstatus_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'ilicode', 'dispname']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 9)

    def test_domain_structure_relations_ZG_Naturschutz_und_Erholung_V1_0_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_bags_of_enum_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        # 7 domain-structure + 1 domain-class relations are expected
        expected_relations = list()

        expected_relations.append({'name': 'ns_bewirtschaftung_ns_bewirtschaftungen_fkey',
                                   'referenced_layer': 'ns_bewirtschaftungen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ns_bewirtschaftung',
                                   'referencing_field': 'ns_bewirtschaftungen'})

        expected_relations.append({'name': 'datenbestand_zustaendigestelle_fkey',
                                   'referenced_layer': 'zustaendige_stelle',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'datenbestand',
                                   'referencing_field': 'zustaendigestelle'})

        expected_relations.append({'name': 'ni_punkt_typ_ni_punkt_typen_fkey',
                                   'referenced_layer': 'ni_punkt_typen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ni_punkt_typ',
                                   'referencing_field': 'ni_punkt_typen'})

        expected_relations.append({'name': 'ei_linie_typ_ei_linie_typen_fkey',
                                   'referenced_layer': 'ei_linie_typen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ei_linie_typ',
                                   'referencing_field': 'ei_linie_typen'})

        expected_relations.append({'name': 'ei_bewirtschaftung_ei_bewirtschaftungen_fkey',
                                   'referenced_layer': 'ei_bewirtschaftungen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ei_bewirtschaftung',
                                   'referencing_field': 'ei_bewirtschaftungen'})

        expected_relations.append({'name': 'ei_punkt_typ_ei_punkt_typen_fkey',
                                   'referenced_layer': 'ei_punkt_typen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ei_punkt_typ',
                                   'referencing_field': 'ei_punkt_typen'})

        expected_relations.append({'name': 'ni_linie_typ_ni_linie_typen_fkey',
                                   'referenced_layer': 'ni_linie_typen',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'ni_linie_typ',
                                   'referencing_field': 'ni_linie_typen'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_typ_fkey',
                                   'referenced_layer': 'nro_typ',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'typ'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ei_punkt_typen', 'T_Id', 'dispName'],
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'T_Id', 'dispName'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ei_linie_typen', 'T_Id', 'dispName'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'T_Id', 'dispName'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ni_punkt_typen', 'T_Id', 'dispName'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'T_Id', 'dispName'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ni_linie_typen', 'T_Id', 'dispName'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'T_Id', 'dispName'],
            ['naturschutzrelevantes_objekt_ohne_schutzstatus_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'T_Id', 'dispName']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 9)

    def test_ili2db3_domain_structure_relations_ZG_Naturschutz_und_Erholung_V1_0_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_bags_of_enum_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        # 7 domain-structure + 1 domain-class relations are expected
        expected_relations = list()

        expected_relations.append({'name': 'ns_bewirtschaftung_ns_bewirtschaftungen_ns_bewirtschaftungen_iliCode',
                                   'referenced_layer': 'ns_bewirtschaftungen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ns_bewirtschaftung',
                                   'referencing_field': 'ns_bewirtschaftungen'})

        expected_relations.append({'name': 'datenbestand_zustaendigestelle_zustaendige_stelle_T_Id',
                                   'referenced_layer': 'zustaendige_stelle',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'datenbestand',
                                   'referencing_field': 'zustaendigestelle'})

        expected_relations.append({'name': 'ni_punkt_typ_ni_punkt_typen_ni_punkt_typen_iliCode',
                                   'referenced_layer': 'ni_punkt_typen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ni_punkt_typ',
                                   'referencing_field': 'ni_punkt_typen'})

        expected_relations.append({'name': 'ei_linie_typ_ei_linie_typen_ei_linie_typen_iliCode',
                                   'referenced_layer': 'ei_linie_typen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ei_linie_typ',
                                   'referencing_field': 'ei_linie_typen'})

        expected_relations.append({'name': 'ei_bewirtschaftung_ei_bewirtschaftungen_ei_bewirtschaftungen_iliCode',
                                   'referenced_layer': 'ei_bewirtschaftungen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ei_bewirtschaftung',
                                   'referencing_field': 'ei_bewirtschaftungen'})

        expected_relations.append({'name': 'ei_punkt_typ_ei_punkt_typen_ei_punkt_typen_iliCode',
                                   'referenced_layer': 'ei_punkt_typen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ei_punkt_typ',
                                   'referencing_field': 'ei_punkt_typen'})

        expected_relations.append({'name': 'ni_linie_typ_ni_linie_typen_ni_linie_typen_iliCode',
                                   'referenced_layer': 'ni_linie_typen',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'ni_linie_typ',
                                   'referencing_field': 'ni_linie_typen'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_typ_nro_typ_iliCode',
                                   'referenced_layer': 'nro_typ',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'typ'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ei_punkt_typen', 'iliCode', 'dispName'],
            ['erholungsinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'iliCode', 'dispName'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ei_linie_typen', 'iliCode', 'dispName'],
            ['erholungsinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ei_bewirtschaftungen', 'iliCode', 'dispName'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'typ', '1..*', 'ni_punkt_typen', 'iliCode', 'dispName'],
            ['naturschutzinfrastruktur_punktobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'iliCode', 'dispName'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'typ', '1..*', 'ni_linie_typen', 'iliCode', 'dispName'],
            ['naturschutzinfrastruktur_linienobjekt_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'iliCode', 'dispName'],
            ['naturschutzrelevantes_objekt_ohne_schutzstatus_geometrie', 'bewirtschaftung', '1..*', 'ns_bewirtschaftungen', 'iliCode', 'dispName']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 9)

    def test_domain_structure_relations_KbS_LV95_V1_3_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/KbS_V1_3.ili')
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        # 2 structure-domain relations defined OUT OF A TOPIC are expected
        expected_relations = list()

        expected_relations.append({'name': 'deponietyp__avalue_fkey',
                                   'referenced_layer': 'deponietyp',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'deponietyp_',
                                   'referencing_field': 'avalue'})

        expected_relations.append({'name': 'untersmassn__avalue_fkey',
                                   'referenced_layer': 'untersmassn',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'untersmassn_',
                                   'referencing_field': 'avalue'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['belasteter_standort_geo_lage_punkt', 'deponietyp', '0..*', 'deponietyp', 't_id', 'dispname'],
            ['belasteter_standort_geo_lage_punkt', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 't_id', 'dispname'],
            ['belasteter_standort_geo_lage_polygon', 'deponietyp', '0..*', 'deponietyp', 't_id', 'dispname'],
            ['belasteter_standort_geo_lage_polygon', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 't_id', 'dispname']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 4)

    def test_ili2db3_domain_structure_relations_KbS_LV95_V1_3_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/KbS_V1_3.ili')
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        # 2 structure-domain relations defined OUT OF A TOPIC are expected
        expected_relations = list()

        expected_relations.append({'name': 'deponietyp__avalue_deponietyp_ilicode',
                                   'referenced_layer': 'deponietyp',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'deponietyp_',
                                   'referencing_field': 'avalue'})

        expected_relations.append({'name': 'untersmassn__avalue_untersmassn_ilicode',
                                   'referenced_layer': 'untersmassn',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'untersmassn_',
                                   'referencing_field': 'avalue'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['belasteter_standort_geo_lage_punkt', 'deponietyp', '0..*', 'deponietyp', 'ilicode', 'dispname'],
            ['belasteter_standort_geo_lage_punkt', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'ilicode', 'dispname'],
            ['belasteter_standort_geo_lage_polygon', 'deponietyp', '0..*', 'deponietyp', 'ilicode', 'dispname'],
            ['belasteter_standort_geo_lage_polygon', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'ilicode', 'dispname']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 4)

    def test_domain_structure_relations_KbS_LV95_V1_3_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/KbS_V1_3.ili')
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_bags_of_enum_kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        # 2 structure-domain relations defined OUT OF A TOPIC are expected
        expected_relations = list()

        expected_relations.append({'name': 'deponietyp__avalue_fkey',
                                   'referenced_layer': 'deponietyp',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'deponietyp_',
                                   'referencing_field': 'avalue'})

        expected_relations.append({'name': 'untersmassn__avalue_fkey',
                                   'referenced_layer': 'untersmassn',
                                   'referenced_field': 'T_Id',
                                   'referencing_layer': 'untersmassn_',
                                   'referencing_field': 'avalue'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['belasteter_standort_geo_lage_punkt', 'deponietyp', '0..*', 'deponietyp', 'T_Id', 'dispName'],
            ['belasteter_standort_geo_lage_punkt', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'T_Id', 'dispName'],
            ['belasteter_standort_geo_lage_polygon', 'deponietyp', '0..*', 'deponietyp', 'T_Id', 'dispName'],
            ['belasteter_standort_geo_lage_polygon', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'T_Id', 'dispName']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 2)

    def test_ili2db3_domain_structure_relations_KbS_LV95_V1_3_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/KbS_V1_3.ili')
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_bags_of_enum_kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        # 2 structure-domain relations defined OUT OF A TOPIC are expected
        expected_relations = list()

        expected_relations.append({'name': 'deponietyp__avalue_deponietyp_iliCode',
                                   'referenced_layer': 'deponietyp',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'deponietyp_',
                                   'referencing_field': 'avalue'})

        expected_relations.append({'name': 'untersmassn__avalue_untersmassn_iliCode',
                                   'referenced_layer': 'untersmassn',
                                   'referenced_field': 'iliCode',
                                   'referencing_layer': 'untersmassn_',
                                   'referencing_field': 'avalue'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['belasteter_standort_geo_lage_punkt', 'deponietyp', '0..*', 'deponietyp', 'iliCode', 'dispName'],
            ['belasteter_standort_geo_lage_punkt', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'iliCode', 'dispName'],
            ['belasteter_standort_geo_lage_polygon', 'deponietyp', '0..*', 'deponietyp', 'iliCode', 'dispName'],
            ['belasteter_standort_geo_lage_polygon', 'untersuchungsmassnahmen', '1..*', 'untersmassn', 'iliCode', 'dispName']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field], expected_bags_of_enum)

        self.assertEqual(count, 2)

    def test_domain_class_relations_Hazard_Mapping_V1_2_postgis(self):
        # Test and ili file with lots of comments inside.
        # This test makes sense because we rely on a custom model parser.

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/Hazard_Mapping_V1_2.ili')
        importer.configuration.ilimodels = 'Hazard_Mapping_LV95_V1_2'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        expected_relations = list()  # 41!!! domain-class relations are expected
        expected_relations.append({
            "name": "hazard_area_hazard_level_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "hazard_level",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_intensity_subproc_synoptic_intensity_fkey",
            "referenced_layer": "detailed_process_synop_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "subproc_synoptic_intensity",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_data_responsibility_fkey",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_pa_state_powder_avalanche_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "pa_state_powder_avalanche",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_fl_state_flooding_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "fl_state_flooding",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_be_state_bank_erosion_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "be_state_bank_erosion",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_if_state_ice_fall_fkey",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "if_state_ice_fall",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_water_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "water",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_landslide_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "landslide",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "hazard_area_main_process_fkey",
            "referenced_layer": "main_process_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "main_process",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "intensity_by_source_intensity_class_fkey",
            "referenced_layer": "intensity_type",
            "referencing_layer": "intensity_by_source",
            "referencing_field": "intensity_class",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_rs_state_rock_slide_rock_aval_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "rs_state_rock_slide_rock_aval",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_max_hazard_level_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "max_hazard_level",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "par_flooding_velocity_method_of_assessment_fkey",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_velocity",
            "referencing_field": "method_of_assessment",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "par_flooding_v_x_h_method_of_assessment_fkey",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_v_x_h",
            "referencing_field": "method_of_assessment",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_rockfall_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "rockfall",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "special_indicat_hazard_area_data_responsibility_fkey",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "special_indicat_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_avalanche_fkey",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "avalanche",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "indicative_hazard_area_data_responsibility_fkey",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "indicative_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "par_flooding_depth_method_of_assessment_fkey",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_depth",
            "referencing_field": "method_of_assessment",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "par_debris_flow_depth_method_of_assessment_fkey",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_debris_flow_depth",
            "referencing_field": "method_of_assessment",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_pl_state_permanent_landslide_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "pl_state_permanent_landslide",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "hazard_area_sources_complete_fkey",
            "referenced_layer": "completeness_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "sources_complete",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_su_state_subsidence_fkey",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "su_state_subsidence",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_fa_state_flowing_avalanche_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "fa_state_flowing_avalanche",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "par_debris_flow_velocity_method_of_assessment_fkey",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_debris_flow_velocity",
            "referencing_field": "method_of_assessment",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "special_indicat_hazard_area_special_process_fkey",
            "referenced_layer": "special_indicat_process_type",
            "referencing_layer": "special_indicat_hazard_area",
            "referencing_field": "special_process",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_gs_state_gliding_snow_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "gs_state_gliding_snow",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_rf_state_rock_fall_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "rf_state_rock_fall",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_hd_state_hillslope_debris_flow_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "hd_state_hillslope_debris_flow",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_intensity_intensity_class_fkey",
            "referenced_layer": "intensity_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "intensity_class",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "intensity_by_source_subproc_intensity_by_source_fkey",
            "referenced_layer": "detailed_process_source_type",
            "referencing_layer": "intensity_by_source",
            "referencing_field": "subproc_intensity_by_source",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_data_responsibility_fkey",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "assessment_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_intensity_sources_in_subprocesses_compl_fkey",
            "referenced_layer": "completeness_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "sources_in_subprocesses_compl",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "hazard_area_subprocesses_complete_fkey",
            "referenced_layer": "completeness_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "subprocesses_complete",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "synoptic_hazard_area_assessment_complete_fkey",
            "referenced_layer": "completeness_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "assessment_complete",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "hazard_area_data_responsibility_fkey",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "indicative_hazard_area_indicative_process_fkey",
            "referenced_layer": "indicative_process_type",
            "referencing_layer": "indicative_hazard_area",
            "referencing_field": "indicative_process",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_df_state_debris_flow_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "df_state_debris_flow",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_sh_state_sinkhole_fkey",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "sh_state_sinkhole",
            "referenced_field": "t_id"})
        expected_relations.append({
            "name": "assessment_area_sl_state_spontaneous_landslide_fkey",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "sl_state_spontaneous_landslide",
            "referenced_field": "t_id"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_Hazard_Mapping_V1_2_postgis(self):
        # Test and ili file with lots of comments inside.
        # This test makes sense because we rely on a custom model parser.

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/Hazard_Mapping_V1_2.ili')
        importer.configuration.ilimodels = 'Hazard_Mapping_LV95_V1_2'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list()  # 41!!! domain-class relations are expected
        expected_relations.append({
            "name": "hazard_area_hazard_level_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "hazard_level",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_intensity_subproc_synoptic_intensity_detailed_process_synop_type_ilicode",
            "referenced_layer": "detailed_process_synop_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "subproc_synoptic_intensity",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_data_responsibility_chcantoncode_ilicode",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_pa_state_powder_avalanche_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "pa_state_powder_avalanche",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_fl_state_flooding_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "fl_state_flooding",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_be_state_bank_erosion_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "be_state_bank_erosion",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_if_state_ice_fall_assessment_simple_type_ilicode",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "if_state_ice_fall",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_water_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "water",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_landslide_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "landslide",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "hazard_area_main_process_main_process_type_ilicode",
            "referenced_layer": "main_process_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "main_process",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "intensity_by_source_intensity_class_intensity_type_ilicode",
            "referenced_layer": "intensity_type",
            "referencing_layer": "intensity_by_source",
            "referencing_field": "intensity_class",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_rs_state_rock_slide_rock_aval_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "rs_state_rock_slide_rock_aval",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_max_hazard_level_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "max_hazard_level",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "par_flooding_velocity_method_of_assessment_assessment_method_type_ilicode",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_velocity",
            "referencing_field": "method_of_assessment",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "par_flooding_v_x_h_method_of_assessment_assessment_method_type_ilicode",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_v_x_h",
            "referencing_field": "method_of_assessment",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_rockfall_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "rockfall",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "special_indicat_hazard_area_data_responsibility_chcantoncode_ilicode",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "special_indicat_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_avalanche_hazard_level_type_ilicode",
            "referenced_layer": "hazard_level_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "avalanche",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "indicative_hazard_area_data_responsibility_chcantoncode_ilicode",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "indicative_hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "par_flooding_depth_method_of_assessment_assessment_method_type_ilicode",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_flooding_depth",
            "referencing_field": "method_of_assessment",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "par_debris_flow_depth_method_of_assessment_assessment_method_type_ilicode",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_debris_flow_depth",
            "referencing_field": "method_of_assessment",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_pl_state_permanent_landslide_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "pl_state_permanent_landslide",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "hazard_area_sources_complete_completeness_type_ilicode",
            "referenced_layer": "completeness_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "sources_complete",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_su_state_subsidence_assessment_simple_type_ilicode",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "su_state_subsidence",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_fa_state_flowing_avalanche_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "fa_state_flowing_avalanche",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "par_debris_flow_velocity_method_of_assessment_assessment_method_type_ilicode",
            "referenced_layer": "assessment_method_type",
            "referencing_layer": "par_debris_flow_velocity",
            "referencing_field": "method_of_assessment",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "special_indicat_hazard_area_special_process_special_indicat_process_type_ilicode",
            "referenced_layer": "special_indicat_process_type",
            "referencing_layer": "special_indicat_hazard_area",
            "referencing_field": "special_process",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_gs_state_gliding_snow_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "gs_state_gliding_snow",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_rf_state_rock_fall_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "rf_state_rock_fall",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_hd_state_hillslope_debris_flow_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "hd_state_hillslope_debris_flow",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_intensity_intensity_class_intensity_type_ilicode",
            "referenced_layer": "intensity_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "intensity_class",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "intensity_by_source_subproc_intensity_by_source_detailed_process_source_type_ilicode",
            "referenced_layer": "detailed_process_source_type",
            "referencing_layer": "intensity_by_source",
            "referencing_field": "subproc_intensity_by_source",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_data_responsibility_chcantoncode_ilicode",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "assessment_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_intensity_sources_in_subprocesses_compl_completeness_type_ilicode",
            "referenced_layer": "completeness_type",
            "referencing_layer": "synoptic_intensity",
            "referencing_field": "sources_in_subprocesses_compl",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "hazard_area_subprocesses_complete_completeness_type_ilicode",
            "referenced_layer": "completeness_type",
            "referencing_layer": "hazard_area",
            "referencing_field": "subprocesses_complete",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "synoptic_hazard_area_assessment_complete_completeness_type_ilicode",
            "referenced_layer": "completeness_type",
            "referencing_layer": "synoptic_hazard_area",
            "referencing_field": "assessment_complete",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "hazard_area_data_responsibility_chcantoncode_ilicode",
            "referenced_layer": "chcantoncode",
            "referencing_layer": "hazard_area",
            "referencing_field": "data_responsibility",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "indicative_hazard_area_indicative_process_indicative_process_type_ilicode",
            "referenced_layer": "indicative_process_type",
            "referencing_layer": "indicative_hazard_area",
            "referencing_field": "indicative_process",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_df_state_debris_flow_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "df_state_debris_flow",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_sh_state_sinkhole_assessment_simple_type_ilicode",
            "referenced_layer": "assessment_simple_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "sh_state_sinkhole",
            "referenced_field": "ilicode"})
        expected_relations.append({
            "name": "assessment_area_sl_state_spontaneous_landslide_assessment_complex_type_ilicode",
            "referenced_layer": "assessment_complex_type",
            "referencing_layer": "assessment_area",
            "referencing_field": "sl_state_spontaneous_landslide",
            "referenced_field": "ilicode"})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_domain_class_relations_ZG_Naturschutz_und_Erholungsinfrastruktur_V1_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": "{}_{}_fkey".format(
                                        relation.referencing_layer.name,
                                        relation.referencing_field
                                    )})

        # 5 domain-class relations that come from double inheritance from
        # abstract classes are expected
        expected_relations = list()

        expected_relations.append({'name': 'erholungsinfrastruktur_linienobjekt_zustaendigkeit_fkey',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'erholungsinfrastruktur_linienobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'erholungsinfrastruktur_punktobjekt_zustaendigkeit_fkey',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'erholungsinfrastruktur_punktobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzinfrastruktur_linienobjekt_zustaendigkeit_fkey',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'naturschutzinfrastruktur_linienobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzinfrastruktur_punktobjekt_zustaendigkeit_fkey',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'naturschutzinfrastruktur_punktobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_zustaendigkeit_fkey',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 't_id',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'zustaendigkeit'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def test_ili2db3_domain_class_relations_ZG_Naturschutz_und_Erholungsinfrastruktur_V1_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Naturschutz_und_Erholungsinfrastruktur_V1.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        # 5 domain-class relations that come from double inheritance from
        # abstract classes are expected
        expected_relations = list()

        expected_relations.append({'name': 'erholungsinfrastruktur_linienobjekt_zustaendigkeit_zustaendigkeit_kanton_ilicode',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'erholungsinfrastruktur_linienobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'erholungsinfrastruktur_punktobjekt_zustaendigkeit_zustaendigkeit_kanton_ilicode',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'erholungsinfrastruktur_punktobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzinfrastruktur_linienobjekt_zustaendigkeit_zustaendigkeit_kanton_ilicode',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'naturschutzinfrastruktur_linienobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzinfrastruktur_punktobjekt_zustaendigkeit_zustaendigkeit_kanton_ilicode',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'naturschutzinfrastruktur_punktobjekt',
                                   'referencing_field': 'zustaendigkeit'})

        expected_relations.append({'name': 'naturschutzrelevantes_objekt_ohne_schutzstatus_zustaendigkeit_zustaendigkeit_kanton_ilicode',
                                   'referenced_layer': 'zustaendigkeit_kanton',
                                   'referenced_field': 'ilicode',
                                   'referencing_layer': 'naturschutzrelevantes_objekt_ohne_schutzstatus',
                                   'referencing_field': 'zustaendigkeit'})

        for expected_relation in expected_relations:
            self.assertIn(expected_relation, relations_dicts)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
