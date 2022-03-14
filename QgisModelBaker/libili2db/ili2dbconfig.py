# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkProxy

from QgisModelBaker.libili2db.ili2dbutils import get_all_modeldir_in_path


class BaseConfiguration(object):
    def __init__(self):
        self.super_pg_user = "postgres"
        self.super_pg_password = "postgres"

        self.custom_model_directories_enabled = False
        self.custom_model_directories = ""
        self.java_path = ""
        self.logfile_path = ""

        self.debugging_enabled = False

    def save(self, settings):
        settings.setValue("SuperUser", self.super_pg_user)
        settings.setValue("SuperPassword", self.super_pg_password)
        settings.setValue(
            "CustomModelDirectoriesEnabled", self.custom_model_directories_enabled
        )
        settings.setValue("CustomModelDirectories", self.custom_model_directories)
        settings.setValue("JavaPath", self.java_path)
        settings.setValue("LogfilePath", self.logfile_path)
        settings.setValue("DebuggingEnabled", self.debugging_enabled)

    def restore(self, settings):
        self.super_pg_user = settings.value("SuperUser", "postgres", str)
        self.super_pg_password = settings.value("SuperPassword", "postgres", str)
        self.custom_model_directories_enabled = settings.value(
            "CustomModelDirectoriesEnabled", False, bool
        )
        self.custom_model_directories = settings.value(
            "CustomModelDirectories", "", str
        )
        self.java_path = settings.value("JavaPath", "", str)
        self.debugging_enabled = settings.value("DebuggingEnabled", False, bool)
        self.logfile_path = settings.value("LogfilePath", "", str)

    def to_ili2db_args(self, with_modeldir=True):
        """
        Create an ili2db command line argument string from this configuration
        """
        args = list()

        if with_modeldir:
            if self.custom_model_directories_enabled and self.custom_model_directories:
                str_model_directories = [
                    get_all_modeldir_in_path(path)
                    for path in self.custom_model_directories.split(";")
                ]
                str_model_directories = ";".join(str_model_directories)
                args += ["--modeldir", str_model_directories]
        if self.debugging_enabled and self.logfile_path:
            args += ["--trace"]
            args += ["--log", self.logfile_path]
        return args

    @property
    def model_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(";")
        else:
            dirs = [
                "%ILI_FROM_DB",
                "%XTF_DIR",
                "http://models.interlis.ch/",
                "%JAR_DIR",
            ]
        return dirs

    @property
    def metaconfig_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(";")
        else:
            dirs = ["https://models.opengis.ch/"]
        return dirs


class Ili2DbCommandConfiguration(object):
    def __init__(self):
        self.base_configuration = BaseConfiguration()

        self.dbport = ""
        self.dbhost = ""
        self.dbpwd = ""
        self.dbusr = ""
        self.dbauthid = ""
        self.db_use_super_login = False
        self.database = ""
        self.dbschema = ""
        self.dbfile = ""
        self.dbservice = None
        self.sslmode = None
        self.tool = None
        self.ilifile = ""
        self.ilimodels = ""
        self.tomlfile = ""
        self.dbinstance = ""
        self.db_odbc_driver = ""
        self.disable_validation = False
        self.metaconfig = None
        self.metaconfig_id = None
        self.db_ili_version = None

    def append_args(self, args, values, consider_metaconfig=False):
        if consider_metaconfig and self.metaconfig and values:
            if "ch.ehi.ili2db" in self.metaconfig.sections():
                metaconfig_ili2db_params = self.metaconfig["ch.ehi.ili2db"]
                if values[0][2:] in metaconfig_ili2db_params.keys():
                    return
        args += values

    def to_ili2db_args(self):

        # Valid ili file, don't pass --modeldir (it can cause ili2db errors)
        with_modeldir = not self.ilifile

        args = self.base_configuration.to_ili2db_args(with_modeldir=with_modeldir)

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            self.append_args(args, ["--proxy", proxy.hostName()])
            self.append_args(args, ["--proxyPort", str(proxy.port())])

        if self.ilimodels:
            self.append_args(args, ["--models", self.ilimodels])

        if self.tomlfile:
            self.append_args(args, ["--iliMetaAttrs", self.tomlfile])

        return args


class ExportConfiguration(Ili2DbCommandConfiguration):
    def __init__(self):
        super().__init__()
        self.xtffile = ""
        self.with_exporttid = False
        self.iliexportmodels = ""
        self.dataset = ""
        self.baskets = list()

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        self.append_args(args, extra_args)

        if with_action:
            self.append_args(args, ["--export"])

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.with_exporttid:
            self.append_args(args, ["--exportTid"])

        if self.iliexportmodels:
            self.append_args(args, ["--exportModels", self.iliexportmodels])

        if self.db_ili_version == 3:
            self.append_args(args, ["--export3"])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        self.append_args(args, [self.xtffile])

        return args


