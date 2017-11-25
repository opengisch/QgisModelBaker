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
import nose2

from projectgenerator.libili2db import iliimporter
from projectgenerator.tests.utils import iliimporter_config
from projectgenerator.libqgsprojectgen.generator.generator import Generator
from qgis.testing import unittest, start_app

start_app()


class TestDomainClassRelation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_domain_class_relations_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2pg',
                              'dbname=gis user=docker password=docker host=postgres',
                              importer.configuration.inheritance,
                              importer.configuration.schema)

        available_layers = generator.layers()
        relations = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list() # 6 domain-class relations are expected
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

    def test_domain_class_relations_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2gpkg'
        importer.configuration = iliimporter_config(importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg.gpkg')
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2gpkg',
                              importer.configuration.uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations = generator.relations(available_layers)

        # Check domain class relations in the relations list
        relations_dicts = list()
        for relation in relations:
            relations_dicts.append({"referencing_layer": relation.referencing_layer.name,
                                    "referenced_layer": relation.referenced_layer.name,
                                    "referencing_field": relation.referencing_field,
                                    "referenced_field": relation.referenced_field,
                                    "name": relation.name})

        expected_relations = list() # 6 domain-class relations are expected
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

    def print_info(self, text):
        print(text)

    def print_error(self, text):
        print(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)

if __name__ == '__main__':
    nose2.main()
