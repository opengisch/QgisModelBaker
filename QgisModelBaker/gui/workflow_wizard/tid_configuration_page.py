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


from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.gui.panel.set_sequence_panel import SetSequencePanel
from QgisModelBaker.gui.panel.tid_config_panel import TIDConfigPanel
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

        self.tid_config_panel = TIDConfigPanel(self.workflow_wizard)
        self.tid_config_layout.addWidget(self.tid_config_panel)

        self.set_sequence_panel = SetSequencePanel(self.workflow_wizard)
        self.set_sequence_layout.addWidget(self.set_sequence_panel)

        self.set_tid_configuration_button.clicked.connect(self._set_tid_configuration)

    def set_configuration(self, configuration):
        self.configuration = configuration

    def _set_tid_configuration(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setValue(100)
        self.setStyleSheet(gui_utils.SUCCESS_STYLE)
        self.workflow_wizard.log_panel.print_info(
            self.tr("Stored TID Configurations to current project")
        )
