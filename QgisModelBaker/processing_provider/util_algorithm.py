import os

from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtGui import QIcon


class UtilAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("Utils")

    def groupId(self):
        return "utils"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "../images/interlis.png"))
