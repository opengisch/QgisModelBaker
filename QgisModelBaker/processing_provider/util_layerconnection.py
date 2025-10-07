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

from typing import Any, Optional

from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.processing_provider.util_algorithm import UtilAlgorithm


class LayerConnectionAlgorithm(UtilAlgorithm):
    """
    This is an algorithm from Model Baker.

    It is meant for the data validation stored in a PostgreSQL database or a GeoPackage.
    """

    # Connection
    SOURCELAYER = "SOURCELAYER"

    # Output
    PROVIDER = "PROVIDER"
    ## PG
    SERVICE = "SERVICE"
    HOST = "HOST"
    DBNAME = "DBNAME"
    PORT = "PORT"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    SCHEMA = "SCHEMA"
    # to do: SSLMODE = "SSLMODE"
    AUTHCFG = "AUTHCFG"
    ## GPKG
    DBPATH = "DBPATH"

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_util_layerconnection"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Get connection from layersource")

    def tags(self) -> list[str]:

        return ["layer", "source", "database", "modelbaker", "ili2db", "interlis"]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr("Receives connection parameters from layer source.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Receives connection parameters from layer source.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):

        sourcelayer_param = QgsProcessingParameterVectorLayer(
            self.SOURCELAYER,
            self.tr("Source layer"),
            [QgsProcessing.SourceType.TypeVector],
            self.tr("No source layer selected"),
        )
        sourcelayer_param.setHelp(
            self.tr(
                "Source layer to get database connection from. If set, it will be prefered over the other connection settings."
            )
        )
        self.addParameter(sourcelayer_param)

        self.addOutput(QgsProcessingOutputString(self.PROVIDER, self.tr("Provider")))
        self.addOutput(QgsProcessingOutputString(self.SERVICE, self.tr("Service")))
        self.addOutput(QgsProcessingOutputString(self.HOST, self.tr("Host")))
        self.addOutput(QgsProcessingOutputString(self.DBNAME, self.tr("Database Name")))
        self.addOutput(QgsProcessingOutputNumber(self.PORT, self.tr("Port Number")))
        self.addOutput(QgsProcessingOutputString(self.USERNAME, self.tr("Username")))
        self.addOutput(QgsProcessingOutputString(self.PASSWORD, self.tr("Password")))
        self.addOutput(QgsProcessingOutputString(self.SCHEMA, self.tr("Schema")))
        # to do self.addOutput(QgsProcessingOutputString(self.SSLMODE, self.tr('SSL Mode')))
        self.addOutput(
            QgsProcessingOutputString(self.AUTHCFG, self.tr("Authentication"))
        )

        self.addOutput(
            QgsProcessingOutputString(self.DBPATH, self.tr("Databasefile Path"))
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        configuration = Ili2DbCommandConfiguration()

        source_layer = self.parameterAsVectorLayer(
            parameters, self.SOURCELAYER, context
        )
        if not source_layer:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.SOURCELAYER)
            )
            return {}

        source_provider = source_layer.dataProvider()
        valid, mode = db_utils.get_configuration_from_sourceprovider(
            source_provider, configuration
        )
        if not (valid and mode):
            # error
            return {}

        if feedback.isCanceled():
            return {}

        return {
            self.PROVIDER: source_provider.name(),
            self.SERVICE: configuration.dbservice,
            self.HOST: configuration.dbhost,
            self.DBNAME: configuration.database,
            self.PORT: configuration.dbport,
            self.USERNAME: configuration.dbusr,
            self.PASSWORD: configuration.dbpwd,
            self.SCHEMA: configuration.dbschema,
            # to do self.SSLMODE: configuration.sslmode_param, this is sslMode in DataSource and an ENUM
            self.AUTHCFG: configuration.dbauthid,
            self.DBPATH: configuration.dbfile,
        }

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()
