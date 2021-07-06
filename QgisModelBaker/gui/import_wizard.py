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

from qgis.PyQt.QtWidgets import QWizard

from QgisModelBaker.gui.intro_page import IntroPage
from QgisModelBaker.gui.import_source_selection_page import ImportSourceSeletionPage


class ImportWizard (QWizard):

    Page_Intro = 1
    Page_ImportSourceSeletion = 2
    Page_ImportDatabaseSelection = 3
    Page_ImportSchemaConfiguration = 4
    Page_ImportDataConfigurtation = 5

    def __init__(self, base_config, parent=None):
        QWizard.__init__(self)

        self.setPage(self.Page_Intro, IntroPage(self))
        self.setPage(self.Page_ImportSourceSeletion, ImportSourceSeletionPage(base_config))
        #self.setPage(self.Page_ImportDatabaseSelection, ImportDatabaseSelectionPage())
        #self.setPage(self.Page_ImportSchemaConfiguration, ImportSchemaConfigurationPage())
        #self.setPage(self.Page_ImportDataConfigurtation, ImportDataConfigurtationPage())

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"));
        self.setWizardStyle(QWizard.ModernStyle);