# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 11/11/21
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
        email                : david at opengis ch
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

from QgisModelBaker.libili2db.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.libili2db.iliexecutable import IliExecutable


class Validator(IliExecutable):
    def __init__(self, parent=None):
        super(Validator, self).__init__(parent)

    def _create_config(self):
        return ValidateConfiguration()
