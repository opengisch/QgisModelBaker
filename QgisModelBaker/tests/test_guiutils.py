"""
/***************************************************************************
    begin                :    13/06/2025
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
import pathlib

from qgis.testing import start_app, unittest

from QgisModelBaker.tests.utils import testdata_path
from QgisModelBaker.utils.gui_utils import ImportModelsModel, SourceModel

start_app()


class TestGuiUtils(unittest.TestCase):
    def test_xtf_modelparse(self):
        """Test if the models are successfully detected from an xtf (or itf).
        Consider the different structure of itf (INTERLIS1) and xtf for INTERLIS2.3 and xtf for INTERLIS2.4.
        Consider ignored Models
        """

        transferfiles = [
            testdata_path("xtf/1_beispiel.itf"),
            testdata_path("xtf/23_ciaf_ladm.xtf"),
            testdata_path("xtf/23_roads_simple.xtf"),
            testdata_path("xtf/24_waldreservate_V2_0.xtf"),
            testdata_path("xtf/24_waldreservate_catalogues_V2_0.xml"),
        ]

        source_model = SourceModel()

        for file in transferfiles:
            source_model.add_source(
                pathlib.Path(file).name,
                pathlib.Path(file).suffix[1:],
                file,
                "unit tests",
            )

        import_models_model = ImportModelsModel()

        import_models_model.refresh_model(source_model)

        assert set(import_models_model.checked_models()) == {
            "Beispiel1",
            "CIAF_LADM",
            "Catastro_COL_ES_V2_1_6",
            "ISO19107_V1_MAGNABOG",
            "RoadsSimple",
            "Waldreservate_V2_0",
        }

    def test_model_summarize(self):
        """Test if the detected models are properly summarized, so the same model don't appear multiple times in the importmodels model."""

        transferfiles = [
            testdata_path("xtf/23_ciaf_ladm.xtf"),
            testdata_path("xtf/23_roads_simple.xtf"),
            testdata_path("xtf/24_waldreservate_V2_0.xtf"),
            testdata_path("xtf/24_waldreservate_catalogues_V2_0.xml"),
        ]

        ilifiles = [
            testdata_path("ilimodels/RoadsSimple.ili"),
            testdata_path("ilimodels/Beispiel1.ili"),
            testdata_path("ilimodels/Waldreservate_V2_0.ili"),
        ]

        source_model = SourceModel()

        for file in transferfiles:
            source_model.add_source(
                pathlib.Path(file).name,
                pathlib.Path(file).suffix[1:],
                file,
                "unit tests",
            )

        for file in ilifiles:
            source_model.add_source(
                pathlib.Path(file).name,
                pathlib.Path(file).suffix[1:],
                file,
                "unit tests",
            )

        import_models_model = ImportModelsModel()

        import_models_model.refresh_model(source_model)

        assert set(import_models_model.checked_models()) == {
            "Beispiel1",  # from ili only
            "CIAF_LADM",  # from xtf only
            "Catastro_COL_ES_V2_1_6",  # from xtf only
            "ISO19107_V1_MAGNABOG",  # from xtf only
            "RoadsSimple",  # from ili and from xtf
            "Waldreservate_V2_0",  # from ili and from xtf
        }
