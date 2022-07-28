import os
import pathlib
import tempfile

import yaml
from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

import QgisModelBaker.internal_libs.projecttopping.projecttopping as toppingmaker

test_path = pathlib.Path(__file__).parent.absolute()


class ToppingMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppingmaker_test_path = os.path.join(test_path, "toppingmaker")

    def test_target(self):
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        filedirs = ["projecttopping", "layerstyle", "layerdefinition", "andanotherone"]
        target = toppingmaker.Target("freddys", maindir, subdir, filedirs)
        target.makedirs()
        count = 0
        for filedir in filedirs:
            assert os.path.isdir(filedir)
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

        projecttopping = toppingmaker.ProjectTopping()
        projecttopping.parse_project(project)

        checked_groups = []
        for item in projecttopping.layertree.items:
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

        projecttopping = toppingmaker.ProjectTopping()
        projecttopping.parse_project(project)

        checked_groups = []
        for item in projecttopping.layertree.items:
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

        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = toppingmaker.Target("freddys", maindir, subdir)

        projecttopping_path = projecttopping.generate_files(target)

        foundAllofEm = False
        foundLayerOne = False
        foundLayerTwo = False

        with open(projecttopping_path, "r") as yamlfile:
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
                            assert childnode["Layer One"]["checked"]
                        if "Layer Two" in childnode:
                            foundLayerTwo = True
                            assert "checked" in childnode["Layer Two"]
                            assert not childnode["Layer Two"]["checked"]
        assert foundAllofEm
        assert foundLayerOne
        assert foundLayerTwo

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


"""
from QgisModelBaker.internal_libs.projecttopping.projecttopping import ProjectTopping, Target

projtop = ProjectTopping()
projtop.load_project(QgsProject.instance())

target = Target("daves_test_topping", "/home/cheapdave/dev/", "topping_test")

projtop.generate_files(target)
"""
