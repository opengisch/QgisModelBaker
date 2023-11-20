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

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.layer_tids_panel import LayerTIDsPanel
from QgisModelBaker.gui.panel.set_sequence_panel import SetSequencePanel
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
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

    def setup_dialog(self, qgis_project, db_connector=None):
        self.qgis_project = qgis_project

        if db_connector:
            self.db_connector = db_connector
        else:
            # getting the data source of the first layer in the layer tree
            first_tree_layer = qgis_project.layerTreeRoot().findLayers()[0]
            if first_tree_layer:
                configuration = Ili2DbCommandConfiguration()
                source_provider = first_tree_layer.layer().dataProvider()
                valid, mode = db_utils.get_configuration_from_sourceprovider(
                    source_provider, configuration
                )
                if valid:
                    configuration.tool = mode
                    self.db_connector = db_utils.get_db_connector(configuration)

        self._reset_tid_configuration()

    def _reset_tid_configuration(self):
        self.layer_tids_panel.load_tid_config(self.qgis_project)
        self.set_sequence_panel.load_sequence(self.db_connector)

    def set_tid_configuration(self):
        result, message = self.set_sequence_panel.save_sequence(self.db_connector)
        # only set the project settings when the sequence part succeeds (or is not performed)
        if result:
            self.layer_tids_panel.save_tid_config(self.qgis_project)
            return True, message
        return False, message
