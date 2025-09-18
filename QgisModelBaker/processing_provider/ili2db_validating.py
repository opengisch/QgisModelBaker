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
import os
from datetime import datetime
from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputString,
    QgsProcessingParameterEnum,
    QgsProject,
)
from qgis.PyQt.QtCore import QCoreApplication, QStandardPaths

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper import ilivalidator
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.processing_provider.ili2db_algorithm import Ili2dbAlgorithm


class ValidatingAlgorithm(Ili2dbAlgorithm):
    """
    This is an algorithm from Model Baker.

    It is meant for the data validation stored in a PostgreSQL database or a GeoPackage.
    """

    # Filters
    FILTERTYPE = "FILTERTYPE"  # none, models, baskets or datasets
    FILTERS = "FILTERS"  # model, basket or dataset names

    # Settings
    EXPORTMODEL = "EXPORTMODEL"
    SKIPGEOMETRYERRORS = "SKIPGEOMETRYERRORS"
    VERBOSE = "VERBOSE"
    VALIDATORCONFIGFILEPATH = "VALIDATORCONFIGFILEPATH"

    # Result
    ISVALID = "ISVALID"
    XTFLOGPATH = "XTFLOGPATH"

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2db_validator"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Validate with ili2db")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "validate",
            "validation",
            "ili2db",
            "ili2gpkg",
            "ili2pg",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr(
            "Validates data in a GeoPackage or a PostgreSQL schema with ili2db."
        )

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr(
            "Validates data in a GeoPackage or a PostgreSQL schema with ili2db."
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):

        self.addConnectionParams()

        filtertype_param = QgsProcessingParameterEnum(
            self.FILTERTYPE,
            self.tr("Filter"),
            ["Models", "Baskets", "Datasets"],
            False,
            "Models",
        )
        filtertype_param.setHelp(self.tr("todo"))
        self.addParameter(filtertype_param)

        self.addOutput(QgsProcessingOutputBoolean(self.ISVALID, self.tr("is valid")))

        self.addOutput(QgsProcessingOutputString(self.XTFLOGPATH))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        configuration = ValidateConfiguration()

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

        output_file_name = (
            "modelbakerili2dbvalidatingalgorithm_xtflog_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            )
        )
        configuration.xtflog = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            output_file_name,
        )
        configuration.with_exporttid = self._get_tid_handling(configuration)
        configuration.ilimodels = "KbS_V1_5"

        # run
        validator = ilivalidator.Validator()
        validator.tool = configuration.tool  # superuser finden? und auch dbparams?
        validator.configuration = configuration
        validator.stdout.connect(feedback.pushInfo)
        validator.stderr.connect(feedback.pushWarning)

        if feedback.isCanceled():
            return {}

        try:
            feedback.pushInfo(f"Run: {validator.command(True)}")
            result = validator.run(None)
            if result == ilivalidator.Validator.SUCCESS:
                feedback.pushInfo(self.tr("... validation succeeded"))
            else:
                feedback.pushWarning(self.tr("... validation failed"))
            isvalid = result
        except JavaNotFoundError as e:
            raise QgsProcessingException(
                self.tr("Java not found error:").format(e.error_string)
            )

        return {self.ISVALID: isvalid, self.XTFLOGPATH: configuration.xtflog}

    def _get_tid_handling(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.get_tid_handling()
        return False

    def _get_models(self, name):
        configuration = ValidateConfiguration()
        source_layer_list = QgsProject.instance().mapLayersByName(name)
        if not source_layer_list:
            return []
        source_provider = source_layer_list[0].dataProvider()
        valid, mode = db_utils.get_configuration_from_sourceprovider(
            source_provider, configuration
        )
        if not (valid and mode):
            return []
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.get_models()
        return []

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()
