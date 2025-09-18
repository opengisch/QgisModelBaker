import os

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterAuthConfig,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
)
from qgis.PyQt.QtGui import QIcon


class Ili2dbAlgorithm(QgsProcessingAlgorithm):

    # Connection
    SOURCELAYER = "SOURCELAYER"
    SOURCETYPE = "SOURCETYPE"
    ## PG
    SERVICE = "SERVICE"
    HOST = "HOST"
    DBNAME = "DBNAME"
    PORT = "PORT"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    AUTHCFG = "AUTHCFG"
    SCHEMA = "SCHEMA"
    SSLMODE = "SSLMODE"
    ## GPKG
    DBPATH = "DBPATH"

    def __init__(self):
        super().__init__()

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "../images/interlis.png"))

    def addConnectionParams(self):

        # If a sourcelayer is set, the connection settings are taken from it
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

        sourcetype_param = QgsProcessingParameterEnum(
            self.SOURCETYPE,
            self.tr("Source"),
            ["GeoPackage", "PostGIS"],
            defaultValue="PostGIS",
            optional=False,
        )
        sourcetype_param.setHelp(self.tr("todo"))
        self.addParameter(sourcetype_param)

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

        dbname_param = QgsProcessingParameterString(
            self.DBNAME,
            self.tr("Database"),
            defaultValue=None,
            optional=True,
        )
        dbname_param.setHelp(self.tr("todo"))
        self.addParameter(dbname_param)

        schema_param = QgsProcessingParameterString(
            self.SCHEMA,
            self.tr("Schema"),
            defaultValue=None,
            optional=True,
        )
        schema_param.setHelp(self.tr("todo"))
        self.addParameter(schema_param)

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

        sourcetype_param = QgsProcessingParameterEnum(
            self.SOURCETYPE,
            self.tr("Source"),
            ["GeoPackage", "PostGIS"],
            defaultValue="PostGIS",
            optional=False,
        )
        sourcetype_param.setHelp(self.tr("todo"))
        self.addParameter(sourcetype_param)

        authcfg_param = QgsProcessingParameterAuthConfig(
            self.AUTHCFG,
            self.tr("Authentification"),
            None,
            True,
        )
        authcfg_param.setHelp(self.tr("todo"))
        self.addParameter(authcfg_param)
