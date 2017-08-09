# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 01/08/17
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
import tempfile
import zipfile
import functools
import locale

from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop

from projectgenerator.utils.qt_utils import download_file
from .ili2pg_config import ExportConfiguration, JavaNotFoundError, ILI2PG_VERSION, ILI2PG_URL


class DataImporter(QObject):
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
        self.configuration = ExportConfiguration() # Also valid for basic data import
        self.encoding = locale.getlocale()[1]
        # This might be unset (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    def run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        ili2pg_dir = 'ili2pg-{}'.format(ILI2PG_VERSION)

        ili2pg_file = os.path.join(dir_path, 'bin', ili2pg_dir, 'ili2pg.jar')
        if not os.path.isfile(ili2pg_file):
            try:
                os.mkdir(os.path.join(dir_path, 'bin'))
            except FileExistsError:
                pass

            tmpfile = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)

            self.stdout.emit(self.tr('Downloading ili2pg version {}...'.format(ILI2PG_VERSION)))
            download_file(ILI2PG_URL, tmpfile.name, on_progress=lambda received, total: self.stdout.emit('.'))

            try:
                with zipfile.ZipFile(tmpfile.name, "r") as z:
                    z.extractall(os.path.join(dir_path, 'bin'))
            except zipfile.BadZipFile:
                # We will realize soon enough that the files were not extracted
                pass

            if not os.path.isfile(ili2pg_file):
                self.stderr.emit(
                    self.tr(
                        'File "{file}" not found. Please download and extract <a href="{ili2pg_url}">{ili2pg_url}</a>.'.format(
                            file=ili2pg_file,
                            ili2pg_url=ILI2PG_URL)))

        args = ["-jar", ili2pg_file]
        args += ["--import"]
        args += ["--dbhost", self.configuration.host]
        args += ["--dbusr", self.configuration.user]
        if self.configuration.password:
            args += ["--dbpwd", self.configuration.password]
        args += ["--dbdatabase", self.configuration.database]
        args += ["--dbschema", self.configuration.schema or self.configuration.database]

        #args += self.configuration.base_configuration.to_ili2db_args()

        if self.configuration.ilimodels:
            args += ['--models', self.configuration.ilimodels]

        args += [self.configuration.xtffile]

        if self.configuration.java_path:
            # A java path is configured: respect it no mather what
            java_paths = [self.configuration.java_path]
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

        self.__result = DataImporter.ERROR

        loop = QEventLoop()
        proc.finished.connect(loop.exit)
        loop.exec()

        self.process_finished.emit(proc.exitCode(), self.__result)
        return self.__result

    def stderr_ready(self, proc):
        text = bytes(proc.readAllStandardError()).decode(self.encoding)
        if not self.__done_pattern:
            self.__done_pattern = re.compile(r"Info: ...import done")
        if self.__done_pattern.search(text):
            self.__result = DataImporter.SUCCESS

        self.stderr.emit(text)

    def stdout_ready(self, proc):
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)

