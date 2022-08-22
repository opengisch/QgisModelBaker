import datetime
import logging
import os
import tempfile

from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

from QgisModelBaker.internal_libs.ilitoppingmaker import (
    ExportSettings,
    IliProjectTopping,
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


class IliProjectToppingTest(unittest.TestCase):
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

    def test_workflow_with_library(self):
        # create topping maker and with it topping.export_settings
        topping = IliProjectTopping(export_settings=self.export_settings)

        # define folders and make target
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        topping.create_target("freddys", maindir, subdir)

        # Check if models are loaded.
        # let's pretend that we received the models from the parsed schemas of the project and selected Kbs_V1_5
        topping.load_available_models(self.project)
        assert topping.models == ["KbS_V1_5"]

        # Check if the export_settings are applied properly when created the projecttopping
        # load QGIS project into structure
        countchecked = 0
        topping.create_projecttopping(self.project)
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

        # let's pretend that the user selected some referencedata via filebrowser and maybe repos
        codetexte_xtf = testdata_path("xtf/KbS_Codetexte_V1_5_20211015.xtf")
        topping.referencedata_paths = [
            codetexte_xtf,
            "ilidata:data_from_another_repo",
        ]

        # let's pretend that we received the parsed schemas of the project and selected one specific. So we got the configuration.
        # we append a metaattr file (toml), and a postscript we select from a repo
        configuration = Ili2DbCommandConfiguration()
        configuration.dbfile = self.dbfile

        topping.metaattr_filepath = testdata_path("toml/KbS_V1_5.toml")
        topping.prescript_filepath = ""
        topping.postscript_filepath = "ilidata:postscript_from_another_repo"
        topping.create_ili2dbsettings(configuration)

        # Check if the settings are loaded from the database
        assert topping.metaconig.ili2dbsection["defaultSrsCode"] == 2056
        assert topping.metaconig.ili2dbsection["smart2Inheritance"] == True
        assert topping.metaconig.ili2dbsection["strokeArcs"] == False
        assert topping.metaconig.ili2dbsection["importTid"] == True
        assert topping.metaconig.ili2dbsection["createBasketCol"] == True

        # ... and finally create the cake
        # generate toppingfiles of ProjectTopping
        projecttopping_id = topping.generate_projecttoppingfiles()

        # generate toppingfiles of the reference data
        referencedata_ids = ",".join(
            [
                self.generate_toppingfile_link(
                    self.topping, IliProjectTopping.REFERENCEDATA_TYPE, path
                )
                for path in topping.referencedata_paths
            ]
        )
        assert referencedata_ids == []

        # update MetaConfig with toppingfile ids
        topping.metaconfig.update_configuration_settings(
            "qgis.modelbaker.projecttopping", projecttopping_id
        )
        topping.metaconfig.update_configuration_settings(
            "ch.interlis.referenceData", referencedata_ids
        )
        assert (
            topping.metaconfig.configuration_section["qgis.modelbaker.projecttopping"]
            == "name"
        )
        assert (
            topping.metaconfig.configuration_section["ch.interlis.referenceData"]
            == "name"
        )

        # generate toppingfiles used for ili2db
        if topping.metaattr_filepath:
            topping.metaconfig.update_ili2db_settings(
                "iliMetaAttrs",
                topping.generate_toppingfile_link(
                    topping.target,
                    IliProjectTopping.METAATTR_TYPE,
                    topping.metaattr_filepath,
                ),
            )
        if topping.prescript_filepath:
            topping.metaconfig.update_ili2db_settings(
                "preScript",
                topping.generate_toppingfile_link(
                    topping.target,
                    IliProjectTopping.SQLSCRIPT_TYPE,
                    topping.prescript_filepath,
                ),
            )
        if topping.postscript_filepath:
            topping.metaconfig.update_ili2db_settings(
                "postScript",
                topping.generate_toppingfile_link(
                    topping.target,
                    IliProjectTopping.SQLSCRIPT_TYPE,
                    topping.postscript_filepath,
                ),
            )

        assert topping.metaconfig.ili2db_section["iliMetaAttrs"] == "name"
        assert topping.metaconfig.ili2db_section["preScript"] == "name"
        assert topping.metaconfig.ili2db_section["postScript"] == "name"

        # generate metaconfig (topping) file
        topping.metaconfig.generate_file(topping.target)

        # Check if written

        # generate ilidata.xml
        topping.generate_ilidataxml(topping.target)

        # Check if written

    def test_workflow_bakedycakedy_way(self):
        configuration = Ili2DbCommandConfiguration()
        configuration.dbfile = self.dbfile
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        # now do the automatic way
        topping = IliProjectTopping("freddys", maindir, subdir, self.export_settings)
        topping.bakedycakedy(self.project, configuration)

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

        return qgis_project, dbfile, export_settings

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
