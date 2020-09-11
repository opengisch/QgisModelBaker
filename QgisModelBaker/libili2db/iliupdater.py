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
import re

from qgis.PyQt.QtCore import pyqtSignal

from QgisModelBaker.libili2db.ili2dbconfig import UpdateDataConfiguration
from QgisModelBaker.libili2db.iliexecutable import IliExecutable


class Updater(IliExecutable):

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)

    __done_pattern = None

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)

    def _create_config(self):
        return UpdateDataConfiguration()

    def _get_done_pattern(self):
        if not self.__done_pattern:
            self.__done_pattern = re.compile(r"Info: \.\.\.update done")

        return self.__done_pattern