class SchemaImportConfiguration(Ili2DbCommandConfiguration):
    def __init__(self):
        super().__init__()
        self.inheritance = "smart1"
        self.create_basket_col = True
        self.create_import_tid = True
        self.srs_auth = "EPSG"  # Default SRS auth in ili2db
        self.srs_code = 2056  # Default SRS code in ili2db
        self.stroke_arcs = True
        self.pre_script = ""
        self.post_script = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        """
        Create an ili2db argument array, with the password masked with ****** and optionally with the ``action``
        argument (--schemaimport) removed
        """
        args = list()

        if with_action:
            self.append_args(args, ["--schemaimport"])

        self.append_args(args, extra_args)

        self.append_args(args, ["--coalesceCatalogueRef"], True)
        self.append_args(args, ["--createEnumTabs"], True)

        if self.disable_validation:
            self.append_args(args, ["--sqlEnableNull"])

        else:
            self.append_args(args, ["--createNumChecks"])
            self.append_args(args, ["--createUnique"])
            self.append_args(args, ["--createFk"])

        self.append_args(args, ["--createFkIdx"], True)
        self.append_args(args, ["--coalesceMultiSurface"], True)
        self.append_args(args, ["--coalesceMultiLine"], True)
        self.append_args(args, ["--coalesceMultiPoint"], True)
        self.append_args(args, ["--coalesceArray"], True)
        self.append_args(args, ["--beautifyEnumDispName"], True)
        self.append_args(args, ["--createGeomIdx"], True)
        self.append_args(args, ["--createMetaInfo"], True)
        self.append_args(args, ["--expandMultilingual"], True)

        if self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--createTypeConstraint"], True)
            self.append_args(args, ["--createEnumTabsWithId"], True)
            self.append_args(args, ["--createTidCol"], True)

        # version 3 backwards compatibility (not needed in newer versions)
        if self.create_import_tid:
            self.append_args(args, ["--importTid"])

        if self.inheritance == "smart1":
            self.append_args(args, ["--smart1Inheritance"])
        elif self.inheritance == "smart2":
            self.append_args(args, ["--smart2Inheritance"])
        else:
            self.append_args(args, ["--noSmartMapping"])

        if self.stroke_arcs:
            self.append_args(args, ["--strokeArcs"])

        if self.create_basket_col:
            self.append_args(args, ["--createBasketCol"])

        if self.srs_auth != "EPSG":
            self.append_args(args, ["--defaultSrsAuth", self.srs_auth])

        self.append_args(args, ["--defaultSrsCode", "{}".format(self.srs_code)])

        if self.pre_script:
            self.append_args(args, ["--preScript", self.pre_script])

        if self.post_script:
            self.append_args(args, ["--postScript", self.post_script])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        if self.ilifile:
            self.append_args(args, [self.ilifile])

        return args


class ImportDataConfiguration(SchemaImportConfiguration):
    def __init__(self):
        super().__init__()
        self.xtffile = ""
        self.delete_data = False
        self.with_importtid = False
        self.dataset = ""
        self.baskets = list()
        self.with_schemaimport = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--import"])

        if self.with_schemaimport:
            self.append_args(args, ["--doSchemaImport"])

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.delete_data:
            self.append_args(args, ["--deleteData"])

        if self.with_importtid:
            self.append_args(args, ["--importTid"])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        self.append_args(
            args,
            SchemaImportConfiguration.to_ili2db_args(
                self, extra_args=extra_args, with_action=False
            ),
        )

        self.append_args(args, [self.xtffile])

        return args


class UpdateDataConfiguration(Ili2DbCommandConfiguration):
    def __init__(self):
        super().__init__()
        self.xtffile = ""
        self.dataset = ""
        self.with_importtid = False
        self.with_importbid = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--update"])

        self.append_args(args, extra_args)

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.with_importtid:
            self.append_args(args, ["--importTid"])

        if self.with_importbid:
            self.append_args(args, ["--importBid"])

        self.append_args(args, ["--dataset", self.dataset])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        self.append_args(args, [self.xtffile])

        return args


class ValidateConfiguration(Ili2DbCommandConfiguration):
    def __init__(self):
        super().__init__()
        self.ilimodels = ""
        self.topics = ""
        self.dataset = ""
        self.baskets = list()
        self.xtflog = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--validate"])

        self.append_args(args, extra_args)

        if self.ilimodels:
            self.append_args(args, ["--models", self.ilimodels])

        if self.topics:
            self.append_args(args, ["--dataset", self.topics])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        if self.xtflog:
            self.append_args(args, ["--xtflog", self.xtflog])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        return args
