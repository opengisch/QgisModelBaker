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


from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.tid_configurator_panel import TIDConfiguratorPanel
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/tid_configuration.ui")


class TIDConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setFinalPage(True)
        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.tid_configurator_panel = TIDConfiguratorPanel(self.workflow_wizard)
        self.tid_configurator_layout.addWidget(self.tid_configurator_panel)

        self.set_layer_tids_and_sequence_button.clicked.connect(
            self._set_tid_configuration
        )

        self.configuration = None

    def set_configuration(self, configuration):
        self.configuration = configuration
        db_connector = db_utils.get_db_connector(self.configuration)
        self.tid_configurator_panel.setup_dialog(QgsProject.instance(), db_connector)

    def _set_tid_configuration(self):
        self.progress_bar.setValue(0)
        # we store the settings to project and db
        result, message = self.tid_configurator_panel.set_tid_configuration()
        if result:
            self.workflow_wizard.log_panel.print_info(
                self.tr("Stored TID configurations to current project")
            )
            self.workflow_wizard.log_panel.print_info(
                self.tr("Stored the sequence value to current database")
            )
            self.progress_bar.setValue(100)
            self.setStyleSheet(gui_utils.SUCCESS_STYLE)
        else:
            self.workflow_wizard.log_panel.print_info(message)
            self.progress_bar.setValue(0)
            self.setStyleSheet(gui_utils.ERROR_STYLE)
