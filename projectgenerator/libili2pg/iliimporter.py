import subprocess
import os

import re
import tempfile
import zipfile

from qgis.PyQt.QtCore import QObject, pyqtSignal

from projectgenerator.utils.qt_utils import download_file

ILI2PG_VERSION = '3.7.0'
ILI2PG_URL = 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(ILI2PG_VERSION)


class Configuration(object):
    def __init__(self):
        self.host = ''
        self.user = ''
        self.database = ''
        self.schema = ''
        self.password = ''
        self.ilifile = ''
        self.port = ''

    @property
    def uri(self):
        uri = []
        uri += ['dbname={}'.format(self.database)]
        uri += ['user={}'.format(self.user)]
        if self.password:
            uri += ['password={}'.format(self.password)]
        uri += ['host={}'.format(self.host)]
        if self.port:
            uri += ['port={}'.format(self.port)]

        return ' '.join(uri)


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
        return result
