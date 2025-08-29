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

from QgisModelBaker.gui.panel.tid_configurator_panel import TIDConfiguratorPanel
from QgisModelBaker.libs.modelbaker.utils.globals import LogLevel
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

        self.configuration = None

    def set_configuration(self, configuration):
        self.tid_configurator_panel.setup_dialog(QgsProject.instance(), configuration)

    def _set_tid_configuration(self):
        self.workflow_wizard.busy(
            self,
            True,
            self.tr("Storing OID configurations"),
        )
        # we store the settings to project and db
        result, message = self.tid_configurator_panel.set_tid_configuration()
        if result:
            self.workflow_wizard.log_panel.print_info(
                self.tr("Stored OID configurations successfully.")
            )
            self.workflow_wizard.busy(self, False)
            return True
        else:
            self.workflow_wizard.log_panel.print_info(message, LogLevel.FAIL)
            self.workflow_wizard.busy(self, False)
        return False

    def validatePage(self) -> bool:
        return self._set_tid_configuration()
        return super().validatePage()

    def help_text(self):
        logline = self.tr(
            "OIDs can be a pain to fill up - let Model Baker do it for you..."
        )
        help_paragraphs = self.tr(
            """
        <p align="justify">Model Baker recognized the OID Type according to the model and proposed <b>default expressions</b>.</p>
        <p align="justify">You still can change them. In case of <b><code>STANDARDOID</code></b> you have to set your own prefix.</p>
        <h4>Reset the <code>t_id</code> value</h4>
        <p align="justify">When using <code>STANDARDOID</code> or <code>I32OID</code> we need a sequence. Here we take the one from the <code>t_id</code>.<br />
        When you change it here, be aware that you don't set it lower than a currently used <code>t_id</code>.</p>
        """
        )
        docutext = self.tr(
            'Find more information about this page in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/#8-oid-values">documentation</a> and about OID settings in general <a href="https://opengisch.github.io/QgisModelBaker/background_info/oid_tid_generator/#tid_(oid)_manager">here</a>'
        )
        return logline, help_paragraphs, docutext
