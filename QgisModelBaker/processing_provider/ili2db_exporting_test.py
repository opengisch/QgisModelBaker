"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import datetime
from datetime import datetime
from typing import Any, Dict, Optional

from osgeo import gdal
from qgis import gui, processing
from qgis.core import (
    Qgis,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.PyQt.QtCore import QT_VERSION_STR, QCoreApplication, Qt, QTimer
from qgis.PyQt.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from QgisModelBaker.processing_provider.ili2db_algorithm import Ili2dbAlgorithm


class CustomAlgorithmDialog(gui.QgsProcessingAlgorithmDialogBase):
    def __init__(
        self,
        algorithm: QgsProcessingAlgorithm,
        parent: Optional[QWidget] = None,
        title: Optional[str] = None,
    ):
        super().__init__(
            parent,
            flags=Qt.WindowFlags(),
            mode=gui.QgsProcessingAlgorithmDialogBase.DialogMode.Single,
        )
        self.context = QgsProcessingContext()
        self.setAlgorithm(algorithm)
        self.setModal(True)
        self.setWindowTitle(title or algorithm.displayName())

        self.panel = gui.QgsPanelWidget()
        layout = self.buildDialog()
        self.panel.setLayout(layout)
        self.setMainWidget(self.panel)

        self.cancelButton().clicked.connect(self.reject)

    def buildDialog(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        self.input = QLineEdit()

        # Set up a debounced signal using QTimer
        self._update_timer = QTimer(self, singleShot=True)
        self._update_timer.timeout.connect(self._on_collection_id_ready)
        self.input.textChanged.connect(self._on_collection_id_changed)

        layout.addWidget(self.input)

        return layout

    def _on_collection_id_changed(self):
        self._update_timer.start(500)  # Debounce input

    def _on_collection_id_ready(self):
        self.pushInfo("Fetching metadata for collection ID…")

    def getParameters(self) -> Dict:
        try:
            return {"DISTANCE": float(self.input.text())}
        except ValueError:
            raise ValueError("Invalid buffer distance")

    def processingContext(self):
        return self.context

    def createFeedback(self):
        return QgsProcessingFeedback()

    def runAlgorithm(self):
        context = self.processingContext()
        feedback = self.createFeedback()
        params = self.getParameters()

        self.pushDebugInfo(f"QGIS version: {Qgis.QGIS_VERSION}")
        self.pushDebugInfo(f"QGIS code revision: {Qgis.QGIS_DEV_VERSION}")
        self.pushDebugInfo(f"Qt version: {QT_VERSION_STR}")
        self.pushDebugInfo(f"GDAL version: {gdal.VersionInfo('--version')}")
        self.pushCommandInfo(
            f"Algorithm started at: {datetime.now().isoformat(timespec='seconds')}"
        )
        self.pushCommandInfo(f"Algorithm '{self.algorithm().displayName()}' starting…")
        self.pushCommandInfo("Input parameters:")
        for k, v in params.items():
            self.pushCommandInfo(f"  {k}: {v}")

        results = processing.run(
            self.algorithm(), params, context=context, feedback=feedback
        )
        self.setResults(results)
        self.showLog()


class ExportingAlgorithm(Ili2dbAlgorithm):
    """
    This is an algorithm from Model Baker.

    It is meant for the data validation stored in a PostgreSQL database or a GeoPackage.
    """

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2db_exporter"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Export with ili2db")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "export",
            "ili2db",
            "ili2gpkg",
            "ili2pg",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr(
            "Exports data from a GeoPackage or a PostgreSQL schema with ili2db."
        )

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr(
            "Exports data from a GeoPackage or a PostgreSQL schema with ili2db."
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        """
        self.dialog = processing.createAlgorithmDialog(
            "native:saveselectedfeatures",
        )
        self.dialog.show()
        dlg = CustomAlgorithmDialog(self)
        dlg.exec()
        """

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        return {}

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()
