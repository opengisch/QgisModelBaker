import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from QgisModelBaker.libs.modelbaker.processing.ili2db_exporting import (
    ExportingGPKGAlgorithm,
    ExportingPGAlgorithm,
)
from QgisModelBaker.libs.modelbaker.processing.ili2db_importing import (
    ImportingGPKGAlgorithm,
    ImportingPGAlgorithm,
)
from QgisModelBaker.libs.modelbaker.processing.ili2db_validating import (
    ValidatingGPKGAlgorithm,
    ValidatingPGAlgorithm,
)


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(ImportingPGAlgorithm())
        self.addAlgorithm(ImportingGPKGAlgorithm())
        self.addAlgorithm(ExportingPGAlgorithm())
        self.addAlgorithm(ExportingGPKGAlgorithm())
        self.addAlgorithm(ValidatingPGAlgorithm())
        self.addAlgorithm(ValidatingGPKGAlgorithm())

    def id(self) -> str:
        return "modelbaker"

    def name(self) -> str:
        return self.tr("Model Baker")

    def icon(self) -> QIcon:
        return QIcon(
            os.path.join(os.path.dirname(__file__), "../images/QgisModelBaker-icon.svg")
        )
