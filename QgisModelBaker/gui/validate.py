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


from qgis.PyQt.QtWidgets import QDockWidget

from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..utils import ui

DIALOG_UI = ui.get_ui_class("validator.ui")


class ValidateDock(QDockWidget, DIALOG_UI):
    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.db_simple_factory = DbSimpleFactory()
        # QgsGui.instance().enableAutoGeometryRestore(self)
