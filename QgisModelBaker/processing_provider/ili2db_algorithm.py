from qgis.core import QgsProcessingAlgorithm


class Ili2dbAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def icon(self):
        return QgsProcessingAlgorithm.icon(self)
