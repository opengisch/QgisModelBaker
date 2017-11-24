# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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
import os

import re
import locale
import functools

from projectgenerator.libili2db.ili2dbutils import get_ili2db_bin
from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop
from qgis.PyQt.QtNetwork import QNetworkProxy
from qgis.core import QgsNetworkAccessManager

from .ili2dbconfig import ImportConfiguration, JavaNotFoundError


class Importer(QObject):
    SUCCESS = 0
    # TODO: Insert more codes?
    ERROR = 1000

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)

    __done_pattern = None
    __result = None

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.tool_name = None
        self.configuration = ImportConfiguration()
        self.encoding = locale.getlocale()[1]
        # This might be unset (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def run(self):
        ili2db_bin = get_ili2db_bin(self.tool_name, self.stdout, self.stderr)
        if not ili2db_bin:
            return

        args = ["-jar", ili2db_bin]
        args += ["--schemaimport"]

        if self.tool_name == 'ili2pg':
            # PostgreSQL specific options
            args += ["--dbhost", self.configuration.host]
            if self.configuration.port:
                args += ["--dbport", self.configuration.port]
            args += ["--dbusr", self.configuration.user]
            if self.configuration.password:
                args += ["--dbpwd", self.configuration.password]
            args += ["--dbdatabase", self.configuration.database]
            args += ["--dbschema", self.configuration.schema or self.configuration.database]
            args += ["--setupPgExt"]
        elif self.tool_name == 'ili2gpkg':
            args += ["--dbfile", self.configuration.dbfile]

        args += ["--coalesceCatalogueRef"]
        args += ["--createEnumTabs"]
        args += ["--createNumChecks"]
        args += ["--coalesceMultiSurface"]
        args += ["--coalesceMultiLine"]
        args += ["--strokeArcs"]
        args += ["--beautifyEnumDispName"]
        #args += ["--createBasketCol"]
        args += ["--createUnique"]
        args += ["--createGeomIdx"]
        args += ["--createFk"]
        args += ["--createFkIdx"]
        args += ["--createMetaInfo"]
        if self.configuration.inheritance == 'smart1':
            args += ["--smart1Inheritance"]
        elif self.configuration.inheritance == 'smart2':
            args += ["--smart2Inheritance"]
        else:
            args += ["--noSmartMapping"]

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            args += ["--proxy", proxy.hostName()]
            args += ["--proxyPort", str(proxy.port())]

        if self.configuration.epsg != 21781:
            args += ["--defaultSrsCode", "{}".format(self.configuration.epsg)]

        if self.configuration.ilimodels:
            args += ['--models', self.configuration.ilimodels]

        if self.configuration.ilifile:
            # Valid ili file, don't pass --modelDir (it can cause ili2db errors)
            args += self.configuration.base_configuration.to_ili2db_args(export_modeldir=False)
            args += [self.configuration.ilifile]
        else:
            args += self.configuration.base_configuration.to_ili2db_args()

        if self.configuration.base_configuration.java_path:
            # A java path is configured: respect it no mather what
            java_paths = [self.configuration.base_configuration.java_path]
        else:
            # By default try JAVA_HOME and PATH
            java_paths = []
            if 'JAVA_HOME' in os.environ:
                paths = os.environ['JAVA_HOME'].split(os.pathsep)
                for path in paths:
                    java_paths += [os.path.join(path.replace("\"","").replace("'",""), 'java')]
            java_paths += ['java']

        proc = None
        for java_path in java_paths:
            proc = QProcess()
            proc.readyReadStandardError.connect(functools.partial(self.stderr_ready, proc=proc))
            proc.readyReadStandardOutput.connect(functools.partial(self.stdout_ready, proc=proc))

            proc.start(java_path, args)

            if not proc.waitForStarted():
                proc = None
            else:
                break

        if not proc:
            raise JavaNotFoundError()

        self.process_started.emit(java_path + ' ' + ' '.join(args))

        self.__result = Importer.ERROR

        loop = QEventLoop()
        proc.finished.connect(loop.exit)
        loop.exec()

        self.process_finished.emit(proc.exitCode(), self.__result)
        return self.__result

    def stderr_ready(self, proc):
        text = bytes(proc.readAllStandardError()).decode(self.encoding)
        if not self.__done_pattern:
            self.__done_pattern = re.compile(r"Info: ...done")
        if self.__done_pattern.search(text):
            self.__result = Importer.SUCCESS

        self.stderr.emit(text)

    def stdout_ready(self, proc):
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)
