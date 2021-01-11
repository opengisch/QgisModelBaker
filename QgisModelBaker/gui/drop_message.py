# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 27.08.2020
        git sha              : :%H$
        copyright            : (C) 2020 by Dave Signer
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
from QgisModelBaker.utils import get_ui_class
from QgisModelBaker.libili2db.globals import DropMode

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtCore import QSettings
from qgis.gui import QgsGui

DIALOG_UI = get_ui_class('drop_message.ui')

class DropMessageDialog(QDialog, DIALOG_UI):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.accepted.connect(lambda: self.handle_dropped_file_configuration(True))
        self.rejected.connect(lambda: self.handle_dropped_file_configuration(False))

    def handle_dropped_file_configuration(self, handle_dropped):
        settings = QSettings()
        if not self.chk_dontask.isChecked():
            settings.setValue('QgisModelBaker/drop_mode', DropMode.ask)
        elif handle_dropped:
            settings.setValue('QgisModelBaker/drop_mode', DropMode.yes)
        else:
            settings.setValue('QgisModelBaker/drop_mode', DropMode.no)
