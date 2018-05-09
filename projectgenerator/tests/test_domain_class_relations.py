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
from projectgenerator.tests.utils import iliimporter_config, testdata_path
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
        importer.configuration = iliimporter_config(
            importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2pg',
                              'dbname=gis user=docker password=docker host=postgres',
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

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

    def test_domain_class_relations_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2gpkg'
        importer.configuration = iliimporter_config(
            importer.tool_name, 'ilimodels/CIAF_LADM')
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

    def test_domain_class_relations_ZG_Abfallsammelstellen_ZEBA_V1_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.epsg = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2pg',
                              'dbname=gis user=docker password=docker host=postgres',
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

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
        importer.tool_name = 'ili2gpkg'
        importer.configuration = iliimporter_config(importer.tool_name)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/ZG_Abfallsammelstellen_ZEBA_V1.ili')
        importer.configuration.ilimodels = 'Abfallsammelstellen_ZEBA_LV03_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg_2.gpkg')
        importer.configuration.epsg = 21781
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
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/repo/ZG_Naturschutz_und_Erholung_V1_0.ili')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholung_V1_0'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.epsg = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2pg',
                              'dbname=gis user=docker password=docker host=postgres',
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

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
