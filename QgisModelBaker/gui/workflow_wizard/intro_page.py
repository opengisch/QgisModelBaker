# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 06.07.2021
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


from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools

from ...utils import ui

PAGE_UI = ui.get_ui_class("workflow_wizard/intro.ui")


class IntroPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.workflow_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.next_id = wizard_tools.PageIds.ImportSourceSeletion
        self.import_button.clicked.connect(self._on_import)
        self.generate_button.clicked.connect(self._on_generate)
        self.export_button.clicked.connect(self._on_export)

    def nextId(self):
        return self.next_id

    def _on_import(self):
        self.next_id = wizard_tools.PageIds.ImportSourceSeletion
        self.workflow_wizard.next()

    def _on_generate(self):
        self.next_id = wizard_tools.PageIds.GenerateDatabaseSelection
        self.workflow_wizard.next()

    def _on_export(self):
        self.next_id = wizard_tools.PageIds.ExportDatabaseSelection
        self.workflow_wizard.next()
