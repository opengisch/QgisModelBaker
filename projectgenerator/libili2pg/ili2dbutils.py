import os
import tempfile
import zipfile

from projectgenerator.libili2pg.ili2pg_config import ILI2PG_VERSION, ILI2PG_URL
from qgis.PyQt.QtCore import QCoreApplication

from projectgenerator.utils.qt_utils import download_file, NetworkError


def get_ili2pg_bin(stdout, stderr):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ili2pg_dir = 'ili2pg-{}'.format(ILI2PG_VERSION)

    ili2pg_file = os.path.join(dir_path, 'bin', ili2pg_dir, 'ili2pg.jar')
    if not os.path.isfile(ili2pg_file):
        try:
            os.mkdir(os.path.join(dir_path, 'bin'))
        except FileExistsError:
            pass

        tmpfile = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)

        stdout.emit(QCoreApplication.translate('ili2dbutils', 'Downloading ili2pg version {}…'.format(ILI2PG_VERSION)))

        try:
            download_file(ILI2PG_URL, tmpfile.name, on_progress=lambda received, total: stdout.emit('.'))
        except NetworkError as e:
            stderr.emit(
                QCoreApplication.translate('ili2dbutils',
                    'Could not download ili2pg\n\n  Error: {error}\n\nFile "{file}" not found. Please download and extract <a href="{ili2pg_url}">{ili2pg_url}</a>'.format(
                        ili2pg_url=ILI2PG_URL,
                        error=e.msg,
                        file=ili2pg_file)
                )
            )
            return None

        try:
            with zipfile.ZipFile(tmpfile.name, "r") as z:
                z.extractall(os.path.join(dir_path, 'bin'))
        except zipfile.BadZipFile:
            # We will realize soon enough that the files were not extracted
            pass

        if not os.path.isfile(ili2pg_file):
            stderr.emit(
                QCoreApplication.translate('ili2dbutils',
                    'File "{file}" not found. Please download and extract <a href="{ili2pg_url}">{ili2pg_url}</a>.'.format(
                        file=ili2pg_file,
                        ili2pg_url=ILI2PG_URL)))
            return None

    return ili2pg_file