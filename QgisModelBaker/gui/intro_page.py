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

from qgis.PyQt.QtWidgets import QWizardPage, QWizard, QLabel, QVBoxLayout
from qgis.PyQt.QtGui import QPixmap

class IntroPage (QWizardPage):

    def __init__(self, wizard, parent=None ):
        QWizardPage.__init__(self, parent)

        self.wizard = wizard

        self.setTitle(self.tr("Introduction"))
        self.setPixmap(QWizard.WatermarkPixmap, QPixmap(":/images/QgisModelBaker-import.svg"))

        label = QLabel(self.tr("This wizard will generate a "))
        label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    def nextId(self):
        return self.wizard.Page_ImportSourceSeletion