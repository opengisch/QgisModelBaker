# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 25.11.2017
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
from projectgenerator.utils import get_ui_class

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem, QDialogButtonBox
from qgis.gui import QgsGui

DIALOG_UI = get_ui_class('multiple_models.ui')


class MultipleModelsDialog(QDialog, DIALOG_UI):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self);
        self.parent = parent

        self.model_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed()

        self.add_button.clicked.connect(self.add_model)
        self.remove_button.clicked.connect(self.remove_model)
        self.buttonBox.accepted.connect(self.accepted)

        self.models_line_edit.textChanged.connect(self.update_add_button_state)
        self.models_line_edit.textChanged.emit(self.models_line_edit.text())

    def add_model(self):
        model_name = self.models_line_edit.text().strip()
        if not self.model_list.findItems(model_name, Qt.MatchExactly):
            self.model_list.addItem(QListWidgetItem(model_name))
            self.models_line_edit.setText("")

    def remove_model(self):
        for item in self.model_list.selectedItems():
            self.model_list.takeItem(self.model_list.row(item))

    def get_models_string(self):
        items = [self.model_list.item(x)
                 for x in range(self.model_list.count())]
        models = ";".join([i.text().strip()
                           for i in items if i.text().strip()])
        return models

    def on_selection_changed(self):
        enable = len(self.model_list.selectedItems()) == 1
        self.remove_button.setEnabled(enable)

    def update_add_button_state(self, text):
        self.add_button.setEnabled(bool(text.strip()))
        self.add_button.setDefault(bool(text.strip()))
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(
            not bool(text.strip()))
