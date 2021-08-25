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

from qgis.PyQt.QtGui import (
    QPixmap
)

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QWizard
)

from ...utils import get_ui_class

PAGE_UI = get_ui_class('workflow_wizard/intro.ui')


class IntroPage (QWizardPage, PAGE_UI):

    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setMinimumSize(600, 500)

        self.setTitle(title)

        self.next_id = self.workflow_wizard.Page_ImportSourceSeletion_Id
        self.import_button.clicked.connect(self.on_import)
        self.generate_button.clicked.connect(self.on_generate)
        self.export_button.clicked.connect(self.on_export)

    def on_import(self):
        self.next_id = self.workflow_wizard.Page_ImportSourceSeletion_Id
        self.workflow_wizard.next()

    def on_generate(self):
        self.next_id = self.workflow_wizard.Page_GenerateDatabaseSelection_Id
        self.workflow_wizard.next()

    def on_export(self):
        self.next_id = self.workflow_wizard.Page_ExportDatabaseSelection_Id
        self.workflow_wizard.next()

    def nextId(self):
        return self.next_id
