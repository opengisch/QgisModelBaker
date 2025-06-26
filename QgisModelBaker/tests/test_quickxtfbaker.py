"""
/***************************************************************************
    begin                :    16/06/2025
    git sha              :    :%H$
    copyright            :    (C) 2025 by Dave Signer
    email                :    david@opengis.ch
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

from qgis.testing import mocked, start_app, unittest

from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration
from QgisModelBaker.tests.utils import testdata_path
from QgisModelBaker.utils.tools import QuickVisualizer

start_app()


class TestQuickVisualizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.iface = mocked.get_iface()
        cls.ili2db_configuration = BaseConfiguration()
        cls.ili2db_configuration.custom_model_directories_enabled = True
        cls.ili2db_configuration.custom_model_directories = testdata_path("ilimodels")

    def show_logs_folder(cls):
        # dummy function available in parent
        pass

    def test_xtf_drop_24_only(self):
        """
        Test with two xtf's of INTERLIS 2.4
        """

        dropped_files = [testdata_path("xtf/24_waldreservate_V2_0.xtf")]

        quick_visualizer = QuickVisualizer(self)
        suc_files, failed_files = quick_visualizer.handle_dropped_files(dropped_files)
        assert len(suc_files) == 1

    def test_xtf_drop_23_only(self):
        """
        Test with two xtf's of INTERLIS 2.3
        """

        dropped_files = [testdata_path("xtf/23_roads_simple.xtf")]

        quick_visualizer = QuickVisualizer(self)
        suc_files, failed_files = quick_visualizer.handle_dropped_files(dropped_files)
        assert len(suc_files) == 1

    def test_xtf_drop_1_only(self):
        """
        Test with an ITF
        """

        dropped_files = [testdata_path("xtf/1_beispiel.itf")]

        quick_visualizer = QuickVisualizer(self)
        suc_files, failed_files = quick_visualizer.handle_dropped_files(dropped_files)
        assert len(suc_files) == 1

    def test_xtf_drop(self):
        """
        Test with ITF and one xtf of INTERLIS 2.3 and one xtf of INTERLIS 2.4
        And pass ili-files that should be ignored
        """

        dropped_files = [
            testdata_path("xtf/24_waldreservate_V2_0.xtf"),
            testdata_path("xtf/23_roads_simple.xtf"),
            testdata_path("xtf/Beispiel1.ili"),
            testdata_path("xtf/1_beispiel.itf"),
        ]

        quick_visualizer = QuickVisualizer(self)
        suc_files, failed_files = quick_visualizer.handle_dropped_files(dropped_files)
        assert len(suc_files) == 3

    def test_xtf_with_fallback(self):
        """
        Test with XTF that is not in repo.
        Default repo would parse XTF-dir, but here we have a custom repo defined, what means it doesn't parse it.
        But we have a fallback, adding the '%XTF_DIR' to the repo list.
        """
        dropped_files = [testdata_path("xtf/23_roads_simple_2.xtf")]

        quick_visualizer = QuickVisualizer(self)
        suc_files, failed_files = quick_visualizer.handle_dropped_files(dropped_files)
        assert len(suc_files) == 1
