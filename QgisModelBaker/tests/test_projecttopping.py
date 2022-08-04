import logging
import os
import tempfile

import yaml
from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

from QgisModelBaker.internal_libs.projecttopping.projecttopping import (
    ProjectTopping,
    Target,
)
from QgisModelBaker.tests.utils import ilidata_path_resolver


class ProjectToppingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.projecttopping_test_path = os.path.join(cls.basetestpath, "projecttopping")

    def test_target(self):
        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        filedirs = ["projecttopping", "layerstyle", "layerdefinition", "andanotherone"]
        target = Target("freddys", maindir, subdir, filedirs)
        target.create_dirs()
        count = 0
        for filedir in filedirs:
            path, _ = target.filedir_path(filedir)
            assert os.path.isdir(path)
            count += 1
        assert count == 4

    def test_parse_project(self):
        """
        "Big Group":
            group: True
            child-nodes:
                - "Layer One":
                    checked: True
                - "Medium Group":
                    group: True
                    child-nodes:
                        - "Layer Two":
                        - "Small Group:
                            - "Layer Three":
                            - "Layer Four":
                        - "Layer Five":
        "All of em":
            group: True
            child-nodes:
                - "Layer One":
                    checked: False
                - "Layer Two":
                - "Layer Three":
                    checked: False
                - "Layer Four":
                - "Layer Five":
        """
        project = self._make_project()
        layers = project.layerTreeRoot().findLayers()
        self.assertEqual(len(layers), 10)

        project_topping = ProjectTopping()
        project_topping.parse_project(project)

        checked_groups = []
        for item in project_topping.layertree.items:
            if item.name == "Big Group":
                assert len(item.items) == 2
                checked_groups.append("Big Group")
                for item in item.items:
                    if item.name == "Medium Group":
                        assert len(item.items) == 3
                        checked_groups.append("Medium Group")
                        for item in item.items:
                            if item.name == "Small Group":
                                assert len(item.items) == 2
                                checked_groups.append("Small Group")
        assert checked_groups == ["Big Group", "Medium Group", "Small Group"]

    def test_generate_files(self):
        project = self._make_project()
        layers = project.layerTreeRoot().findLayers()
        self.assertEqual(len(layers), 10)

        project_topping = ProjectTopping()
        project_topping.parse_project(project)

        checked_groups = []
        for item in project_topping.layertree.items:
            if item.name == "Big Group":
                assert len(item.items) == 2
                checked_groups.append("Big Group")
                for item in item.items:
                    if item.name == "Medium Group":
                        assert len(item.items) == 3
                        checked_groups.append("Medium Group")
                        for item in item.items:
                            if item.name == "Small Group":
                                assert len(item.items) == 2
                                checked_groups.append("Small Group")
        assert checked_groups == ["Big Group", "Medium Group", "Small Group"]

        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = Target("freddys", maindir, subdir)

        projecttopping_file_path = os.path.join(
            target.main_dir, project_topping.generate_files(target)
        )

        foundAllofEm = False
        foundLayerOne = False
        foundLayerTwo = False

        with open(projecttopping_file_path, "r") as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            assert projecttopping_data["layertree"]
            for node in projecttopping_data["layertree"]:
                if "All of em" in node:
                    foundAllofEm = True
                    assert "child-nodes" in node["All of em"]
                    for childnode in node["All of em"]["child-nodes"]:
                        if "Layer One" in childnode:
                            foundLayerOne = True
                            assert "checked" in childnode["Layer One"]
                            assert not childnode["Layer One"]["checked"]
                        if "Layer Two" in childnode:
                            foundLayerTwo = True
                            assert "checked" in childnode["Layer Two"]
                            assert childnode["Layer Two"]["checked"]
        assert foundAllofEm
        assert foundLayerOne
        assert foundLayerTwo

    def test_custom_path_resolver(self):

        # load QGIS project into structure
        project_topping = ProjectTopping()
        project = self._make_project()
        project_topping.parse_project(project)

        # create target with path resolver
        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = Target("freddys", maindir, subdir, [], ilidata_path_resolver)

        project_topping.generate_files(target)

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

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
