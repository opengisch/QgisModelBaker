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
from QgisModelBaker.gui.panel.set_sequence_panel import SetSequencePanel
from QgisModelBaker.gui.panel.tid_config_panel import TIDConfigPanel
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/tid_configuration.ui")


class TIDConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent
        self.qgis_project = QgsProject.instance()

        self.setupUi(self)
        self.setFinalPage(True)
        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.tid_config_panel = TIDConfigPanel(self.workflow_wizard)
        self.tid_config_layout.addWidget(self.tid_config_panel)

        self.set_sequence_panel = SetSequencePanel(self.workflow_wizard)
        self.set_sequence_layout.addWidget(self.set_sequence_panel)

        self.reset_tid_config_button.clicked.connect(self._reset_tid_configuration)
        self.set_tid_config_and_sequence_button.clicked.connect(
            self._set_tid_configuration
        )

        self.configuration = None
        self.db_connector = None

    def set_configuration(self, configuration):
        self.configuration = configuration

    def setup_dialog(self):
        self.db_connector = db_utils.get_db_connector(self.configuration)
        self._reset_tid_configuration()

    def _reset_tid_configuration(self):
        self.tid_config_panel.load_tid_config(self.qgis_project)
        self.set_sequence_panel.load_sequence(self.db_connector)

    def _set_tid_configuration(self):
        self.progress_bar.setValue(0)

        self.tid_config_panel.save_tid_config(self.qgis_project)
        self.workflow_wizard.log_panel.print_info(
            self.tr("Stored TID configurations to current project")
        )

        self.progress_bar.setValue(50)

        self.set_sequence_panel.save_sequence(self.db_connector)
        self.workflow_wizard.log_panel.print_info(
            self.tr("Stored the sequence value to current database")
        )

        self.progress_bar.setValue(100)
        self.setStyleSheet(gui_utils.SUCCESS_STYLE)
