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

from QgisModelBaker.libili2db.ili2dbutils import (
    get_ili2db_bin,
    get_java_path,
    JavaNotFoundError
)
from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop

from QgisModelBaker.libili2db.ili2dbconfig import (
        SchemaImportConfiguration,
        ImportDataConfiguration
)
from QgisModelBaker.libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory


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
        self.tool = None
        self.dataImport = dataImport
        if dataImport:
            self.configuration = ImportDataConfiguration()
        else:
            self.configuration = SchemaImportConfiguration()
        self.encoding = locale.getlocale()[1]

        # Lets python try to determine the default locale
        if not self.encoding:
            self.encoding = locale.getdefaultlocale()[1]

        # This might be unset
        # (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def run(self):
        ili2db_bin = get_ili2db_bin(self.tool, self.configuration.db_ili_version, self.stdout, self.stderr)
        if not ili2db_bin:
            return

        ili2db_jar_arg = ["-jar", ili2db_bin]

        self.configuration.tool = self.tool
        db_simple_factory = DbSimpleFactory()
        db_factory = db_simple_factory.create_factory(self.tool)

        config_manager = db_factory.get_db_command_config_manager(self.configuration)

        args = config_manager.get_ili2db_args(False)
        args_hide_password = config_manager.get_ili2db_args(True)

        java_path = get_java_path(self.configuration.base_configuration)

        proc = QProcess()
        proc.readyReadStandardError.connect(
            functools.partial(self.stderr_ready, proc=proc))
        proc.readyReadStandardOutput.connect(
            functools.partial(self.stdout_ready, proc=proc))

        proc.start(java_path, ili2db_jar_arg + args)

        if not proc.waitForStarted():
            proc = None

        if not proc:
            raise JavaNotFoundError()

        safe_args = ili2db_jar_arg + args_hide_password
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
            if self.dataImport:
                self.__done_pattern = re.compile(r"Info: \.\.\.import done")
            else:
                self.__done_pattern = re.compile(r"Info: \.\.\.done")
        if self.__done_pattern.search(text):
            self.__result = Importer.SUCCESS

        self.stderr.emit(text)

    def stdout_ready(self, proc):
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)
