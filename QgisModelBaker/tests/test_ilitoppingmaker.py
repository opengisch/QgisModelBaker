import datetime
import logging
import os
import tempfile

from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.internal_libs.ilitoppingmaker import (
    ExportSettings,
    IliData,
    IliProjectTopping,
    IliTarget,
    MetaConfig,
)
from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.db_factory.gpkg_command_config_manager import (
    GpkgCommandConfigManager,
)
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper import iliimporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.tests.utils import testdata_path


class IliToppingMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppingmaker_test_path = os.path.join(cls.basetestpath, "toppingmaker")

        # create a project of KbS_V1_5 with some additional layers
        (
            cls.project,
            cls.dbfile,
            cls.export_settings,
        ) = cls.make_project_and_export_settings(cls)

    def test_workflow_stepbystep(self):
        # create topping maker without any constructor params
        topping = IliProjectTopping()

        # Check if the export_settings are applied properly when created the projecttopping
        # load QGIS project into structure
        countchecked = 0
        topping.parse_project(self.project, self.export_settings)
        for item in topping.layertree.items:
            if item.name == "Layer One":
                assert item.properties.qmlstylefile
                assert not item.properties.definitionfile
                assert not (item.properties.provider or item.properties.uri)
                countchecked += 1
            if item.name == "Layer Two":
                assert not item.properties.qmlstylefile
                assert not item.properties.definitionfile
                assert item.properties.provider and item.properties.uri
                countchecked += 1
            if item.name == "Layer Three":
                assert item.properties.qmlstylefile
                assert item.properties.definitionfile
                assert item.properties.provider and item.properties.uri
                countchecked += 1
            if item.name == "Layer Four":
                assert not item.properties.qmlstylefile
                assert item.properties.definitionfile
                assert not (item.properties.provider or item.properties.uri)
                countchecked += 1
            if item.name == "Layer Five":
                assert not item.properties.qmlstylefile
                assert item.properties.definitionfile
                assert not (item.properties.provider or item.properties.uri)
                countchecked += 1
            if item.name == "Belasteter_Standort (Geo_Lage_Punkt)":
                assert item.properties.qmlstylefile
                assert not item.properties.definitionfile
                assert not (item.properties.provider or item.properties.uri)
                countchecked += 1
            if item.name == "Belasteter_Standort":
                assert not item.properties.qmlstylefile
                assert not item.properties.definitionfile
                assert item.properties.provider and item.propertiestem.uri
                countchecked += 1
        assert countchecked == 7

        # let's pretend that we received the models from the parsed schemas of the project and selected Kbs_V1_5
        assert topping.set_models == ["KbS_V1_5"]

        # let's pretend that the user selected some referencedata via filebrowser and maybe repos
        codetexte_xtf = testdata_path("xtf/KbS_Codetexte_V1_5_20211015.xtf")
        topping.set_referencedata_paths = [
            codetexte_xtf,
            "ilidata:data_from_another_repo",
        ]

        # let's pretend that we received the parsed schemas of the project and selected one specific. So we got the configuration.
        # we append a metaattr file (toml), and a postscript we select from a repo
        configuration = Ili2DbCommandConfiguration()
        configuration.dbfile = self.dbfile

        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            topping.metaconfig.ili2db_settings.parse_parameters_from_db(db_connector)

        topping.metaconfig.ili2db_settings.metaattr_path = testdata_path(
            "toml/KbS_V1_5.toml"
        )
        topping.metaconfig.ili2db_settings.prescript_path = ""
        topping.metaconfig.ili2db_settings.postscript_path = (
            "ilidata:postscript_from_another_repo"
        )

        # Check if the settings are loaded from the database
        assert topping.metaconfig.ili2db_settings.parameters["defaultSrsCode"] == 2056
        assert (
            topping.metaconfig.ili2db_settings.parameters["smart2Inheritance"] == True
        )
        assert topping.metaconfig.ili2db_settings.parameters["strokeArcs"] == False
        assert topping.metaconfig.ili2db_settings.parameters["importTid"] == True
        assert topping.metaconfig.ili2db_settings.parameters["createBasketCol"] == True

        # ... and finally create the cake

        # define folders and make target and set it
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        target = IliTarget(
            "freddys",
            maindir,
            subdir,
            None,
            "mailto:freddy",
            "27-09-2022",
            "27-09-2022",
        )

        # genearate the topping files connected to the project topping
        projecttopping_id = topping.generate_files(target)

        # update metaconfig object and generate ili2db (topping) file
        topping.metaconfig.update_projecttopping_path(projecttopping_id)
        topping.metaconfig.generate_files(target)

        # generate ilidata
        ilidata = IliData()
        ilidata_path = ilidata.generate_file(self.target, self.models)

        # Check if written
        assert ilidata_path

    def test_workflow_makeit_way(self):
        # prepare target
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        target = IliTarget(
            "freddys",
            maindir,
            subdir,
            None,
            "mailto:freddy",
            "27-09-2022",
            "27-09-2022",
        )

        # prepare metaconfig
        metaconfig = MetaConfig()
        configuration = Ili2DbCommandConfiguration()
        configuration.dbfile = self.dbfile
        configuration.tool = DbIliMode.ili2gpkg
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            metaconfig.ili2db_settings.parse_parameters_from_db(db_connector)
        metaconfig.ili2db_settings.metaattr_path = testdata_path("toml/KbS_V1_5.toml")
        metaconfig.ili2db_settings.prescript_path = ""
        metaconfig.ili2db_settings.postscript_path = (
            "ilidata:postscript_from_another_repo"
        )

        # now do the automatic way
        topping = IliProjectTopping(target, self.export_settings, metaconfig)
        ilidata_path = topping.makeit(self.project)
        assert ilidata_path

    def make_project_and_export_settings(self):
        # import schema with modelbaker library
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration.ilifile = testdata_path("ilimodels/KbS_V1_5.ili")
        importer.configuration.ilimodels = "KbS_V1_5"
        dbfile = os.path.join(
            self.basetestpath,
            "tmp_kbs_v1_5_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.dbfile = dbfile
        importer.configuration.srs_code = 2056
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.configuration.stroke_arcs = False
        importer.configuration.tomlfile = testdata_path("toml/KbS_V1_5.toml")
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

        l1 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer One", "memory"
        )
        assert l1.isValid()
        l2 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Two", "memory"
        )
        assert l2.isValid()
        l3 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Three", "memory"
        )
        assert l3.isValid()
        l4 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Four", "memory"
        )
        assert l4.isValid()
        l5 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Five", "memory"
        )
        assert l5.isValid()

        qgis_project.addMapLayer(l1, False)
        qgis_project.addMapLayer(l2, False)
        qgis_project.addMapLayer(l3, False)
        qgis_project.addMapLayer(l4, False)
        qgis_project.addMapLayer(l5, False)

        biggroup = qgis_project.layerTreeRoot().addGroup("Big Group")
        biggroup.addLayer(l1)
        mediumgroup = biggroup.addGroup("Medium Group")
        mediumgroup.addLayer(l2)
        smallgroup = mediumgroup.addGroup("Small Group")
        smallgroup.addLayer(l3)
        smallgroup.addLayer(l4)
        mediumgroup.addLayer(l5)
        allofemgroup = qgis_project.layerTreeRoot().addGroup("All of em")
        node1 = allofemgroup.addLayer(l1)
        node1.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l2)
        node3 = allofemgroup.addLayer(l3)
        node3.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l4)
        allofemgroup.addLayer(l5)

        root = qgis_project.layerTreeRoot()
        layers = root.findLayers()
        assert len(layers) == 30

        export_settings = ExportSettings()
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE, None, "Layer One", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE, None, "Layer Three", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE,
            None,
            "Belasteter_Standort (Geo_Lage_Punkt)",
            True,
        )

        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Three", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Four", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Five", True
        )

        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Belasteter_Standort", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Layer Two", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Layer Three", True
        )
        qgis_project.write()
        return qgis_project, dbfile, export_settings

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
