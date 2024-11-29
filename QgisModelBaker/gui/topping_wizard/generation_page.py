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

PAGE_UI = gui_utils.get_ui_class("topping_wizard/generation.ui")


class GenerationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.info_text_box.setStyleSheet(f"background-color: lightgray;")
        self.run_generate_button.clicked.connect(self.generate)

    def generate(self):
        result_message = ""
        ilidata_file = self.topping_wizard.topping.makeit(QgsProject.instance())
        if ilidata_file:
            self.progress_bar.setValue(100)
            result_message = self.tr("Toppings generated 🧁")
            self.info_text_box.setHtml(f"Find the ilidata.xml here:\n\n{ilidata_file}")
        else:
            self.progress_bar.setValue(0)
            result_message = self.tr("Toppings not generated 💩")
        self.progress_bar.setFormat(result_message)
        self.progress_bar.setTextVisible(True)
        self.topping_wizard.log_panel.print_info(
            result_message, gui_utils.LogColor.COLOR_SUCCESS
        )
