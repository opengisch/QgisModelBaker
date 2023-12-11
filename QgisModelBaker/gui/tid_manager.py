"""
/***************************************************************************
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

from qgis.core import QgsMapLayer, QgsProject
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from QgisModelBaker.gui.panel.tid_configurator_panel import TIDConfiguratorPanel
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("tid_manager.ui")


class TIDManagerDialog(QDialog, DIALOG_UI):
    def __init__(self, iface, parent=None, base_config=None):

        QDialog.__init__(self, parent)
        self.iface = iface
        self._close_editing()
        self.parent = parent
        self.base_config = base_config

        self.setupUi(self)

        self.tid_configurator_panel = TIDConfiguratorPanel(
            self.parent, self.base_config
        )
        self.tid_configurator_layout.addWidget(self.tid_configurator_panel)

        self.buttonBox.accepted.connect(self._accepted)
        self.buttonBox.rejected.connect(self._rejected)

        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.tid_configurator_panel.setup_dialog(QgsProject.instance())

    def _close_editing(self):
        editable_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.iface.vectorLayerTools().stopEditing(layer)
                if layer.isEditable():
                    editable_layers.append(layer)
        if editable_layers:
            # in case it could not close it automatically
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Warning)
            warning_title = self.tr("Layers still editable")
            warning_box.setWindowTitle(warning_title)
            warning_box.setText(
                self.tr(
                    "You still have layers in edit mode.\nIn case you modify the sequence in the database of those layers, it could lead to database locks.\nEditable layers are:\n - {}"
                ).format("\n - ".join([layer.name() for layer in editable_layers]))
            )
            warning_box.exec_()

    def _accepted(self):
        result, message = self.tid_configurator_panel.set_tid_configuration()
        if not result:
            error_box = QMessageBox(self)
            error_box.setIcon(QMessageBox.Critical)
            warning_title = self.tr("Problems on setting T_Id sequence.")
            error_box.setWindowTitle(warning_title)
            error_box.setText(message)
            error_box.exec_()
        else:
            self.close()

    def _rejected(self):
        self.close()
