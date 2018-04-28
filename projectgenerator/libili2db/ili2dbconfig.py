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

from projectgenerator.libili2db.ili2dbutils import get_all_modeldir_in_path
from qgis.PyQt.QtNetwork import QNetworkProxy
from qgis.core import QgsNetworkAccessManager
import os

ili2db_tools = {
    'ili2pg': {
        'version': '3.11.2'
    },
    'ili2gpkg': {
        'version': '3.11.3'
    }
}
ili2db_tools['ili2pg'][
    'url'] = 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(ili2db_tools['ili2pg']['version'])
ili2db_tools['ili2gpkg'][
    'url'] = 'http://www.eisenhutinformatik.ch/interlis/ili2gpkg/ili2gpkg-{}.zip'.format(
    ili2db_tools['ili2gpkg']['version'])


class BaseConfiguration(object):

    def __init__(self):
        self.custom_model_directories_enabled = False
        self.custom_model_directories = ''
        self.java_path = ''
        self.logfile_path = ''

        self.debugging_enabled = False

    def save(self, settings):
        settings.setValue('CustomModelDirectoriesEnabled',
                          self.custom_model_directories_enabled)
        settings.setValue('CustomModelDirectories',
                          self.custom_model_directories)
        settings.setValue('JavaPath', self.java_path)
        settings.setValue('LogfilePath', self.logfile_path)
        settings.setValue('DebuggingEnabled', self.debugging_enabled)

    def restore(self, settings):
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
        self.database = ''
        self.dbschema = ''
        self.dbfile = ''
        self.tool_name = None
        self.ilifile = ''
        self.ilimodels = ''

    @property
    def uri(self):
        uri = []
        if self.tool_name == 'ili2pg':
            uri += ['dbname={}'.format(self.database)]
            uri += ['user={}'.format(self.dbusr)]
            if self.dbpwd:
                uri += ['password={}'.format(self.dbpwd)]
            uri += ['host={}'.format(self.dbhost)]
            if self.dbport:
                uri += ['port={}'.format(self.dbport)]
        elif self.tool_name == 'ili2gpkg':
            uri = [self.dbfile]
        return ' '.join(uri)

    def to_ili2db_args(self, hide_password=False):

        # Valid ili file, don't pass --modeldir (it can cause ili2db errors)
        with_modeldir = not self.ilifile

        args = self.base_configuration.to_ili2db_args(with_modeldir=with_modeldir)

        if self.tool_name == 'ili2pg':
            # PostgreSQL specific options
            args += ["--dbhost", self.dbhost]
            if self.dbport:
                args += ["--dbport", self.dbport]
            args += ["--dbusr", self.dbusr]
            if self.dbpwd:
                if hide_password:
                    args += ["--dbpwd", '******']
                else:
                    args += ["--dbpwd", self.dbpwd]
            args += ["--dbdatabase", self.database]
            args += ["--dbschema",
                     self.dbschema or self.database]
        elif self.tool_name == 'ili2gpkg':
            args += ["--dbfile", self.dbfile]

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            args += ["--proxy", proxy.hostName()]
            args += ["--proxyPort", str(proxy.port())]

        if self.ilimodels:
            args += ['--models', self.ilimodels]

        if self.ilifile:
            args += [self.ilifile]

        return args


class ExportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''

    def to_ili2db_args(self, hide_password=False, with_action=True):
        args = list()

        if with_action:
            args += ["--export"]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self, hide_password=hide_password)

        args += [self.xtffile]

        return args


class SchemaImportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.inheritance = 'smart1'
        self.epsg = 21781  # Default EPSG code in ili2pg

    def to_ili2db_args(self, hide_password=False, with_action=True):
        """
        Create an ili2db argument array, with the password masked with ****** and optionally with the action
        argument (--schemaimport) removed
        """
        args = list()

        if with_action:
            args += ["--schemaimport"]

        args += ["--coalesceCatalogueRef"]
        args += ["--createEnumTabs"]
        args += ["--createNumChecks"]
        args += ["--coalesceMultiSurface"]
        args += ["--coalesceMultiLine"]
        args += ["--coalesceMultiPoint"]
        args += ["--coalesceArray"]
        args += ["--strokeArcs"]
        args += ["--beautifyEnumDispName"]
        # args += ["--createBasketCol"]
        args += ["--createUnique"]
        args += ["--createGeomIdx"]
        args += ["--createFk"]
        args += ["--createFkIdx"]
        args += ["--createMetaInfo"]

        if self.inheritance == 'smart1':
            args += ["--smart1Inheritance"]
        elif self.inheritance == 'smart2':
            args += ["--smart2Inheritance"]
        else:
            args += ["--noSmartMapping"]

        if self.epsg != 21781:
            args += ["--defaultSrsCode", "{}".format(self.epsg)]

        if self.tool_name == 'ili2pg':
            args += ["--setupPgExt"]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self, hide_password)

        return args


class ImportDataConfiguration(SchemaImportConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''
        self.delete_data = False

    def to_ili2db_args(self, hide_password=False, with_action=True):
        args = list()

        if with_action:
            args += ["--import"]

        if self.delete_data:
            args += ["--deleteData"]

        args = SchemaImportConfiguration.to_ili2db_args(self, hide_password=hide_password, with_action=False)

        return args


class JavaNotFoundError(FileNotFoundError):
    pass
