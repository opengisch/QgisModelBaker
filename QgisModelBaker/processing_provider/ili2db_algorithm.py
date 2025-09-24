import os
from abc import abstractmethod

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterAuthConfig,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

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
    def get_db_settings(self, connection):
        return False


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

    def addConnectionParams(self):

        service_param = QgsProcessingParameterString(
            self.SERVICE,
            self.tr("Service"),
            None,
            optional=True,
        )
        service_param.setHelp(self.tr("todo"))
        self.addParameter(service_param)

        host_param = QgsProcessingParameterString(
            self.HOST,
            self.tr("Host"),
            defaultValue="localhost",
            optional=True,
        )
        host_param.setHelp(self.tr("todo"))
        self.addParameter(host_param)

        port_param = QgsProcessingParameterNumber(
            self.PORT,
            self.tr("Port"),
            type=QgsProcessingParameterNumber.Type.Integer,
            defaultValue=5432,
            optional=True,
        )
        port_param.setHelp(self.tr("todo"))
        self.addParameter(port_param)

        dbname_param = QgsProcessingParameterString(
            self.DBNAME,
            self.tr("Database"),
            defaultValue=None,
            optional=True,
        )
        dbname_param.setHelp(self.tr("todo"))
        self.addParameter(dbname_param)

        username_param = QgsProcessingParameterString(
            self.USERNAME,
            self.tr("Username"),
            defaultValue=None,
            optional=True,
        )
        username_param.setHelp(self.tr("todo"))
        self.addParameter(username_param)

        password_param = QgsProcessingParameterString(
            self.PASSWORD,
            self.tr("Password"),
            defaultValue=None,
            optional=True,
        )
        password_param.setHelp(self.tr("todo"))
        self.addParameter(password_param)

        schema_param = QgsProcessingParameterString(
            self.SCHEMA,
            self.tr("Schema"),
            defaultValue=None,
            optional=True,
        )
        schema_param.setHelp(self.tr("todo"))
        self.addParameter(schema_param)

        sslmode_param = QgsProcessingParameterEnum(
            self.SSLMODE,
            self.tr("SSL Mode"),
            ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"],
            defaultValue=None,
            optional=True,
        )
        sslmode_param.setHelp(self.tr("todo"))
        self.addParameter(sslmode_param)

        authcfg_param = QgsProcessingParameterAuthConfig(
            self.AUTHCFG,
            self.tr("Authentification"),
            defaultValue=None,
            optional=True,
        )
        authcfg_param.setHelp(self.tr("todo"))
        self.addParameter(authcfg_param)

        # outputs for pass through
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

    def get_db_settings(self, parameters, context, configuration):
        """
        Returns true if mandatory parameters are given
        """

        service = self.parameterAsString(parameters, self.SERVICE, context)
        service_map, _ = db_utils.get_service_config(service)

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
        valid = bool(
            configuration.dbhost and configuration.database and configuration.dbschema
        )
        return valid


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

    def addConnectionParams(self):

        dbpath_param = QgsProcessingParameterString(
            self.DBPATH,
            self.tr("Database File"),
            defaultValue=None,
            optional=True,
        )
        dbpath_param.setHelp(self.tr("todo"))
        self.addParameter(dbpath_param)

        self.addOutput(
            QgsProcessingOutputString(self.DBPATH, self.tr("Databasefile Path"))
        )

    def get_db_settings(self, parameters, context, connection):
        """
        Returns true if mandatory parameters are given
        """
        valid = False
        dbpath = self.parameterAsString(parameters, self.DBPATH, context)
        if dbpath:
            connection.db_file = dbpath
            valid = True
        return valid
