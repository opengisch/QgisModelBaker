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

import re
from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication, QObject

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper import iliexporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import ExportConfiguration
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.libs.modelbaker.utils.globals import MODELS_BLACKLIST
from QgisModelBaker.processing_provider.ili2db_algorithm import (
    Ili2gpkgAlgorithm,
    Ili2pgAlgorithm,
)


class ProcessExporter(QObject):

    # Filters
    FILTERMODE = "FILTERMODE"  # none, models, baskets or datasets
    FILTER = "FILTER"  # model, basket or dataset names

    # Settings
    EXPORTMODEL = "EXPORTMODEL"
    DISABLEVALIDATION = "DISABLEVALIDATION"

    XTFFILEPATH = "XTFFILEPATH"

    # Result
    ISVALID = "ISVALID"

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def export_input_params(self):
        params = []

        xtffile_param = QgsProcessingParameterFileDestination(
            self.XTFFILEPATH,
            self.tr("Target Transferfile (XTF)"),
            self.tr("INTERLIS Transferfile (*.xtf *.xml)"),
            defaultValue=None,
            optional=False,
        )
        xtffile_param.setHelp(
            self.tr("The XTF File where the data should be exported to.")
        )
        params.append(xtffile_param)

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
            <p>If your data is in the format of the cantonal model, but you want to export it in the format of the national model you need to define this here.</p>
            <p>Usually, this is one single model. However, it is also possible to pass multiple models, which makes sense if there are multiple base models in the schema you want to export.</p>
            </body></html>"""
            )
        )
        params.append(exportmodel_param)

        disablevalidation_param = QgsProcessingParameterBoolean(
            self.DISABLEVALIDATION,
            self.tr("Disable validaton of the data"),
            defaultValue=False,
        )
        disablevalidation_param.setHelp(
            self.tr(
                "Ignores geometry errors (--skipGeometryErrors) and constraint validation (--disableValidation)"
            )
        )
        params.append(disablevalidation_param)

        return params

    def export_output_params(self):
        params = []

        params.append(
            QgsProcessingOutputBoolean(self.ISVALID, self.tr("Export Result"))
        )
        params.append(
            QgsProcessingOutputFile(self.XTFFILEPATH, self.tr("Transferfile Path"))
        )

        return params

    def initParameters(self):
        for connection_input_param in self.parent.connection_input_params():
            self.parent.addParameter(connection_input_param)
        for connection_output_param in self.parent.connection_output_params():
            self.parent.addOutput(connection_output_param)

        for export_input_param in self.export_input_params():
            self.parent.addParameter(export_input_param)
        for export_output_param in self.export_output_params():
            self.parent.addOutput(export_output_param)

    def run(self, configuration, feedback):
        # run
        exporter = iliexporter.Exporter(self)
        exporter.tool = configuration.tool

        # to do superuser finden? und auch dpparams?
        exporter.configuration = configuration
        exporter.stdout.connect(feedback.pushInfo)
        exporter.stderr.connect(feedback.pushInfo)

        if feedback.isCanceled():
            return {}

        try:
            feedback.pushInfo(f"Run: {exporter.command(True)}")
            result = exporter.run(None)
            if result == iliexporter.Exporter.SUCCESS:
                feedback.pushInfo(self.tr("... export succeeded"))
            else:
                feedback.pushWarning(self.tr("... export failed"))
            isvalid = result
        except JavaNotFoundError as e:
            raise QgsProcessingException(
                self.tr("Java not found error:").format(e.error_string)
            )

        return {self.ISVALID: isvalid, self.XTFFILEPATH: configuration.xtffile}

    def get_configuration_from_input(self, parameters, context, tool):

        configuration = ExportConfiguration()
        configuration.base_configuration = self.parent.current_baseconfig()
        configuration.tool = tool

        # get database settings form the parent
        if not self.parent.get_db_configuration_from_input(
            parameters, context, configuration
        ):
            return None

        # get settings according to the db
        configuration.with_exporttid = self._get_tid_handling(configuration)

        # get settings from the input
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

        configuration.disable_validation = self.parent.parameterAsBool(
            parameters, self.DISABLEVALIDATION, context
        )

        configuration.xtffile = self.parent.parameterAsFile(
            parameters, self.XTFFILEPATH, context
        )

        return configuration

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
                    if name and name not in modelnames and name not in MODELS_BLACKLIST:
                        modelnames.append(name)
        return modelnames

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)


class ExportingPGAlgorithm(Ili2pgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data export from a PostgreSQL database.
    """

    def __init__(self):
        super().__init__()

        # initialize the exporter with self as parent
        self.exporter = ProcessExporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2pg_exporter"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Export with ili2pg (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "export",
            "transferfile",
            "xtf" "ili2db",
            "ili2pg",
            "Postgres",
            "PostGIS",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr("Exports data from a PostgreSQL schema with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Exports data from a PostgreSQL schema with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.exporter.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.exporter.get_configuration_from_input(
            parameters, context, DbIliMode.pg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start export")
            )
        else:
            output_map.update(self.exporter.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map


class ExportingGPKGAlgorithm(Ili2gpkgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data export from a GeoPackage file.
    """

    def __init__(self):
        super().__init__()

        # initialize the exporter with self as parent
        self.exporter = ProcessExporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2gpkg_exporter"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Export with ili2gpkg (GeoPackage)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "export",
            "transferfile",
            "xtf",
            "ili2db",
            "ili2gpkg",
            "GeoPackage",
            "GPKG",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr("Exports data from a GeoPackage file with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Exports data from a GeoPackage file with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.exporter.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.exporter.get_configuration_from_input(
            parameters, context, DbIliMode.gpkg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start export")
            )
        else:
            output_map.update(self.exporter.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map
