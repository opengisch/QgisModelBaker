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
import os

from PyQt5.QtCore import QSize
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox

from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import DropMode


class DopMessageModelBakerDialog(QDialog, gui_utils.get_ui_class("drop_message.ui")):
    def __init__(self, dropped_files, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setFixedSize(QSize())
        QgsGui.instance().enableAutoGeometryRestore(self)

        file_list = "\n- ".join(
            os.path.basename(path)
            for path in dropped_files
            if dropped_files.index(path) < 10
        )
        self.info_label.setText(
            self.tr(
                "Do you want to use the Model Baker plugin to handle the following {}?\n- {} {}"
            ).format(
                self.tr("files") if len(dropped_files) > 1 else self.tr("file"),
                file_list,
                self.tr("\nand {} more...").format(len(dropped_files) - 10)
                if len(dropped_files) > 10
                else "",
            )
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


class DropMessageQuickDialog(QDialog, gui_utils.get_ui_class("drop_quick_message.ui")):
    def __init__(self, dropped_files, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setFixedSize(QSize())
        QgsGui.instance().enableAutoGeometryRestore(self)

        quick_button = self.button_box.addButton(
            self.tr("Quickly visualize"), QDialogButtonBox.ActionRole
        )
        wizard_button = self.button_box.addButton(
            self.tr("Go to Model Baker Wizard"), QDialogButtonBox.ActionRole
        )

        file_list = "\n- ".join(
            os.path.basename(path)
            for path in dropped_files
            if dropped_files.index(path) < 10
        )
        self.info_label.setText(
            self.tr(
                "Would you like to quickly visualize {}, or would you prefer to create a structured database using the Model Baker Wizard?\n- {} {}"
            ).format(
                self.tr("these files")
                if len(dropped_files) > 1
                else self.tr("this file"),
                file_list,
                self.tr("\nand {} more...").format(len(dropped_files) - 10)
                if len(dropped_files) > 10
                else "",
            )
        )
        quick_button.clicked.connect(self.accept)
        quick_button.clicked.connect(
            lambda: self.handle_dropped_file_quick_configuration()
        )
        wizard_button.clicked.connect(self.reject)
        wizard_button.clicked.connect(
            lambda: self.handle_dropped_file_quick_configuration()
        )

    def handle_dropped_file_quick_configuration(self):
        settings = QSettings()
        settings.setValue(
            "QgisModelBaker/open_wizard_always", self.chk_alwayswizard.isChecked()
        )
