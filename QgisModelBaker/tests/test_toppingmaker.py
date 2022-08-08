import datetime
import logging
import os
import tempfile

from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

from QgisModelBaker.internal_libs.toppingmaker.toppingmaker import (
    ProjectTopping,
    ToppingMaker,
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


class ToppingMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppingmaker_test_path = os.path.join(cls.basetestpath, "toppingmaker")

    def test_workflow_with_library(self):
        """
        To remove:
            set folders (Target)
            set [models] ➝ set models
            load project into projecttopping
            provide projecttopping (settings over model)
            edit projecttopping (settings over model)
            append [referencefiles] and [paths (with ilidata) and contextinfo] (list somewhere)
            load ili2db settings from db (MetaConfig settings somewhere)
            write [projecttoppingfile] and [toppingfiles] and [paths (with ilidata) and contextinfo]
            create ilidata.xml (from pathmapping)
        """
        # create a project of RoadsSimple with some additional layers
        project, dbfile = self._make_project()

        # start
        topping_maker = ToppingMaker()

        # page 1:
        # create target
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        topping_maker.create_target("freddys", maindir, subdir)

        # page 2:
        # let's pretend that we received the models from the parsed schemas of the project and selected RoadsSimple and something else
        # that's done over the model - all of em are checked per default
        topping_maker.load_available_models(project)

        # page 3:
        # load QGIS project into structure
        topping_maker.create_projecttopping(project)
        # let's pretend that the user made some mutations on the project
        self._make_mutations_on_projecttopping(topping_maker.project_topping)

        # page 4:
        # let's pretend that the user selected some referencedata via filebrowser and maybe repos
        codetexte_xtf = testdata_path("xtf/KbS_Codetexte_V1_5_20211015.xtf")
        topping_maker.referencedata_paths = [
            codetexte_xtf,
            "ilidata:data_from_another_repo",
        ]

        # page 5:
        # let's pretend that we received the parsed schemas of the project and selected one specific. So we got the configuration.
        # we append a metaattr file (toml), and a postscript we select from a repo

        configuration = Ili2DbCommandConfiguration()
        configuration.dbfile = dbfile
        metaattr_filepath = testdata_path("toml/KbS_V1_5.toml")
        prescript_filepath = ""
        postscript_filepath = "ilidata:postscript_from_another_repo"
        topping_maker.create_ili2dbsettings(
            configuration, metaattr_filepath, prescript_filepath, postscript_filepath
        )

        # page 6:
        # generate everything
        # - toppingfiles and projecttopping
        # - metaconfig file
        # - ilidata.xml
        topping_maker.generate()

    def _make_mutations_on_projecttopping(self, projecttopping: ProjectTopping):
        for item in projecttopping.layertree.items:
            if item.name == "Belasteter_Standort (Geo_Lage_Punkt)":
                item.properties.checked = False
                item.properties.use_source = False
            if item.name == "Belasteter_Standort":
                item.properties.use_definitionfile = True
            if item.name == "tables":
                item.properties.expanded = False

    def _make_project(self):
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

        return qgis_project, dbfile

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
