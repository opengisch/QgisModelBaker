# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 09/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

import configparser
import datetime
import logging
import os
import pathlib
import shutil
import tempfile
from decimal import Decimal

import yaml
from qgis.core import Qgis, QgsEditFormConfig, QgsProject, QgsRelation
from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.testing import start_app, unittest

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libili2db.ilicache import (
    IliDataCache,
    IliDataItemModel,
    IliToppingFileCache,
    IliToppingFileItemModel,
)
from QgisModelBaker.libqgsprojectgen.dataobjects.project import Project
from QgisModelBaker.libqgsprojectgen.db_factory.gpkg_command_config_manager import (
    GpkgCommandConfigManager,
)
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from QgisModelBaker.tests.utils import (
    get_pg_connection_string,
    iliimporter_config,
    testdata_path,
)

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestProjectGen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_ili2db3_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                belasteter_standort_punkt_layer = layer
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                assert fields == set(
                    [
                        "letzteanpassung",
                        "zustaendigkeitkataster",
                        "geo_lage_polygon",
                        "inbetrieb",
                        "ersteintrag",
                        "bemerkung_en",
                        "bemerkung_rm",
                        "katasternummer",
                        "bemerkung_it",
                        "nachsorge",
                        "url_kbs_auszug",
                        "url_standort",
                        "statusaltlv",
                        "bemerkung_fr",
                        "standorttyp",
                        "bemerkung",
                        "geo_lage_punkt",
                        "bemerkung_de",
                        "t_basket",
                    ]
                )

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "parzellenidentifikation",
                        "egrid_",
                        "deponietyp",
                        "untersmassn",
                    ]
                    assert set(tab_list) == set(expected_tab_list)
                    assert len(tab_list) == len(expected_tab_list)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                belasteter_standort_polygon_layer = layer

        assert count == 1
        assert len(available_layers) == 18

        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )

    def test_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                belasteter_standort_punkt_layer = layer
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                assert fields == set(
                    [
                        "letzteanpassung",
                        "zustaendigkeitkataster",
                        "geo_lage_polygon",
                        "inbetrieb",
                        "ersteintrag",
                        "katasternummer",
                        "nachsorge",
                        "url_kbs_auszug",
                        "url_standort",
                        "statusaltlv",
                        "standorttyp",
                        "bemerkung",
                        "bemerkung_de",
                        "bemerkung_fr",
                        "bemerkung_rm",
                        "bemerkung_it",
                        "bemerkung_en",
                        "geo_lage_punkt",
                        "t_basket",
                    ]
                )

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "parzellenidentifikation",
                        "egrid_",
                        "deponietyp",
                        "untersmassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                belasteter_standort_polygon_layer = layer

        assert count == 1
        assert len(available_layers) == 18

        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )

    def test_ili2db3_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_3_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        importer.configuration.db_ili_version = 3
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "belasteter_standort":  # Polygon
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                assert fields == set(
                    [
                        "letzteanpassung",
                        "zustaendigkeitkataster",
                        "geo_lage_polygon",
                        "inbetrieb",
                        "ersteintrag",
                        "bemerkung_en",
                        "bemerkung_rm",
                        "katasternummer",
                        "bemerkung_it",
                        "nachsorge",
                        "url_kbs_auszug",
                        "url_standort",
                        "statusaltlv",
                        "bemerkung_fr",
                        "standorttyp",
                        "bemerkung",
                        "bemerkung_de",
                        "T_basket",
                    ]
                )

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "parzellenidentifikation",
                        "belasteter_standort_geo_lage_punkt",
                        "egrid_",
                        "deponietyp",
                        "untersmassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        assert tab.columnCount() == 2
                    else:
                        assert tab.columnCount() == 1

        assert count == 1
        assert (
            set(
                [
                    "statusaltlv",
                    "multilingualtext",
                    "untersmassn",
                    "multilingualmtext",
                    "languagecode_iso639_1",
                    "deponietyp",
                    "zustaendigkeitkataster",
                    "standorttyp",
                    "localisedtext",
                    "localisedmtext",
                    "belasteter_standort",
                    "deponietyp_",
                    "egrid_",
                    "untersmassn_",
                    "parzellenidentifikation",
                    "belasteter_standort_geo_lage_punkt",
                    "T_ILI2DB_BASKET",
                    "T_ILI2DB_DATASET",
                ]
            )
            == set([layer.name for layer in available_layers])
        )

    def test_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "belasteter_standort":  # Polygon
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                assert fields == set(
                    [
                        "letzteanpassung",
                        "zustaendigkeitkataster",
                        "geo_lage_polygon",
                        "inbetrieb",
                        "ersteintrag",
                        "katasternummer",
                        "nachsorge",
                        "url_kbs_auszug",
                        "url_standort",
                        "statusaltlv",
                        "standorttyp",
                        "bemerkung",
                        "bemerkung_de",
                        "bemerkung_fr",
                        "bemerkung_rm",
                        "bemerkung_it",
                        "bemerkung_en",
                        "T_basket",
                    ]
                )

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "parzellenidentifikation",
                        "belasteter_standort_geo_lage_punkt",
                        "egrid_",
                        "deponietyp",
                        "untersmassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        assert tab.columnCount() == 2
                    else:
                        assert tab.columnCount() == 1

        assert count == 1
        assert (
            set(
                [
                    "statusaltlv",
                    "multilingualtext",
                    "untersmassn",
                    "multilingualmtext",
                    "languagecode_iso639_1",
                    "deponietyp",
                    "zustaendigkeitkataster",
                    "standorttyp",
                    "localisedtext",
                    "localisedmtext",
                    "belasteter_standort",
                    "deponietyp_",
                    "egrid_",
                    "untersmassn_",
                    "parzellenidentifikation",
                    "belasteter_standort_geo_lage_punkt",
                    "T_ILI2DB_BASKET",
                    "T_ILI2DB_DATASET",
                ]
            )
            == set([layer.name for layer in available_layers])
        )

    def test_naturschutz_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 13
        assert len(available_layers) == 25
        assert len(relations) == 29

    def test_naturschutz_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 22
        assert len(available_layers) == 25
        assert len(relations) == 29

    def test_naturschutz_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart1", importer.configuration.dbschema
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 17
        assert len(available_layers) == 25
        assert len(relations) == 38

    def test_naturschutz_set_ignored_layers_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 15
        assert len(available_layers) == 23
        assert len(relations) == 26

    def test_naturschutz_set_ignored_layers_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        legend = generator.legend(available_layers)
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 24
        assert len(available_layers) == 23
        assert len(relations) == 26

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        layer_names = [l.name().lower() for l in qgis_project.mapLayers().values()]
        assert "einzelbaum" not in layer_names
        assert "datenbestand" not in layer_names
        assert "hochstamm_obstgarten" in layer_names

    def test_naturschutz_set_ignored_layers_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart1", importer.configuration.dbschema
        )

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 19
        assert len(available_layers) == 23
        assert len(relations) == 35

    def test_naturschutz_nometa_postgis(self):
        # model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta"
        )
        importer.configuration.dbschema = "naturschutz_nometa_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 7
        assert len(available_layers) == 31
        assert len(relations) == 45

    def test_naturschutz_nometa_geopackage(self):
        # model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_nometa_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 16
        assert len(available_layers) == 31
        assert len(relations) == 45

    def test_ranges_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '9.9999999999999906e+013'

                count += 1
                break

        assert count == 1

    def test_ranges_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_ranges_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '9.99999999999999E13'

                count += 1
                break

        assert count == 1

    def test_ranges_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '99999999999999.9'

                count += 1
                break

        assert count == 1

    def test_precision_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_prec_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_precision_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_precision_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_precision_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_prec_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_extent_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_extent_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_extent_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_extent_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_nmrel_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "CoordSys"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "geoellipsoidal":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("lambert_from5_fkey")
                assert map["nm-rel"] == "lambert_to5_fkey"
                map = edit_form_config.widgetConfig("axis_geoellipsoidal_axis_fkey")
                assert bool(map) is False
        assert count == 1

    def test_nmrel_geopackage(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "CoordSys"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_nmrel_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "geoellipsoidal":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("lambert_from5_geoellipsoidal_T_Id")
                assert map["nm-rel"] == "lambert_to5_geocartesian2d_T_Id"
                map = edit_form_config.widgetConfig(
                    "axis_geoellipsoidal_axis_geoellipsoidal_T_Id"
                )
                assert bool(map) is False
        assert count == 1

    def test_meta_attr_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"t_ili_tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"t_id"'
                )

        assert count == 2

    def test_meta_attr_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_meta_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )

        assert count == 2

    def test_meta_attr_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()

        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )

        assert count == 2

    def test_meta_attr_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"t_ili_tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"t_id"'
                )
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_hidden_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/hidden_fields.toml")
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in project.layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        assert len(attribute_names) == 19
                        assert "tipo" not in attribute_names
                        assert "avaluo" not in attribute_names

        assert count == 1

    def test_meta_attr_hidden_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/hidden_fields.toml")
        importer.configuration.inheritance = "smart2"
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in project.layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        assert len(attribute_names) == 19
                        assert "tipo" not in attribute_names
                        assert "avaluo" not in attribute_names

        assert count == 1

    def test_meta_attr_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_order_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_order_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_meta_attr_order_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_meta_attr_order_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")
        importer.configuration.inheritance = "smart2"
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_bagof_cardinalities_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/CardinalityBag.ili")
        importer.configuration.ilimodels = "CardinalityBag"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ["fische_None", "valuerelation_0", "0..*", "ei_typen", "t_id", "dispname"],
            ["fische_None", "valuerelation_1", "1..*", "ei_typen", "t_id", "dispname"],
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                assert [
                    layer_name,
                    attribute,
                    cardinality,
                    domain_table.name,
                    key_field,
                    value_field,
                ] in expected_bags_of_enum

        assert count == 2

        # Test constraints
        for layer in available_layers:
            if layer.name == "fische":
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("valuerelation_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("valuerelation_1")
                    )
                    == 'array_length("valuerelation_1")>0'
                )

    def test_bagof_cardinalities_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/CardinalityBag.ili")
        importer.configuration.ilimodels = "CardinalityBag"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_bags_of_enum_CardinalityBag_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ["fische_None", "valuerelation_0", "0..*", "ei_typen", "T_Id", "dispName"],
            ["fische_None", "valuerelation_1", "1..*", "ei_typen", "T_Id", "dispName"],
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                assert [
                    layer_name,
                    attribute,
                    cardinality,
                    domain_table.name,
                    key_field,
                    value_field,
                ] in expected_bags_of_enum

        assert count == 2

        # Test constraints
        for layer in available_layers:
            if layer.name == "fische":
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("valuerelation_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("valuerelation_1")
                    )
                    == 'array_length("valuerelation_1")>0'
                )

    def test_relation_strength_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbschema = "assoc23_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert (
            qgis_project.relationManager().relation("agg3_agg3_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("agg3_agg3_b_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_b_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg1_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg2_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc1_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc2_a_fkey").strength()
            == QgsRelation.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager().relation("classb1_comp1_a_fkey").strength()
            == QgsRelation.Composition
        )

    def test_relation_strength_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_assoc23_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert (
            qgis_project.relationManager()
            .relation("agg3_agg3_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("agg3_agg3_b_classb1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("assoc3_assoc3_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("assoc3_assoc3_b_classb1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_agg1_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_agg2_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_assoc1_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_assoc2_a_classa1_T_Id")
            .strength()
            == QgsRelation.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager()
            .relation("classb1_comp1_a_classa1_T_Id")
            .strength()
            == QgsRelation.Composition
        )

    def test_relation_strength_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbschema = "assoc23_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert (
            qgis_project.relationManager().relation("agg3_agg3_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("agg3_agg3_b_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_b_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg1_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg2_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc1_a_fkey").strength()
            == QgsRelation.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc2_a_fkey").strength()
            == QgsRelation.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager().relation("classb1_comp1_a_fkey").strength()
            == QgsRelation.Composition
        )

    def test_kbs_postgis_basket_handling(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the system group for the basket layers
        system_group = qgis_project.layerTreeRoot().findGroup("system")
        assert system_group is not None
        system_group_layers = system_group.findLayers()
        assert set([layer.name() for layer in system_group_layers]) == {
            "t_ili2db_dataset",
            "t_ili2db_basket",
        }
        assert [layer.layer().readOnly() for layer in system_group_layers] == [
            True,
            True,
        ]

        count = 0
        for layer in available_layers:
            # check the widget configuration of the t_basket field
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("t_basket")
                assert map["Relation"] == "belasteter_standort_t_basket_fkey"
                assert (
                    map["FilterExpression"]
                    == "\"topic\" = 'KbS_LV95_V1_3.Belastete_Standorte'"
                )

            # check the display expression of the basket table
            if layer.name == "t_ili2db_basket":
                count += 1
                display_expression = layer.layer.displayExpression()
                assert (
                    display_expression
                    == "coalesce(attribute(get_feature('t_ili2db_dataset', 't_id', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('t_ili2db_dataset', 't_id', dataset), 'datasetname'), t_ili_tid))"
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_geopackage_basket_handling(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the system group for the basket layers
        system_group = qgis_project.layerTreeRoot().findGroup("system")
        assert system_group is not None
        system_group_layers = system_group.findLayers()
        assert set([layer.name() for layer in system_group_layers]) == {
            "T_ILI2DB_DATASET",
            "T_ILI2DB_BASKET",
        }
        assert [layer.layer().readOnly() for layer in system_group_layers] == [
            True,
            True,
        ]

        count = 0
        for layer in available_layers:
            # check the widget configuration of the t_basket field
            if layer.name == "belasteter_standort":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("T_basket")
                assert (
                    map["Relation"]
                    == "belasteter_standort_T_basket_T_ILI2DB_BASKET_T_Id"
                )
                assert (
                    map["FilterExpression"]
                    == "\"topic\" = 'KbS_LV95_V1_3.Belastete_Standorte'"
                )

            # check the display expression of the basket table
            if layer.name == "T_ILI2DB_BASKET":
                count += 1
                display_expression = layer.layer.displayExpression()
                assert (
                    display_expression
                    == "coalesce(attribute(get_feature('T_ILI2DB_DATASET', 'T_Id', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('T_ILI2DB_DATASET', 'T_Id', dataset), 'datasetname'), T_Ili_Tid))"
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_postgis_toppings(self):
        """
        Reads this metaconfig found in ilidata.xml according to the modelname KbS_LV95_V1_4

        [CONFIGURATION]
        qgis.modelbaker.layertree=file:tests/testdata/ilirepo/24/layertree/opengis_layertree_KbS_LV95_V1_4.yaml
        ch.interlis.referenceData=ilidata:ch.sh.ili.catalogue.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        defaultSrsCode=3857
        models=KbS_Basis_V1_4
        preScript=file:tests/testdata/ilirepo/24/sql/opengisch_KbS_LV95_V1_4_test.sql
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml

        [qgis.modelbaker.qml]
        "Belasteter_Standort (Geo_Lage_Polygon)"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001
        "Belasteter_Standort (Geo_Lage_Punkt)"=file:tests/testdata/ilirepo/24/qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_punkt.qml
        Parzellenidentifikation=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005
        """

        toppings_test_path = os.path.join(test_path, "testdata", "ilirepo", "24")

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, os.path.join(test_path, "testdata", "ilirepo", "24")
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        # get the metaconfiguration
        ilimetaconfigcache = IliDataCache(
            importer.configuration.base_configuration, "KbS_LV95_V1_4"
        )
        ilimetaconfigcache.refresh()
        matches_on_id = ilimetaconfigcache.model.match(
            ilimetaconfigcache.model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_localfiletest",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True

        repository = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ILIREPO)
        )
        url = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.URL)
        )
        path = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.RELATIVEFILEPATH)
        )
        dataset_id = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ID)
        )

        metaconfig_path = ilimetaconfigcache.download_file(
            repository, url, path, dataset_id
        )
        metaconfig = self.load_metaconfig(
            os.path.join(toppings_test_path, metaconfig_path)
        )

        # Read ili2db settings
        assert "ch.ehi.ili2db" in metaconfig.sections()
        ili2db_metaconfig = metaconfig["ch.ehi.ili2db"]
        model_list = importer.configuration.ilimodels.strip().split(
            ";"
        ) + ili2db_metaconfig.get("models").strip().split(";")
        importer.configuration.ilimodels = ";".join(model_list)
        assert importer.configuration.ilimodels == "KbS_LV95_V1_4;KbS_Basis_V1_4"
        srs_code = ili2db_metaconfig.get("defaultSrsCode")
        importer.configuration.srs_code = srs_code
        assert importer.configuration.srs_code == "3857"
        command = importer.command(True)
        assert "KbS_LV95_V1_4;KbS_Basis_V1_4" in command
        assert "3857" in command

        # read and download topping files in ili2db settings (prefixed with ilidata or file - means they are found in ilidata.xml or referenced locally)
        ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
        ili_meta_attrs_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, ili_meta_attrs_list
        )
        # absolute path since it's defined as ilidata:...
        expected_ili_meta_attrs_file_path_list = [
            os.path.join(toppings_test_path, "toml/sh_KbS_LV95_V1_4.toml")
        ]
        assert expected_ili_meta_attrs_file_path_list == ili_meta_attrs_file_path_list
        importer.configuration.tomlfile = ili_meta_attrs_file_path_list[0]

        prescript_list = ili2db_metaconfig.get("preScript").split(";")
        prescript_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, prescript_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_prescript_file_path_list = [
            os.path.join(toppings_test_path, "sql/opengisch_KbS_LV95_V1_4_test.sql")
        ]
        assert expected_prescript_file_path_list == prescript_file_path_list
        importer.configuration.pre_script = prescript_file_path_list[0]

        command = importer.command(True)
        assert "opengisch_KbS_LV95_V1_4_test.sql" in command
        assert "sh_KbS_LV95_V1_4.toml" in command

        # and override defaultSrsCode manually
        importer.configuration.srs_code = "2056"

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        # Toppings legend and layers: apply
        assert "CONFIGURATION" in metaconfig.sections()
        configuration_section = metaconfig["CONFIGURATION"]
        assert "qgis.modelbaker.layertree" in configuration_section
        layertree_data_list = configuration_section["qgis.modelbaker.layertree"].split(
            ";"
        )
        layertree_data_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, layertree_data_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_layertree_data_file_path_list = [
            os.path.join(
                toppings_test_path, "layertree/opengis_layertree_KbS_LV95_V1_4.yaml"
            )
        ]
        assert layertree_data_file_path_list == expected_layertree_data_file_path_list
        layertree_data_file_path = layertree_data_file_path_list[0]

        custom_layer_order_structure = list()
        with open(layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )
            assert "layer-order" in layertree_data
            custom_layer_order_structure = layertree_data["layer-order"]

        assert len(custom_layer_order_structure) == 2

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the legend with layers, groups and subgroups
        belasteter_standort_group = qgis_project.layerTreeRoot().findGroup(
            "Belasteter Standort"
        )
        assert belasteter_standort_group is not None
        belasteter_standort_group_layer = belasteter_standort_group.findLayers()
        assert [layer.name() for layer in belasteter_standort_group_layer] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
        ]
        informationen_group = qgis_project.layerTreeRoot().findGroup("Informationen")
        assert informationen_group is not None
        informationen_group_layers = informationen_group.findLayers()
        assert [layer.name() for layer in informationen_group_layers] == [
            "EGRID_",
            "Deponietyp_",
            "ZustaendigkeitKataster",
            "Untersuchungsmassnahmen_Definition",
            "StatusAltlV_Definition",
            "Standorttyp_Definition",
            "Deponietyp_Definition",
            "Parzellenidentifikation",
            "UntersMassn_",
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]

        text_infos_group = informationen_group.findGroup("Text Infos")
        assert text_infos_group is not None
        text_infos_group_layers = text_infos_group.findLayers()
        assert [layer.name() for layer in text_infos_group_layers] == [
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
        ]
        other_infos_group = informationen_group.findGroup("Other Infos")
        self.assertIsNotNone(other_infos_group)
        other_infos_group_layers = other_infos_group.findLayers()
        assert [layer.name() for layer in other_infos_group_layers] == [
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]
        # check the node properties
        belasteter_standort_punkt_layer = None
        belasteter_standort_polygon_layer = None
        for layer in belasteter_standort_group_layer:
            if layer.name() == "Belasteter_Standort (Geo_Lage_Punkt)":
                belasteter_standort_punkt_layer = layer
            if layer.name() == "Belasteter_Standort (Geo_Lage_Polygon)":
                belasteter_standort_polygon_layer = layer
        assert belasteter_standort_punkt_layer is not None
        assert belasteter_standort_polygon_layer is not None
        assert belasteter_standort_group.isMutuallyExclusive() is True
        assert (
            belasteter_standort_punkt_layer.isVisible() is False
        )  # because of the mutually-child
        assert (
            belasteter_standort_polygon_layer.isVisible() is True
        )  # because of the mutually-child
        assert belasteter_standort_punkt_layer.isExpanded() is False
        assert belasteter_standort_polygon_layer.isExpanded() is True
        assert (
            bool(belasteter_standort_punkt_layer.customProperty("showFeatureCount"))
            is True
        )
        assert (
            bool(belasteter_standort_polygon_layer.customProperty("showFeatureCount"))
            is False
        )
        egrid_layer = None
        zustaendigkeitkataster_layer = None
        for layer in informationen_group_layers:
            if layer.name() == "EGRID_":
                egrid_layer = layer
            if layer.name() == "ZustaendigkeitKataster":
                zustaendigkeitkataster_layer = layer
        assert egrid_layer is not None
        assert zustaendigkeitkataster_layer is not None
        assert bool(egrid_layer.customProperty("showFeatureCount")) is False
        assert (
            bool(zustaendigkeitkataster_layer.customProperty("showFeatureCount"))
            is True
        )
        assert text_infos_group.isExpanded() is True
        assert text_infos_group.isVisible() is False
        assert other_infos_group.isVisible() is True
        assert other_infos_group.isExpanded() is False

        # check the custom layer order
        assert bool(qgis_project.layerTreeRoot().hasCustomLayerOrder()) is True
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[0].name()
            == "Belasteter_Standort (Geo_Lage_Polygon)"
        )
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[1].name()
            == "Belasteter_Standort (Geo_Lage_Punkt)"
        )

        # and read qml part, download files and check the form configurations set by the qml
        assert "qgis.modelbaker.qml" in metaconfig.sections()
        qml_section = dict(metaconfig["qgis.modelbaker.qml"])
        assert list(qml_section.values()) == [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "file:tests/testdata/ilirepo/24/qml/opengisch_KbS_LV95_V1_4_004_belasteterstandort_punkt.qml",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]
        qml_file_model = self.get_topping_file_model(
            importer.configuration.base_configuration, list(qml_section.values())
        )
        for layer in project.layers:
            if layer.alias:
                if any(layer.alias.lower() == s for s in qml_section):
                    layer_qml = layer.alias.lower()
                elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                    layer_qml = f'"{layer.alias.lower()}"'
                else:
                    continue
                matches = qml_file_model.match(
                    qml_file_model.index(0, 0),
                    Qt.DisplayRole,
                    qml_section[layer_qml],
                    1,
                )
                if matches:
                    style_file_path = matches[0].data(
                        int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                    )
                    layer.layer.loadNamedStyle(style_file_path)

        layer_names = set([layer.name for layer in available_layers])
        assert layer_names == {
            "untersuchungsmassnahmen_definition",
            "statusaltlv_definition",
            "untersmassn",
            "deponietyp_definition",
            "parzellenidentifikation",
            "multilingualtext",
            "languagecode_iso639_1",
            "belasteter_standort",
            "zustaendigkeitkataster",
            "deponietyp_",
            "standorttyp",
            "localisedtext",
            "multilingualmtext",
            "untersmassn_",
            "statusaltlv",
            "localisedmtext",
            "standorttyp_definition",
            "egrid_",
            "deponietyp",
            "t_ili2db_basket",
            "t_ili2db_dataset",
        }

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                field_names = set([field.name() for field in tabs[0].children()])
                assert field_names == {
                    "geo_lage_polygon",
                    "bemerkung_de",
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "url_standort",
                    "bemerkung_rm",
                    "standorttyp",
                    "bemerkung_en",
                    "inbetrieb",
                    "geo_lage_punkt",
                    "bemerkung_it",
                    "url_kbs_auszug",
                    "bemerkung",
                    "nachsorge",
                    "ersteintrag",
                    "bemerkung_fr",
                    "katasternummer",
                    "statusaltlv",
                }

                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Bemerkung Romanisch"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Bemerkung Italienisch"
            if layer.name == "parzellenidentifikation":
                count += 1
                assert (
                    layer.layer.displayExpression()
                    == "nbident || ' - '  || \"parzellennummer\" "
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_geopackage_toppings(self):
        """
        Reads this metaconfig found in ilidata.xml according to the modelname KbS_LV95_V1_4

        [CONFIGURATION]
        qgis.modelbaker.layertree=file:tests/testdata/ilirepo/24/layertree/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml
        ch.interlis.referenceData=ilidata:ch.sh.ili.catalogue.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        models = KbS_Basis_V1_4
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml
        preScript=file:tests/testdata/ilirepo/24/sql/opengisch_KbS_LV95_V1_4_test.sql
        defaultSrsCode=3857

        [qgis.modelbaker.qml]
        "Belasteter_Standort"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001
        "Belasteter_Standort (Geo_Lage_Punkt)"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004
        Parzellenidentifikation=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005
        """

        toppings_test_path = os.path.join(test_path, "testdata", "ilirepo", "24")

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, os.path.join(test_path, "testdata", "ilirepo", "24")
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_toppings_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )

        # get the metaconfiguration
        ilimetaconfigcache = IliDataCache(
            importer.configuration.base_configuration, "KbS_LV95_V1_4"
        )
        ilimetaconfigcache.refresh()
        matches_on_id = ilimetaconfigcache.model.match(
            ilimetaconfigcache.model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg_localfiletest",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True

        repository = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ILIREPO)
        )
        url = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.URL)
        )
        path = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.RELATIVEFILEPATH)
        )
        dataset_id = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ID)
        )

        metaconfig_path = ilimetaconfigcache.download_file(
            repository, url, path, dataset_id
        )
        metaconfig = self.load_metaconfig(
            os.path.join(toppings_test_path, metaconfig_path)
        )

        # Read ili2db settings
        assert "ch.ehi.ili2db" in metaconfig.sections()
        ili2db_metaconfig = metaconfig["ch.ehi.ili2db"]
        model_list = importer.configuration.ilimodels.strip().split(
            ";"
        ) + ili2db_metaconfig.get("models").strip().split(";")
        importer.configuration.ilimodels = ";".join(model_list)
        assert importer.configuration.ilimodels == "KbS_LV95_V1_4;KbS_Basis_V1_4"
        srs_code = ili2db_metaconfig.get("defaultSrsCode")
        importer.configuration.srs_code = srs_code
        assert importer.configuration.srs_code == "3857"
        command = importer.command(True)
        assert "KbS_LV95_V1_4;KbS_Basis_V1_4" in command
        assert "3857" in command

        # read and download topping files in ili2db settings (prefixed with ilidata or file - means they are found in ilidata.xml or referenced locally)
        ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
        ili_meta_attrs_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, ili_meta_attrs_list
        )
        # absolute path since it's defined as ilidata:...
        expected_ili_meta_attrs_file_path_list = [
            os.path.join(toppings_test_path, "toml/sh_KbS_LV95_V1_4.toml")
        ]
        assert expected_ili_meta_attrs_file_path_list == ili_meta_attrs_file_path_list
        importer.configuration.tomlfile = ili_meta_attrs_file_path_list[0]

        prescript_list = ili2db_metaconfig.get("preScript").split(";")
        prescript_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, prescript_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_prescript_file_path_list = [
            os.path.join(toppings_test_path, "sql/opengisch_KbS_LV95_V1_4_test.sql")
        ]
        assert expected_prescript_file_path_list == prescript_file_path_list
        importer.configuration.pre_script = prescript_file_path_list[0]

        command = importer.command(True)
        assert "opengisch_KbS_LV95_V1_4_test.sql" in command
        assert "sh_KbS_LV95_V1_4.toml" in command

        # and override defaultSrsCode manually
        importer.configuration.srs_code = "2056"

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        # Toppings legend and layers: apply
        assert "CONFIGURATION" in metaconfig.sections()
        configuration_section = metaconfig["CONFIGURATION"]
        assert "qgis.modelbaker.layertree" in configuration_section
        layertree_data_list = configuration_section["qgis.modelbaker.layertree"].split(
            ";"
        )
        layertree_data_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, layertree_data_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_layertree_data_file_path_list = [
            os.path.join(
                toppings_test_path,
                "layertree/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml",
            )
        ]
        assert layertree_data_file_path_list == expected_layertree_data_file_path_list
        layertree_data_file_path = layertree_data_file_path_list[0]

        custom_layer_order_structure = list()
        with open(layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )
            assert "layer-order" in layertree_data
            custom_layer_order_structure = layertree_data["layer-order"]

        assert len(custom_layer_order_structure) == 2

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the legend with layers, groups and subgroups
        belasteter_standort_group = qgis_project.layerTreeRoot().findGroup(
            "Belasteter Standort"
        )
        assert belasteter_standort_group is not None
        belasteter_standort_group_layer = belasteter_standort_group.findLayers()
        assert [layer.name() for layer in belasteter_standort_group_layer] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort",
        ]

        informationen_group = qgis_project.layerTreeRoot().findGroup("Informationen")
        assert informationen_group is not None
        informationen_group_layers = informationen_group.findLayers()

        assert [layer.name() for layer in informationen_group_layers] == [
            "EGRID_",
            "Deponietyp_",
            "ZustaendigkeitKataster",
            "Untersuchungsmassnahmen_Definition",
            "StatusAltlV_Definition",
            "Standorttyp_Definition",
            "Deponietyp_Definition",
            "Parzellenidentifikation",
            "UntersMassn_",
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]

        text_infos_group = informationen_group.findGroup("Text Infos")
        assert text_infos_group is not None
        text_infos_group_layers = text_infos_group.findLayers()
        assert [layer.name() for layer in text_infos_group_layers] == [
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
        ]
        other_infos_group = informationen_group.findGroup("Other Infos")
        assert other_infos_group is not None
        other_infos_group_layers = other_infos_group.findLayers()
        assert [layer.name() for layer in other_infos_group_layers] == [
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]
        # check the node properties
        belasteter_standort_punkt_layer = None
        belasteter_standort_polygon_layer = None
        for layer in belasteter_standort_group_layer:
            if layer.name() == "Belasteter_Standort (Geo_Lage_Punkt)":
                belasteter_standort_punkt_layer = layer
            if layer.name() == "Belasteter_Standort":
                belasteter_standort_polygon_layer = layer
        assert belasteter_standort_punkt_layer is not None
        assert belasteter_standort_polygon_layer is not None
        assert (
            belasteter_standort_punkt_layer.isVisible() is False
        )  # because of yaml setting
        assert (
            belasteter_standort_polygon_layer.isVisible() is True
        )  # because of yaml setting
        assert belasteter_standort_punkt_layer.isExpanded() is False
        assert belasteter_standort_polygon_layer.isExpanded() is True
        assert (
            bool(belasteter_standort_punkt_layer.customProperty("showFeatureCount"))
            is True
        )
        assert (
            bool(belasteter_standort_polygon_layer.customProperty("showFeatureCount"))
            is False
        )
        egrid_layer = None
        zustaendigkeitkataster_layer = None
        for layer in informationen_group_layers:
            if layer.name() == "EGRID_":
                egrid_layer = layer
            if layer.name() == "ZustaendigkeitKataster":
                zustaendigkeitkataster_layer = layer
        assert egrid_layer is not None
        assert zustaendigkeitkataster_layer is not None
        assert bool(egrid_layer.customProperty("showFeatureCount")) is False
        assert (
            bool(zustaendigkeitkataster_layer.customProperty("showFeatureCount"))
            is True
        )
        assert text_infos_group.isExpanded() is True
        assert text_infos_group.isVisible() is False
        assert other_infos_group.isVisible() is True
        assert other_infos_group.isExpanded() is False

        # check the custom layer order
        assert bool(qgis_project.layerTreeRoot().hasCustomLayerOrder()) is True
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[0].name()
            == "Belasteter_Standort"
        )
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[1].name()
            == "Belasteter_Standort (Geo_Lage_Punkt)"
        )

        # and read qml part, download files and check the form configurations set by the qml
        assert "qgis.modelbaker.qml" in metaconfig.sections()
        qml_section = dict(metaconfig["qgis.modelbaker.qml"])
        assert list(qml_section.values()) == [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004_GPKG",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]
        qml_file_model = self.get_topping_file_model(
            importer.configuration.base_configuration, list(qml_section.values())
        )
        for layer in project.layers:
            if layer.alias:
                if any(layer.alias.lower() == s for s in qml_section):
                    layer_qml = layer.alias.lower()
                elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                    layer_qml = f'"{layer.alias.lower()}"'
                else:
                    continue
                matches = qml_file_model.match(
                    qml_file_model.index(0, 0),
                    Qt.DisplayRole,
                    qml_section[layer_qml],
                    1,
                )
                if matches:
                    style_file_path = matches[0].data(
                        int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                    )
                    layer.layer.loadNamedStyle(style_file_path)

        layer_names = set([layer.name for layer in available_layers])
        assert layer_names == {
            "untersuchungsmassnahmen_definition",
            "statusaltlv_definition",
            "untersmassn",
            "deponietyp_definition",
            "parzellenidentifikation",
            "multilingualtext",
            "languagecode_iso639_1",
            "belasteter_standort",
            "zustaendigkeitkataster",
            "deponietyp_",
            "standorttyp",
            "localisedtext",
            "multilingualmtext",
            "untersmassn_",
            "statusaltlv",
            "localisedmtext",
            "standorttyp_definition",
            "egrid_",
            "deponietyp",
            "belasteter_standort_geo_lage_punkt",
            "T_ILI2DB_BASKET",
            "T_ILI2DB_DATASET",
        }

        count = 0
        for layer in available_layers:
            if layer.name == "belasteter_standort":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                field_names = set([field.name() for field in tabs[0].children()])
                assert field_names == {
                    "geo_lage_polygon",
                    "bemerkung_de",
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "url_standort",
                    "bemerkung_rm",
                    "standorttyp",
                    "bemerkung_en",
                    "inbetrieb",
                    "geo_lage_punkt",
                    "bemerkung_it",
                    "url_kbs_auszug",
                    "bemerkung",
                    "nachsorge",
                    "ersteintrag",
                    "bemerkung_fr",
                    "katasternummer",
                    "statusaltlv",
                }

                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Bemerkung Romanisch"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Bemerkung Italienisch"
            if layer.name == "parzellenidentifikation":
                count += 1
                assert (
                    layer.layer.displayExpression()
                    == "nbident || ' - '  || \"parzellennummer\" "
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_postgis_multisurface(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.tomlfile = testdata_path("toml/multisurface.toml")
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Punkt)"

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Polygon)"

        assert count == 2

    def test_kbs_geopackage_multisurface(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.tomlfile = testdata_path("toml/multisurface.toml")
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort_geo_lage_punkt"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Punkt)"

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort"

        assert count == 2

    def test_unit(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )

        importer.configuration.dbschema = "nue_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()

        infra_po = next(
            (
                layer
                for layer in available_layers
                if layer.name == "erholungsinfrastruktur_punktobjekt"
            )
        )
        naechste_kontrolle = next(
            (field for field in infra_po.fields if field.name == "naechste_kontrolle")
        )
        assert naechste_kontrolle.alias == "Naechste_Kontrolle"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    def load_metaconfig(self, path):
        metaconfig = configparser.ConfigParser()
        metaconfig.clear()
        metaconfig.read_file(open(path))
        metaconfig.read(path)
        return metaconfig

    # that's the same like in generate_project.py
    def get_topping_file_list(self, base_config, id_list):
        topping_file_model = self.get_topping_file_model(base_config, id_list)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, base_config, id_list):
        topping_file_cache = IliToppingFileCache(base_config, id_list)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        return topping_file_cache.model

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
