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

from QgisModelBaker.libili2db.ili2dbutils import get_all_modeldir_in_path
from qgis.PyQt.QtNetwork import QNetworkProxy
from qgis.core import QgsNetworkAccessManager
from ..libili2db.globals import DbIliMode


class BaseConfiguration(object):

    def __init__(self):
        self.super_pg_user = 'postgres'
        self.super_pg_password = 'postgres'

        self.custom_model_directories_enabled = False
        self.custom_model_directories = ''
        self.java_path = ''
        self.logfile_path = ''

        self.debugging_enabled = False

    def save(self, settings):
        settings.setValue('SuperUser', self.super_pg_user)
        settings.setValue('SuperPassword', self.super_pg_password)
        settings.setValue('CustomModelDirectoriesEnabled',
                          self.custom_model_directories_enabled)
        settings.setValue('CustomModelDirectories',
                          self.custom_model_directories)
        settings.setValue('JavaPath', self.java_path)
        settings.setValue('LogfilePath', self.logfile_path)
        settings.setValue('DebuggingEnabled', self.debugging_enabled)

    def restore(self, settings):
        self.super_pg_user = settings.value(
            'SuperUser', 'postgres', str )
        self.super_pg_password = settings.value(
            'SuperPassword', 'postgres', str )
        self.custom_model_directories_enabled = settings.value(
            'CustomModelDirectoriesEnabled', False, bool)
        self.custom_model_directories = settings.value(
            'CustomModelDirectories', '', str)
        self.java_path = settings.value('JavaPath', '', str)
        self.debugging_enabled = settings.value(
            'DebuggingEnabled', False, bool)
        self.logfile_path = settings.value('LogfilePath', '', str)

    def to_ili2db_args(self, with_modeldir=True):
        """
        Create an ili2db command line argument string from this configuration
        """
        args = list()

        if with_modeldir:
            if self.custom_model_directories_enabled and self.custom_model_directories:
                str_model_directories = [get_all_modeldir_in_path(path) for path in
                                         self.custom_model_directories.split(';')]
                str_model_directories = ';'.join(str_model_directories)
                args += ['--modeldir', str_model_directories]
        if self.debugging_enabled and self.logfile_path:
            args += ['--trace']
            args += ['--log', self.logfile_path]
        return args

    @property
    def model_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(';')
        else:
            dirs = [
                '%ILI_FROM_DB',
                '%XTF_DIR',
                'http://models.interlis.ch/',
                '%JAR_DIR'
            ]
        return dirs


class Ili2DbCommandConfiguration(object):
    def __init__(self):
        self.base_configuration = BaseConfiguration()

        self.dbport = ''
        self.dbhost = ''
        self.dbpwd = ''
        self.dbusr = ''
        self.db_use_super_login = False
        self.database = ''
        self.dbschema = ''
        self.dbfile = ''
        self.tool = None
        self.ilifile = ''
        self.ilimodels = ''
        self.tomlfile = ''

    def to_ili2db_args(self):

        # Valid ili file, don't pass --modeldir (it can cause ili2db errors)
        with_modeldir = not self.ilifile

        args = self.base_configuration.to_ili2db_args(with_modeldir=with_modeldir)

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            args += ["--proxy", proxy.hostName()]
            args += ["--proxyPort", str(proxy.port())]

        if self.ilimodels:
            args += ['--models', self.ilimodels]

        if self.tomlfile:
            args += ["--iliMetaAttrs", self.tomlfile]

        return args


class ExportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''
        self.iliexportmodels = ''
        self.disable_validation = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()
        
        args += extra_args

        if with_action:
            args += ["--export"]

        if self.disable_validation:
            args += ["--disableValidation"]

        if self.iliexportmodels:
            args += ['--exportModels', self.iliexportmodels]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self)

        args += [self.xtffile]

        return args


class SchemaImportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.inheritance = 'smart1'
        self.create_basket_col = False
        self.create_import_tid = True
        self.epsg = 21781  # Default EPSG code in ili2pg
        self.stroke_arcs = True

    def to_ili2db_args(self, extra_args=[], with_action=True):
        """
        Create an ili2db argument array, with the password masked with ****** and optionally with the ``action``
        argument (--schemaimport) removed
        """
        args = list()

        if with_action:
            args += ["--schemaimport"]

        args += extra_args

        args += ["--coalesceCatalogueRef"]
        args += ["--createEnumTabs"]
        args += ["--createNumChecks"]
        args += ["--coalesceMultiSurface"]
        args += ["--coalesceMultiLine"]
        args += ["--coalesceMultiPoint"]
        args += ["--coalesceArray"]
        args += ["--beautifyEnumDispName"]
        args += ["--createUnique"]
        args += ["--createGeomIdx"]
        args += ["--createFk"]
        args += ["--createEnumTabsWithId"]
        args += ["--createFkIdx"]
        args += ["--createMetaInfo"]
        args += ["--expandMultilingual"]
        args += ["--createTidCol"]

        if self.create_import_tid:
            args += ["--importTid"]

        if self.inheritance == 'smart1':
            args += ["--smart1Inheritance"]
        elif self.inheritance == 'smart2':
            args += ["--smart2Inheritance"]
        else:
            args += ["--noSmartMapping"]

        if self.stroke_arcs:
            args += ["--strokeArcs"]

        if self.create_basket_col:
            args += ["--createBasketCol"]

        if self.epsg != 21781:
            args += ["--defaultSrsCode", "{}".format(self.epsg)]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self)

        if self.ilifile:
            args += [self.ilifile]
        
        return args


class ImportDataConfiguration(SchemaImportConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''
        self.delete_data = False
        self.disable_validation = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            args += ["--import"]

        # No schema import, see https://github.com/opengisch/QgisModelBaker/issues/322
        # args += ["--doSchemaImport"]

        if self.disable_validation:
            args += ["--disableValidation"]

        if self.delete_data:
            args += ["--deleteData"]

        args += SchemaImportConfiguration.to_ili2db_args(self, extra_args=extra_args, with_action=False)

        args += [self.xtffile]

        return args
