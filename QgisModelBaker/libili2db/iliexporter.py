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

from qgis.PyQt.QtCore import pyqtSignal

from QgisModelBaker.libili2db.ili2dbconfig import ExportConfiguration
from QgisModelBaker.libili2db.iliexecutable import IliExecutable


class Exporter(IliExecutable):

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)

    __done_pattern = None

    def __init__(self, parent=None):
        super(Exporter, self).__init__(parent)
        self.version = 4

    def _create_config(self):
        return ExportConfiguration()

    def _get_done_pattern(self):
        if not self.__done_pattern:
            self.__done_pattern = re.compile(r"Info: ...export done")

        return self.__done_pattern

    def _get_ili2db_version(self):
        return self.version

    def _args(self, hide_password):
        args = super(Exporter, self)._args(hide_password)

        if self.version == 3 and '--export3' in args:
            args.remove('--export3')

        return args
