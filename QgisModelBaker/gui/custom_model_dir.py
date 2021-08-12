# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 11.08.2017
        git sha              : :%H$
        copyright            : (C) 2017 by Sergio Ramírez (BSF-Swissphoto)
        email                : seralra96@gmail.com
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
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem

from QgisModelBaker.utils.qt_utils import selectFolder
from QgisModelBaker.utils.ui import get_ui_class

DIALOG_UI = get_ui_class("custom_model_dir.ui")


class CustomModelDirDialog(QDialog, DIALOG_UI):
    def __init__(self, current_paths, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.parent = parent

        paths = current_paths.split(";")
        self.model_dir_list.addItems([path for path in paths if path.strip()] or [""])
        for i in range(self.model_dir_list.count()):
            self.set_flags(self.model_dir_list.item(i))

        self.model_dir_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed()

        self.add_button.clicked.connect(self.add_model_dir)
        self.remove_button.clicked.connect(self.remove_model_dir)
        self.browse_button.clicked.connect(self.browse_dir)
        self.buttonBox.accepted.connect(self.accepted)

    def add_model_dir(self):
        item = QListWidgetItem()
        self.set_flags(item)
        self.model_dir_list.addItem(item)
        self.model_dir_list.setCurrentItem(item)
        self.browse_dir()

    def remove_model_dir(self):
        for item in self.model_dir_list.selectedItems():
            self.model_dir_list.takeItem(self.model_dir_list.row(item))

    def accepted(self):
        items = [
            self.model_dir_list.item(x) for x in range(self.model_dir_list.count())
        ]
        new_paths = ";".join([i.text().strip() for i in items if i.text().strip()])
        self.parent.custom_model_directories_line_edit.setText(new_paths)

    def browse_dir(self):
        selectFolder(
            self.model_dir_list.currentItem(),
            title=QCoreApplication.translate(
                "QgisModelBaker", "Open Folder with ili Models"
            ),
            parent=None,
        )

    def set_flags(self, item):
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)

    def on_selection_changed(self):
        enable = len(self.model_dir_list.selectedItems()) == 1
        self.browse_button.setEnabled(enable)
        self.remove_button.setEnabled(enable)
