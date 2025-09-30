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

import os
import re
from datetime import datetime
from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication, QObject, QStandardPaths

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper import ilivalidator
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.processing_provider.ili2db_algorithm import (
    Ili2gpkgAlgorithm,
    Ili2pgAlgorithm,
)


class Validator(QObject):

    # Filters
    FILTERMODE = "FILTERMODE"  # none, models, baskets or datasets
    FILTER = "FILTER"  # model, basket or dataset names

    # Settings
    EXPORTMODEL = "EXPORTMODEL"
    SKIPGEOMETRYERRORS = "SKIPGEOMETRYERRORS"
    VERBOSE = "VERBOSE"
    VALIDATORCONFIGFILEPATH = "VALIDATORCONFIGFILEPATH"

    # Result
    ISVALID = "ISVALID"
    XTFLOGPATH = "XTFLOGPATH"

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def validation_input_params(self):
        params = []
        filtermode_param = QgsProcessingParameterEnum(
            self.FILTERMODE,
            self.tr("Filter Mode"),
            ["Models", "Baskets", "Datasets"],
            optional=True,
            usesStaticStrings=True,
        )
        filtermode_param.setHelp(
            self.tr(
                "Whether data should be filtered according to the models, baskets or datasets in which they are stored."
            )
        )
        params.append(filtermode_param)

        filter_param = QgsProcessingParameterString(
            self.FILTER, self.tr("Filter (semicolon-separated)"), optional=True
        )
        filter_param.setHelp(
            self.tr(
                "A semicolon-separated list of the relevant models, baskets or datasets"
            )
        )
        params.append(filter_param)

        exportmodel_param = QgsProcessingParameterString(
            self.EXPORTMODEL,
            self.tr("Export Models"),
            optional=True,
        )
        exportmodel_param.setHelp(
            self.tr(
                """<html><head/><body>
            <p>If your data is in the format of the cantonal model, but you want to validate it in the format of the national model you need to define this here.</p>
            <p>Usually, this is one single model. However, it is also possible to pass multiple models, which makes sense if there are multiple base models in the schema you want to validate.</p>
            </body></html>"""
            )
        )
        params.append(exportmodel_param)

        skipgeom_param = QgsProcessingParameterBoolean(
            self.SKIPGEOMETRYERRORS,
            self.tr("Skip Geometry Errors"),
            defaultValue=False,
        )
        skipgeom_param.setHelp(
            self.tr(
                "Ignores geometry errors (--skipGeometryErrors) and AREA topology validation (--disableAreaValidation)"
            )
        )
        params.append(skipgeom_param)

        verbose_param = QgsProcessingParameterBoolean(
            self.VERBOSE,
            self.tr("Activate Verbose Mode"),
            defaultValue=False,
        )
        verbose_param.setHelp(
            self.tr("Verbose Mode provides you more information in the log output.")
        )
        params.append(verbose_param)

        validatorconfig_param = QgsProcessingParameterFile(
            self.VALIDATORCONFIGFILEPATH,
            self.tr("Validator config file"),
            optional=True,
        )
        validatorconfig_param.setHelp(
            self.tr("You can add a validator config file to control the validation.")
        )
        params.append(validatorconfig_param)

        return params

    def validation_output_params(self):
        params = []

        params.append(QgsProcessingOutputBoolean(self.ISVALID, self.tr("is valid")))
        params.append(QgsProcessingOutputString(self.XTFLOGPATH, self.tr("xtflog")))

        return params

    def initParameters(self):
        for connection_input_param in self.parent.connection_input_params():
            self.parent.addParameter(connection_input_param)
        for connection_output_param in self.parent.connection_output_params():
            self.parent.addOutput(connection_output_param)

        for validation_input_param in self.validation_input_params():
            self.parent.addParameter(validation_input_param)
        for validation_output_param in self.validation_output_params():
            self.parent.addOutput(validation_output_param)

    def run(self, configuration, feedback):
        output_file_name = (
            "modelbakerili2dbvalidatingalgorithm_xtflog_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.now()
            )
        )
        configuration.xtflog = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            output_file_name,
        )
        configuration.with_exporttid = self._get_tid_handling(configuration)

        # run
        validator = ilivalidator.Validator(self)
        validator.tool = configuration.tool

        # to do superuser finden? und auch dpparams?
        validator.configuration = configuration
        validator.stdout.connect(feedback.pushInfo)
        validator.stderr.connect(feedback.pushInfo)

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

    def get_configuration_from_input(self, parameters, context, configuration):

        # get database settings form the parent
        if not self.parent.get_db_configuration_from_input(
            parameters, context, configuration
        ):
            return False

        filtermode = self.parent.parameterAsString(parameters, self.FILTERMODE, context)
        filters = self.parent.parameterAsString(parameters, self.FILTER, context)
        if filtermode == "Models" and filters:
            configuration.ilimodels = filters
        elif filtermode == "Datasets" and filters:
            configuration.dataset = filters
        elif filtermode == "Baskets" and filters:
            configuration.baskets = filters
        else:
            configuration.ilimodels = ";".join(self._get_model_names(configuration))

        exportmodels = self.parent.parameterAsString(
            parameters, self.EXPORTMODEL, context
        )
        if exportmodels:
            configuration.iliexportmodels = exportmodels

        configuration.skip_geometry_errors = self.parent.parameterAsBool(
            parameters, self.SKIPGEOMETRYERRORS, context
        )

        configuration.verbose = self.parent.parameterAsBool(
            parameters, self.VERBOSE, context
        )

        validatorconfigfile = self.parent.parameterAsFile(
            parameters, self.VALIDATORCONFIGFILEPATH, context
        )

        if validatorconfigfile:
            configuration.valid_config = validatorconfigfile

        return True

    def _get_tid_handling(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.get_tid_handling()
        return False

    def _get_model_names(self, configuration):
        modelnames = []

        db_connector = db_utils.get_db_connector(configuration)
        if (
            db_connector
            and db_connector.db_or_schema_exists()
            and db_connector.metadata_exists()
        ):
            db_models = db_connector.get_models()
            regex = re.compile(r"(?:\{[^\}]*\}|\s)")
            for db_model in db_models:
                for modelname in regex.split(db_model["modelname"]):
                    name = modelname.strip()
                    if name and name not in modelnames:
                        modelnames.append(name)
        return modelnames

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)


