# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-08-01
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/models.ui")


class ModelsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.items_view.setModel(self.toppingmaker_wizard.topping_maker.models_model)
        self.items_view.clicked.connect(self.items_view.model().check)
        self.items_view.space_pressed.connect(self.items_view.model().check)

        """
        - [ ] maybe having check all possibility
        - [ ] maybe having a refresh button when beside the layertree is changed
        - [ ] maybe the reload should not be done on initializePage because then on going back and next then it's relaoded and checked are lost.
        """

    def initializePage(self) -> None:
        self.toppingmaker_wizard.topping_maker.load_available_models(
            QgsProject.instance()
        )
        return super().initializePage()

    def validatePage(self) -> bool:
        if not self.toppingmaker_wizard.topping_maker.models_model.checked_entries:
            self.toppingmaker_wizard.log_panel.print_info(
                self.tr("At least one model should be selected."),
                gui_utils.LogColor.COLOR_FAIL,
            )
            return False
        return super().validatePage()
