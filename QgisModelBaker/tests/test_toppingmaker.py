import datetime
import os
import tempfile

from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

from QgisModelBaker.internal_libs.projecttopping.projecttopping import (
    ProjectTopping,
    Target,
)


class ProjectToppingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppingmaker_test_path = os.path.join(cls.basetestpath, "toppingmaker")

    def test_path_resolver(self):

        # load QGIS project into structure
        projecttopping = ProjectTopping()
        project = self._make_project()
        projecttopping.parse_project(project)

        # create target with path resolver
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = Target("freddys", maindir, subdir, [], ilidata_path_resolver)

        projecttopping.generate_files(target)

        # there should be exported 10 layerstyle files
        # check the values of two of em
        countchecked = 0
        for toppingfileinfo in target.toppingfileinfo_list:
            assert "id" in toppingfileinfo
            assert "path" in toppingfileinfo
            assert "type" in toppingfileinfo
            assert "version" in toppingfileinfo

            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_one.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_two.qml_001":
                countchecked += 1
            if (
                toppingfileinfo["id"]
                == "freddys.layerstyle_freddys_layer_three.qml_001"
            ):
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_four.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_five.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_one.qml_002":
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_two.qml_002":
                countchecked += 1
            if (
                toppingfileinfo["id"]
                == "freddys.layerstyle_freddys_layer_three.qml_002"
            ):
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_four.qml_002":
                countchecked += 1
            if toppingfileinfo["id"] == "freddys.layerstyle_freddys_layer_five.qml_002":
                countchecked += 1

        assert countchecked == 10

    def test_direct_library(self):
        """
        from QgisModelBaker.internal_libs.toppingmaker.toppingmaker import (
            MetaConfigInfo,
            ReferenceData,
            ToppingMaker,
        )
        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        # set target folders
        toppingmaker_target = Target("freddys", maindir, subdir, self.ilidata_path_resolver)

        # parse models with modelbaker library

        # set models of interest (parsed from backend)
        toppingmaker_models = ["RoadSimple","SomethingModel"]

        # load QGIS project into structure
        toppingmaker_projecttopping = ProjectTopping()
        toppingmaker_projecttopping.parse_project(self._make_project())

        # here we need to create a model and pass to it toppingmaker_projecttopping
        # on changing settings, they need to be back in toppingmaker_projecttopping, would this be possible?
        # otherwise we do toppingmaker_projecttopping = projecttopping_model.toppingmaker_projecttopping

        toppingmaker_referencedata = ToppingFile(["/home/dave/localthing.xml", "ilidata:2314142342"])

        # parse ili2db settings from db
        settings = {"smart2inheritance":True}
        toppingmaker_ili2dbsettings = Ili2DbSettings(settings)

        # provide the user the possiblity to select tomlfile, sqlfile
        toppingmaker_tomlfile = TomlFile(["/home/dave/localtoml.toml"])

        toppingmaker_sqlprescriptfile = SQLPreFile(["/home/dave/localtoml.sql"])
        topping_maker = ToppingMaker()

        topping_maker.target = projecttopping.
        topping_maker.considered_models = ["RoadSimpple", "Something"]

        # could be topping_maker.parse_project(self._make_project())

        project_topping.parse_project(self._make_project())
        topping_maker.projecttopping = projecttopping

        # topping_maker.projecttopping edits...

        topping_maker.reference_data = toppingmaker.ReferenceData(["/home/dave/localthing.xml", "ilidata:2314142342"])

        topping_maker.metaconfig_info.load_ili2db_settings(db_connector)

        reference_data_list = topping_maker.reference_data.generate_files(target)
        topping_maker.projecttopping.generate_files(target)
        """

    def _make_project(self):
        project = QgsProject()
        project.removeAllMapLayers()

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

        project.addMapLayer(l1, False)
        project.addMapLayer(l2, False)
        project.addMapLayer(l3, False)
        project.addMapLayer(l4, False)
        project.addMapLayer(l5, False)

        biggroup = project.layerTreeRoot().addGroup("Big Group")
        biggroup.addLayer(l1)
        mediumgroup = biggroup.addGroup("Medium Group")
        mediumgroup.addLayer(l2)
        smallgroup = mediumgroup.addGroup("Small Group")
        smallgroup.addLayer(l3)
        smallgroup.addLayer(l4)
        mediumgroup.addLayer(l5)
        allofemgroup = project.layerTreeRoot().addGroup("All of em")
        node1 = allofemgroup.addLayer(l1)
        node1.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l2)
        node3 = allofemgroup.addLayer(l3)
        node3.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l4)
        allofemgroup.addLayer(l5)

        return project


def ilidata_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)

    # can I access here self (member) variables from the Target?
    id = unique_id_in_target_scope(target, f"{target.projectname}.{type}_{name}_001")
    path = os.path.join(relative_filedir_path, name)
    type = type
    version = datetime.datetime.now().strftime("%Y-%m-%d")
    toppingfile = {"id": id, "path": path, "type": type, "version": version}
    # can I access here self (member) variables from the Target?
    target.toppingfileinfo_list.append(toppingfile)
    return path


def unique_id_in_target_scope(target: Target, id):
    for toppingfileinfo in target.toppingfileinfo_list:
        if "id" in toppingfileinfo and toppingfileinfo["id"] == id:
            iterator = int(id[-3:])
            iterator += 1
            id = f"{id[:-3]}{iterator:03}"
            return unique_id_in_target_scope(target, id)
    return id
