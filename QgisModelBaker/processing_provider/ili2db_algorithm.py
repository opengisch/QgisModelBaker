import os
from abc import abstractmethod

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingOutputFile,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterAuthConfig,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication, QSettings
from qgis.PyQt.QtGui import QIcon

import QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig as ili2dbconfig
import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils


class Ili2dbAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("ili2db")

    def groupId(self):
        return "ili2db"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "../images/interlis.png"))

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()

    @abstractmethod
    def connection_input_params(self):
        return []

    @abstractmethod
    def connection_output_params(self):
        return []

    @abstractmethod
    def get_db_configuration_from_input(self, parameters, context, configuration):
        return False

    @abstractmethod
    def get_output_from_db_configuration(self, configuration):
        return {}

    @abstractmethod
    def get_settings_configuration_from_input(self, parameters, context, configuration):
        return

    def current_baseconfig(self):
        baseconfig = ili2dbconfig.BaseConfiguration()
        settings = QSettings()
        settings.beginGroup("QgisModelBaker/ili2db")
        baseconfig.restore(settings)
        return baseconfig


class Ili2pgAlgorithm(Ili2dbAlgorithm):

    SERVICE = "SERVICE"
    HOST = "HOST"
    DBNAME = "DBNAME"
    PORT = "PORT"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    SCHEMA = "SCHEMA"
    SSLMODE = "SSLMODE"
    AUTHCFG = "AUTHCFG"

    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("ili2db")

    def groupId(self):
        return "ili2db"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "../images/interlis.png"))

    def connection_input_params(self):
        params = []

        service_param = QgsProcessingParameterString(
            self.SERVICE,
            self.tr("Service"),
            None,
            optional=True,
        )
        service_param.setHelp(self.tr("The PostgreSQL service config file."))
        params.append(service_param)

        host_param = QgsProcessingParameterString(
            self.HOST,
            self.tr("Host"),
            defaultValue="localhost",
            optional=True,
        )
        host_param.setHelp(
            self.tr("The host of the database server. By default is localhost.")
        )
        params.append(host_param)

        port_param = QgsProcessingParameterNumber(
            self.PORT,
            self.tr("Port"),
            type=QgsProcessingParameterNumber.Type.Integer,
            defaultValue=5432,
            optional=True,
        )
        port_param.setHelp(
            self.tr("The port of the database server. By default is 5432.")
        )
        params.append(port_param)

        dbname_param = QgsProcessingParameterString(
            self.DBNAME,
            self.tr("Database"),
            defaultValue=None,
            optional=True,
        )
        dbname_param.setHelp(self.tr("The database name. The database should exist."))
        params.append(dbname_param)

        schema_param = QgsProcessingParameterString(
            self.SCHEMA,
            self.tr("Schema"),
            defaultValue=None,
            optional=True,
        )
        schema_param.setHelp(self.tr("The database schema."))
        params.append(schema_param)

        sslmode_param = QgsProcessingParameterEnum(
            self.SSLMODE,
            self.tr("SSL Mode"),
            ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"],
            defaultValue=None,
            optional=True,
            usesStaticStrings=True,
        )
        sslmode_param.setHelp(self.tr("The SSL mode if needed."))
        params.append(sslmode_param)
        username_param = QgsProcessingParameterString(
            self.USERNAME,
            self.tr("Username"),
            defaultValue=None,
            optional=True,
        )
        username_param.setHelp(self.tr("The username to access the database."))
        params.append(username_param)

        password_param = QgsProcessingParameterString(
            self.PASSWORD,
            self.tr("Password"),
            defaultValue=None,
            optional=True,
        )
        password_param.setHelp(self.tr("The password of the user."))
        params.append(password_param)

        authcfg_param = QgsProcessingParameterAuthConfig(
            self.AUTHCFG,
            self.tr("Authentification"),
            defaultValue=None,
            optional=True,
        )
        authcfg_param.setHelp(
            self.tr(
                "When choosing a QGIS Autentification you don't need username and password."
            )
        )
        params.append(authcfg_param)

        return params

    def connection_output_params(self):
        params = []

        # outputs for pass through
        params.append(QgsProcessingOutputString(self.SERVICE, self.tr("Service")))
        params.append(QgsProcessingOutputString(self.HOST, self.tr("Host")))
        params.append(QgsProcessingOutputString(self.DBNAME, self.tr("Database Name")))
        params.append(QgsProcessingOutputNumber(self.PORT, self.tr("Port Number")))
        params.append(QgsProcessingOutputString(self.USERNAME, self.tr("Username")))
        params.append(QgsProcessingOutputString(self.PASSWORD, self.tr("Password")))
        params.append(QgsProcessingOutputString(self.SCHEMA, self.tr("Schema")))
        params.append(QgsProcessingOutputString(self.SSLMODE, self.tr("SSL Mode")))
        params.append(
            QgsProcessingOutputString(self.AUTHCFG, self.tr("Authentication"))
        )

        return params

    def get_db_configuration_from_input(self, parameters, context, configuration):
        """
        Returns true if mandatory parameters are given
        """

        configuration.dbservice = self.parameterAsString(
            parameters, self.SERVICE, context
        )
        service_map, _ = db_utils.get_service_config(configuration.dbservice)

        if self.parameterAsString(parameters, self.AUTHCFG, context):
            configuration.dbauthid = self.parameterAsString(
                parameters, self.AUTHCFG, context
            )  # needed for passthroug
            authconfig_map = db_utils.get_authconfig_map(configuration.dbauthid)
            configuration.dbusr = authconfig_map.get("username")
            configuration.dbpwd = authconfig_map.get("password")
        else:
            configuration.dbusr = self.parameterAsString(
                parameters, self.USERNAME, context
            ) or service_map.get("user")
            configuration.dbpwd = self.parameterAsString(
                parameters, self.PASSWORD, context
            ) or service_map.get("password")
        configuration.dbhost = self.parameterAsString(
            parameters, self.HOST, context
        ) or service_map.get("host")
        configuration.dbport = str(
            self.parameterAsInt(parameters, self.PORT, context)
        ) or service_map.get("port")
        configuration.database = self.parameterAsString(
            parameters, self.DBNAME, context
        ) or service_map.get("dbname")
        configuration.dbschema = self.parameterAsString(
            parameters, self.SCHEMA, context
        )
        configuration.sslmode = self.parameterAsEnum(parameters, self.SSLMODE, context)
        valid = bool(
            configuration.dbhost and configuration.database and configuration.dbschema
        )
        return valid

    def get_output_from_db_configuration(self, configuration):
        """
        Returns an output map
        """

        output_map = {
            self.SERVICE: configuration.dbservice,
            self.HOST: configuration.dbhost,
            self.DBNAME: configuration.database,
            self.PORT: configuration.dbport,
            self.USERNAME: configuration.dbusr,
            self.PASSWORD: configuration.dbpwd,
            self.SCHEMA: configuration.dbschema,
            self.SSLMODE: configuration.sslmode,
            self.AUTHCFG: configuration.dbauthid,
        }
        return output_map


class Ili2gpkgAlgorithm(Ili2dbAlgorithm):

    DBPATH = "DBPATH"

    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("ili2db")

    def groupId(self):
        return "ili2db"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "../images/interlis.png"))

    def connection_input_params(self):
        params = []

        dbpath_param = QgsProcessingParameterFile(
            self.DBPATH,
            self.tr("Database File"),
            defaultValue=None,
            optional=True,
        )
        dbpath_param.setHelp(self.tr("todo"))
        params.append(dbpath_param)

        return params

    def connection_output_params(self):
        params = []

        params.append(
            QgsProcessingOutputFile(self.DBPATH, self.tr("Databasefile Path"))
        )

        return params

    def get_db_configuration_from_input(self, parameters, context, configuration):
        """
        Returns true if mandatory parameters are given
        """
        valid = False
        dbpath = self.parameterAsFile(parameters, self.DBPATH, context)
        if dbpath and dbpath.endswith(".gpkg"):
            configuration.dbfile = dbpath
            valid = True
        return valid

    def get_output_from_db_configuration(self, configuration):
        """
        Returns an output map
        """

        output_map = {self.DBPATH: configuration.dbfile}
        return output_map
