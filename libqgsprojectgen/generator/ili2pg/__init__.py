# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/01/17
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

from qgis.PyQt.QtCore import QStandardPaths
import urllib.request
import zipfile
import os

ILI2PG_VERSION='3.6.1'


class Ili2Pg(object):
    def __init__(self):
        pass

    def generate(self, configuration):
        self.ensure_ili2pg_installed()

    def ensure_ili2pg_installed(self):
        ili2pg_location = QStandardPaths.locate(QStandardPaths.AppDataLocation, 'ili2pg', QStandardPaths.LocateDirectory)
        if not ili2pg_location:
            appdata_location = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not appdata_location:
                raise RuntimeError('Ili2Pg not found in app data and no writable location found in {}!'.format(QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)))
            tempfile_location = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
            filename = 'ili2pg-{}.zip'.format(ILI2PG_VERSION)
            downloaded_file = os.path.join(tempfile_location, filename)
            urllib.request.urlretrieve(
                'http://www.eisenhutinformatik.ch/interlis/ili2pg/{}'.format(filename),
                downloaded_file)

            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                zip_ref.extract(os.path.join(appdata_location, 'ili2pg'))
