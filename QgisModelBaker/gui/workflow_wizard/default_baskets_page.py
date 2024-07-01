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
from QgisModelBaker.utils.gui_utils import LogLevel

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
                self.workflow_wizard.log_panel.print_info(feedback[1], LogLevel.INFO)
            else:
                # negative
                self.workflow_wizard.log_panel.print_info(feedback[1], LogLevel.FAIL)
                success = False

        if success:
            self.progress_bar.setFormat(self.tr("Default baskets created!"))
            self.progress_bar.setValue(100)
            self.setStyleSheet(gui_utils.SUCCESS_STYLE)
            self.create_default_baskets_button.setDisabled(True)
            self.skip_button.setDisabled(True)
            self.baskets_panel.setDisabled(True)
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
        self.create_default_baskets_button.setDisabled(True)
        self.skip_button.setDisabled(True)
        self.baskets_panel.setDisabled(True)
        self.setComplete(True)

    def help_text(self):
        logline = self.tr(
            "Honestly, I don't know if you want to create the baskets or skip this step.<br />See below..."
        )
        help_paragraphs = self.tr(
            """
        <p align="justify">If you plan to <b>import data later</b> (from <code>xtf</code> or <code>xml</code>), the necessary baskets will be created on import anyway.</p>
        <p align="justify">However, if you have no data to import and want to <b>collect the data fresh</b>, you may need to create the baskets.</p>
        <p align="justify">The checked baskets are those that Model Baker has identified as <i>relevant</i> according to the recognised <a href="https://opengisch.github.io/QgisModelBaker/background_info/extended_models_optimization/#basket-handling">inheritance</a>.</p>
        """
        )
        docutext = self.tr(
            'Find more information about this in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/#5-create-baskets">documentation</a> and about baskets and datasets in general <a href="https://opengisch.github.io/QgisModelBaker/background_info/basket_handling/">here</a>...'
        )
        return logline, help_paragraphs, docutext