class ValidatingPGAlgorithm(Ili2pgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data validation stored in a PostgreSQL database.
    """

    def __init__(self):
        super().__init__()

        # initialize the validator with self as parent
        self.validator = Validator(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2pg_validator"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Validate with ili2pg (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "validate",
            "validation",
            "ili2db",
            "ili2pg",
            "Postgres",
            "PostGIS",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr("Validates data in a PostgreSQL schema with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Validates data in a PostgreSQL schema with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.validator.initParameters()

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
        configuration.tool = DbIliMode.pg

        output_map = {}
        if not self.validator.get_configuration_from_input(
            parameters, context, configuration
        ):
            feedback.pushWarning(
                self.tr("Invalid input parameters. Cannot start validation.")
            )
        else:
            output_map.update(self.validator.run(configuration, feedback))
        output_map.update(self.get_output_from_db_configuration(configuration))

        return output_map


class ValidatingGPKGAlgorithm(Ili2gpkgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data validation stored in a GeoPackage file.
    """

    def __init__(self):
        super().__init__()

        # initialize the validator with self as parent
        self.validator = Validator(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2gpkg_validator"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Validate with ili2gpkg (GeoPackage)")

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
            "GeoPackage",
            "GPKG",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr("Validates data in a GeoPackage file with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Validates data in a GeoPackage file with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.validator.initParameters()

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
        configuration.tool = DbIliMode.gpkg

        output_map = {}
        if not self.validator.get_configuration_from_input(
            parameters, context, configuration
        ):
            feedback.pushWarning(
                self.tr("Invalid input parameters. Cannot start validation.")
            )
        else:
            output_map.update(self.validator.run(configuration, feedback))
        output_map.update(self.get_output_from_db_configuration(configuration))

        return output_map
