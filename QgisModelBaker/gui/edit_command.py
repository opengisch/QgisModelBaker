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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem, QDialogButtonBox
from qgis.gui import QgsGui

DIALOG_UI = get_ui_class('edit_command.ui')


class EditCommandDialog(QDialog, DIALOG_UI):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr('Run'))
