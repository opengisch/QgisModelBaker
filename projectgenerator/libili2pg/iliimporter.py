import subprocess
import os

import re

from qgis.PyQt.QtCore import QObject, pyqtSignal

class Configuration(object):
    def __init__(self):
        self.host = ''
        self.user = ''
        self.database = ''
        self.schema = ''
        self.password = ''
        self.ilifile = ''

class Importer(QObject):
    SUCCESS = 0
    # TODO: Insert more codes?
    ERROR = 1000

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.filename = None
        self.configuration = Configuration()

    def run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))

        ili2pg_file = os.path.join(dir_path, 'bin', 'ili2pg.jar')
        if not os.path.isfile(ili2pg_file):
            self.stderr.emit(
                'File "{}" not found. Please download and extract http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-3.6.2.zip.'.format(
                    ili2pg_file))
            os.mkdir(os.path.join(dir_path, 'bin'))

        args = ["java"]
        args += ["-jar", ili2pg_file]
        args += ["--schemaimport"]
        args += ["--dbhost", self.configuration.host]
        args += ["--dbusr", self.configuration.user]
        if self.configuration.password:
            args += ["--dbpwd", self.configuration.password]
        args += ["--dbdatabase", self.configuration.database]
        args += ["--dbschema", self.configuration.schema or self.configuration.database]
        args += ["--importTid"]
        args += ["--nameByTopic"]
        args += ["--createEnumTabs"]
        args += ["--createEnumColAsItfCode"]
        args += ["--createNumChecks"]
        args += ["--smart1Inheritance"]
        args += ["--coalesceMultiSurface"]
        args += ["--createGeomIdx"]
        args += ["--createFk"]
        args += [self.configuration.ilifile]

        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )

        self.process_started.emit(' '.join(proc.args))

        done_pattern = re.compile(r"Info: ...done")

        result = Importer.ERROR
        finished = False
        while not finished:
            try:
                output = proc.communicate(timeout=2)
                self.stdout.emit(output[1].decode())
                self.stderr.emit(output[0].decode())
                if done_pattern.search(output[1].decode()):
                    result = Importer.SUCCESS
                finished = True
            except subprocess.TimeoutExpired:
                pass

        self.process_finished.emit(proc.returncode, result)
