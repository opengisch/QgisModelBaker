import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .ili2db_exporting import ExportingAlgorithm
from .ili2db_validating import ValidatingPGAlgorithm
from .util_layerconnection import LayerConnectionAlgorithm


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(ValidatingPGAlgorithm())
        self.addAlgorithm(ExportingAlgorithm())
        self.addAlgorithm(LayerConnectionAlgorithm())

    def id(self) -> str:
        return "modelbaker"

    def name(self) -> str:
        return self.tr("Model Baker")

    def icon(self) -> QIcon:
        return QIcon(
            os.path.join(os.path.dirname(__file__), "../images/QgisModelBaker-icon.svg")
        )
