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

from projectgenerator.libili2db.ili2dbconfig import (
        SchemaImportConfiguration,
        ImportDataConfiguration,
        JavaNotFoundError,
        ili2db_tools
)


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

    def __init__(self, dataImport=False, parent=None):
        QObject.__init__(self, parent)
        self.filename = None
        self.tool_name = None
        self.dataImport = dataImport
        if dataImport:
            self.configuration = ImportDataConfiguration()
        else:
            self.configuration = SchemaImportConfiguration()
        self.encoding = locale.getlocale()[1]
        # This might be unset
        # (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def run(self):
        ili2db_bin = get_ili2db_bin(self.tool_name, self.stdout, self.stderr, ili2db_tools)
        if not ili2db_bin:
            return

        ili2db_jar_arg = ["-jar", ili2db_bin]

        self.configuration.tool_name = self.tool_name

        args = self.configuration.to_ili2db_args()

        if self.dataImport:
            args += [self.configuration.xtffile]

        if self.configuration.base_configuration.java_path:
            # A java path is configured: respect it no mather what
            java_paths = [self.configuration.base_configuration.java_path]
        else:
            # By default try JAVA_HOME and PATH
            java_paths = []
            if 'JAVA_HOME' in os.environ:
                paths = os.environ['JAVA_HOME'].split(os.pathsep)
                for path in paths:
                    java_paths += [os.path.join(path.replace("\"",
                                                             "").replace("'", ""), 'java')]
            java_paths += ['java']

        proc = None
        for java_path in java_paths:
            proc = QProcess()
            proc.readyReadStandardError.connect(
                functools.partial(self.stderr_ready, proc=proc))
            proc.readyReadStandardOutput.connect(
                functools.partial(self.stdout_ready, proc=proc))

            proc.start(java_path, ili2db_jar_arg + args)

            if not proc.waitForStarted():
                proc = None
            else:
                break

        if not proc:
            raise JavaNotFoundError()

        safe_args = ili2db_jar_arg + self.configuration.to_ili2db_args(hide_password=True)
        safe_command = java_path + ' ' + ' '.join(safe_args)
        self.process_started.emit(safe_command)

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
