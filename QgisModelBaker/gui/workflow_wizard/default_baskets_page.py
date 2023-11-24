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

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.basket_panel import BasketPanel
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.globals import DEFAULT_DATASETNAME
from QgisModelBaker.utils.gui_utils import LogColor

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/default_baskets.ui")


class DefaultBasketsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.baskets_panel = BasketPanel(self)
        self.baskets_layout.addWidget(self.baskets_panel)

        self.create_default_baskets_button.clicked.connect(self._create_default_baskets)
        self.skip_button.clicked.connect(self._skip)

        self.db_connector = None
        self.is_complete = False

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.create_default_baskets_button.setDisabled(complete)
        self.skip_button.setDisabled(complete)
        self.baskets_panel.setDisabled(complete)
        self.completeChanged.emit()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def restore_configuration(self, configuration):
        self.db_connector = db_utils.get_db_connector(configuration)
        self.baskets_panel.load_basket_config(self.db_connector, DEFAULT_DATASETNAME)

    def _create_default_baskets(self):
        self.progress_bar.setValue(0)
        # we store the settings to the db
        feedbacks = self.baskets_panel.save_basket_config(
            self.db_connector, DEFAULT_DATASETNAME
        )
        success = True
        for feedback in feedbacks:
            if feedback[0]:
                # positive
                self.workflow_wizard.log_panel.print_info(
                    feedback[1], LogColor.COLOR_INFO
                )
            else:
                # negative
                self.workflow_wizard.log_panel.print_info(
                    feedback[1], LogColor.COLOR_FAIL
                )
                success = False

        if success:
            self.progress_bar.setFormat(self.tr("Default baskets created!"))
            self.progress_bar.setValue(100)
            self.setStyleSheet(gui_utils.SUCCESS_STYLE)
            self.setComplete(True)
        else:
            self.workflow_wizard.log_panel.print_info(message)
            self.progress_bar.setFormat(
                self.tr(
                    "Issues occured. Skip to proceed and fix it in Dataset Manager..."
                )
            )
            self.progress_bar.setValue(0)

    def _skip(self):
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat(self.tr("SKIPPED"))
        self.progress_bar.setTextVisible(True)
        self.setStyleSheet(gui_utils.INACTIVE_STYLE)
        self.setComplete(True)
