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
    """Executes an update operation on ili2db.
    """
    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)

    def _create_config(self):
        return UpdateDataConfiguration()
