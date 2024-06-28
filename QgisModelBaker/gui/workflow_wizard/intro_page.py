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

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/intro.ui")


class IntroPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.workflow_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.next_id = gui_utils.PageIds.ImportSourceSelection
        self.import_button.clicked.connect(self._on_import)
        self.generate_button.clicked.connect(self._on_generate)
        self.export_button.clicked.connect(self._on_export)

    def nextId(self):
        return self.next_id

    def _on_import(self):
        self.next_id = gui_utils.PageIds.ImportSourceSelection
        self.workflow_wizard.next()

    def _on_generate(self):
        self.next_id = gui_utils.PageIds.GenerateDatabaseSelection
        self.workflow_wizard.next()

    def _on_export(self):
        self.next_id = gui_utils.PageIds.ExportDatabaseSelection
        self.workflow_wizard.next()

    def help_text(self):
        logline = self.tr(
            "You have just opened the Workflow Wizard, now you need to choose your plans..."
        )
        help_paragraphs = self.tr(
            """
        <h4 align="justify">> Choose data files and models to import or generate a new database</h4>
        <p align="justify">If you want to <b>create a physical database </b> based on an INTERLIS model, regardless of whether it is based on an ili-file or a model from the repository.</p>
        <p align="justify">Or if you want to <b>import data</b> (catalogues or user data), regardless of whether the database already exists or not.</p>
        <h4 align="justify">> Generate a QGIS Project from an existing database</h4>
        <p align="justify">If you want to select a database from which to <b>create a QGIS project</b>.</p>
        <h4 align="justify">> Export data from an existing database</h4>
        <p align="justify">If you want to <b>export data</b> to an XTF file.</p>
        """
        )
        docutext = self.tr(
            'Find more information about the <b>workflow wizard</b> in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/">documentation</a>...'
        )
        return logline, help_paragraphs, docutext
