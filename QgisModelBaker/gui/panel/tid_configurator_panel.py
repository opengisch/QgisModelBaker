"""
/***************************************************************************
                              -------------------
        begin                : 17.11.2023
        git sha              : :%H$
        copyright            : (C) 2023 by Dave Signer
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


from qgis.PyQt.QtWidgets import QWidget

from QgisModelBaker.gui.panel.layer_tids_panel import LayerTIDsPanel
from QgisModelBaker.gui.panel.set_sequence_panel import SetSequencePanel
from QgisModelBaker.utils import gui_utils

WIDGET_UI = gui_utils.get_ui_class("tid_configurator_panel.ui")


class TIDConfiguratorPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.layer_tids_panel = LayerTIDsPanel(self.parent)
        self.layer_tids_layout.addWidget(self.layer_tids_panel)

        self.set_sequence_panel = SetSequencePanel(self.parent)
        self.set_sequence_layout.addWidget(self.set_sequence_panel)

        self.reset_layer_tids_button.clicked.connect(self._reset_tid_configuration)

        self.qgis_project = None
        self.db_connector = None

    def setup_dialog(self, db_connector, qgis_project):
        self.qgis_project = qgis_project
        self.db_connector = db_connector
        self._reset_tid_configuration()

    def _reset_tid_configuration(self):
        self.layer_tids_panel.load_tid_config(self.qgis_project)
        self.set_sequence_panel.load_sequence(self.db_connector)

    def set_tid_configuration(self):
        self.layer_tids_panel.save_tid_config(self.qgis_project)
        self.set_sequence_panel.save_sequence(self.db_connector)
