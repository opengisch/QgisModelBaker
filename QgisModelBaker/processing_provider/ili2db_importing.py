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
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication, QObject

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper import iliimporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
    ImportDataConfiguration,
    UpdateDataConfiguration,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.processing_provider.ili2db_algorithm import (
    Ili2gpkgAlgorithm,
    Ili2pgAlgorithm,
)
from QgisModelBaker.utils.gui_utils import MODELS_BLACKLIST


class ProcessImporter(QObject):

    # Settings
    DISABLEVALIDATION = "DISABLEVALIDATION"
    DATASET = "DATASET"
    DELETEDATA = "DELETEDATA"

    XTFFILEPATH = "XTFFILEPATH"

    # Result
    ISVALID = "ISVALID"

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def import_input_params(self):
        params = []

        xtffile_param = QgsProcessingParameterFile(
            self.XTFFILEPATH,
            self.tr("Source Transferfile (XTF)"),
            defaultValue=None,
            optional=False,
        )
        xtffile_param.setHelp(
            self.tr("The XTF File where the data should be imported from.")
        )
        params.append(xtffile_param)

        dataset_param = QgsProcessingParameterString(
            self.DATASET, self.tr("Dataset name"), optional=True
        )
        dataset_param.setHelp(
            self.tr(
                "The dataset the data should be connected to (works only when basket handling is active in the existing database)."
            )
        )
        params.append(dataset_param)

        deletedata_param = QgsProcessingParameterBoolean(
            self.DELETEDATA,
            self.tr("Delete data first"),
            defaultValue=False,
        )
        deletedata_param.setHelp(
            self.tr(
                "Deletes previously existing data from the target database (when basket handling active it performs a --replace instead of an --update)"
            )
        )
        params.append(deletedata_param)

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

    def import_output_params(self):
        params = []

        params.append(
            QgsProcessingOutputBoolean(self.ISVALID, self.tr("Import Result"))
        )

        return params

    def initParameters(self):
        for connection_input_param in self.parent.connection_input_params():
            self.parent.addParameter(connection_input_param)
        for connection_output_param in self.parent.connection_output_params():
            self.parent.addOutput(connection_output_param)

        for import_input_param in self.import_input_params():
            self.parent.addParameter(import_input_param)
        for import_output_param in self.import_output_params():
            self.parent.addOutput(import_output_param)

    def run(self, configuration, feedback):

        # run
        importer = iliimporter.Importer(self)
        importer.tool = configuration.tool

        # to do superuser finden? und auch dpparams?
        importer.configuration = configuration
        importer.stdout.connect(feedback.pushInfo)
        importer.stderr.connect(feedback.pushInfo)

        if feedback.isCanceled():
            return {}

        try:
            feedback.pushInfo(f"Run: {importer.command(True)}")
            result = importer.run(None)
            if result == iliimporter.Importer.SUCCESS:
                feedback.pushInfo(self.tr("... import succeeded"))
            else:
                feedback.pushWarning(self.tr("... import failed"))
            isvalid = result
        except JavaNotFoundError as e:
            raise QgsProcessingException(
                self.tr("Java not found error:").format(e.error_string)
            )

        return {self.ISVALID: isvalid, self.XTFFILEPATH: configuration.xtffile}

    def get_configuration_from_input(self, parameters, context, tool):

        configuration = Ili2DbCommandConfiguration()
        configuration.tool = tool

        # get database settings form the parent
        if not self.parent.get_db_configuration_from_input(
            parameters, context, configuration
        ):
            return None

        # get settings according to the db
        if not self._basket_handling(configuration):
            configuration = ImportDataConfiguration(configuration)
        else:
            configuration = UpdateDataConfiguration(configuration)
            configuration.with_importbid = True
        configuration.with_importtid = self._get_tid_handling(configuration)

        # get settings from the input
        configuration.disable_validation = self.parent.parameterAsBool(
            parameters, self.DISABLEVALIDATION, context
        )
        configuration.delete_data = self.parent.parameterAsBool(
            parameters, self.DELETEDATA, context
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

    def _basket_handling(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.get_basket_handling()
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


class ImportingPGAlgorithm(Ili2pgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data import to a PostgreSQL database.
    """

    def __init__(self):
        super().__init__()

        # initialize the importer with self as parent
        self.importer = ProcessImporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2pg_importer"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Import with ili2pg (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "import",
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
        return self.tr("Imports data to a PostgreSQL schema with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Imports data to a PostgreSQL schema with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.importer.initParameters()

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
                self.tr("Invalid input parameters. Cannot start import")
            )
        else:
            output_map.update(self.importer.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map


class ImportingGPKGAlgorithm(Ili2gpkgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data import to a GeoPackage file.
    """

    def __init__(self):
        super().__init__()

        # initialize the importer with self as parent
        self.importer = ProcessImporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2gpkg_importer"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Import with ili2gpkg (GeoPackage)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "import",
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
        return self.tr("Imports data to a GeoPackage file with ili2db.")

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr("Imports data to a GeoPackage file with ili2db.")

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.importer.initParameters()

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
        configuration = self.importer.get_configuration_from_input(
            parameters, context, DbIliMode.gpkg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start import")
            )
        else:
            output_map.update(self.importer.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map
