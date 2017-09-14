# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo
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
import os

import re
import functools
import locale

from projectgenerator.libili2pg.ili2dbutils import get_ili2pg_bin
from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop

from .ili2pg_config import ExportConfiguration, JavaNotFoundError


class Exporter(QObject):
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
        self.filename = None
        self.configuration = ExportConfiguration()
        self.encoding = locale.getlocale()[1]
        # This might be unset (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def run(self):
        ili2pg_bin = get_ili2pg_bin(self.stdout, self.stderr)

        args = ["-jar", ili2pg_bin]
        args += ["--export"]
        args += ["--dbhost", self.configuration.host]
        if self.configuration.port:
            args += ["--dbport", self.configuration.port]
        args += ["--dbusr", self.configuration.user]
        if self.configuration.password:
            args += ["--dbpwd", self.configuration.password]
        args += ["--dbdatabase", self.configuration.database]
        args += ["--dbschema", self.configuration.schema or self.configuration.database]

        args += self.configuration.base_configuration.to_ili2db_args(False)

        if self.configuration.ilimodels:
            args += ['--models', self.configuration.ilimodels]

        args += [self.configuration.xtffile]

        if self.configuration.base_configuration.java_path:
            # A java path is configured: respect it no mather what
            java_paths = [self.configuration.base_configuration.java_path]
        else:
            # By default try JAVA_HOME and PATH
            java_paths = []
            if 'JAVA_HOME' in os.environ:
                paths = os.environ['JAVA_HOME'].split(";")
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

        self.__result = Exporter.ERROR

        loop = QEventLoop()
        proc.finished.connect(loop.exit)
        loop.exec()

        self.process_finished.emit(proc.exitCode(), self.__result)
        return self.__result

    def stderr_ready(self, proc):
        text = bytes(proc.readAllStandardError()).decode(self.encoding)
        if not self.__done_pattern:
            self.__done_pattern = re.compile(r"Info: ...export done")
        if self.__done_pattern.search(text):
            self.__result = Exporter.SUCCESS

        self.stderr.emit(text)

    def stdout_ready(self, proc):
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)

