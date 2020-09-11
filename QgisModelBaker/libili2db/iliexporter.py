# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
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

import re
import functools
import locale

from QgisModelBaker.libili2db.ili2dbutils import (
    get_ili2db_bin,
    get_java_path,
    JavaNotFoundError
)
from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop

from QgisModelBaker.libili2db.ili2dbconfig import ExportConfiguration
from QgisModelBaker.libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory


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
        self.tool = None
        self.configuration = ExportConfiguration()
        self.encoding = locale.getlocale()[1]

        # Lets python try to determine the default locale
        if not self.encoding:
            self.encoding = locale.getdefaultlocale()[1]

        # This might be unset
        # (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def args(self, hide_password ):
        self.configuration.tool = self.tool
        db_simple_factory = DbSimpleFactory()
        db_factory = db_simple_factory.create_factory(self.tool)

        config_manager = db_factory.get_db_command_config_manager(self.configuration)

        return config_manager.get_ili2db_args(hide_password)

    def command(self, hide_password, version=4):
        ili2db_bin = get_ili2db_bin(self.tool, version, self.stdout, self.stderr)
        if not ili2db_bin:
            return

        ili2db_jar_arg = ["-jar", ili2db_bin]

        args = self.args(hide_password)

        java_path = get_java_path(self.configuration.base_configuration)

        command_args = ili2db_jar_arg + args
        command = java_path + ' ' + ' '.join(command_args)

        return command

    def command_with_password(self, command):
        if '--dbpwd ******' in command:
            args = self.args(False)
            i = args.index('--dbpwd')
            command = command.replace('--dbpwd ******', '--dbpwd '+args[i+1])
        return command

    def command_without_password(self, command):
        regex = re.compile('--dbpwd [^ ]*')
        match = regex.match(command)
        if match:
            command = command.replace(match.group(1), '--dbpwd ******')
        return command

    def run(self, version=4, command=None):
        if not command:
            # we usually use version 4 except in case of a fallback
            command = self.command(False,version)

        proc = QProcess()
        proc.readyReadStandardError.connect(
            functools.partial(self.stderr_ready, proc=proc))
        proc.readyReadStandardOutput.connect(
            functools.partial(self.stdout_ready, proc=proc))

        proc.start(self.command_with_password(command))

        if not proc.waitForStarted():
            proc = None

        if not proc:
            raise JavaNotFoundError()

        self.process_started.emit(self.command_without_password(command))

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
