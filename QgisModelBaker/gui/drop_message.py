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

from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog

from QgisModelBaker.libili2db.globals import DropMode
from QgisModelBaker.utils import ui

DIALOG_UI = ui.get_ui_class("drop_message.ui")


class DropMessageDialog(QDialog, DIALOG_UI):
    def __init__(self, file_name, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.info_label.setText(
            self.tr(
                "Do you want to use the Model Baker plugin to handle file {}?"
            ).format(file_name)
        )
        self.accepted.connect(lambda: self.handle_dropped_file_configuration(True))
        self.rejected.connect(lambda: self.handle_dropped_file_configuration(False))

    def handle_dropped_file_configuration(self, handle_dropped):
        settings = QSettings()
        if not self.chk_dontask.isChecked():
            settings.setValue("QgisModelBaker/drop_mode", DropMode.ASK.name)
        elif handle_dropped:
            settings.setValue("QgisModelBaker/drop_mode", DropMode.YES.name)
        else:
            settings.setValue("QgisModelBaker/drop_mode", DropMode.NO.name)
