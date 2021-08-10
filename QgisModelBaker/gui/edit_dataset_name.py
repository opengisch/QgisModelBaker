# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 10.08.2021
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
from enum import Enum

from QgisModelBaker.utils import get_ui_class

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

DIALOG_UI = get_ui_class('edit_dataset_name.ui')


class EditDatasetDialog(QDialog, DIALOG_UI):

    class UpdateMode(Enum):
        CREATE = 1
        RENAME = 2

    def __init__(self, parent=None, db_connector = None, dataset = (None,None)):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.tid, self.datasetname= dataset
        self.db_connector = db_connector
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr('Create Dataset') if not self.datasetname else self.tr('Rename Dataset'))
        self.dataset_line_edit.setText(self.datasetname)

        self.button_box.accepted.connect(self.accepted)

    def accepted(self):
        new_dataset_name = self.dataset_line_edit.text()
        status, message = self.database_command(new_dataset_name)
        if not status:
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Critical)
            warning_title = self.tr("Rename Dataset") if self.tid else self.tr("Create Dataset")
            warning_box.setWindowTitle(warning_title)
            warning_box.setText(message)
            warning_box.exec_()

    def database_command(self, new_dataset_name):
        if self.tid:
            return self.db_connector.rename_dataset(self.tid, new_dataset_name)
        else:
            return self.db_connector.create_dataset(new_dataset_name)
