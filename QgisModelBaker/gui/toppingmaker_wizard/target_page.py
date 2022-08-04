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
from QgisModelBaker.libs.modelbaker.utils.qt_utils import make_folder_selector, slugify
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/target.ui")


class TargetPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.projectname_line_edit.setPlaceholderText(
            slugify(QgsProject.instance().title()) or "dummy_project"
        )
        self.main_folder_browse_button.clicked.connect(
            make_folder_selector(
                self.main_folder_line_edit,
                title=self.tr("Target Folder Selection", "Open Main Target Folder"),
                parent=None,
            )
        )
        """
        - [ ] sub folder selection with passing main folder. whatever with selection etc.
        - [ ] fill info text edit with layer tree how it will look like...
        - [ ] is complete only when having valid values
        self.sub_folder_browse_button.clicked.connect(
            make_subfolder_selector(
                self.main_folder_line_edit.text(),
                self.sub_folder_line_edit,
                title=self.tr(
                    "Target Folder Selection", "Open Main Target Folder"
                ),
                parent=None,
            )
        )
        """

    def initializePage(self) -> None:
        return super().initializePage()

    def validatePage(self) -> bool:
        projectname = (
            self.projectname_line_edit.text()
            or slugify(QgsProject.instance().title())
            or "dummy_project"
        )
        mainfolder = self.main_folder_line_edit.text()
        subfolder = self.sub_folder_line_edit.text()

        if not mainfolder:
            self.toppingmaker_wizard.log_panel.print_info(
                self.tr("Target Folder needs to be set."),
                gui_utils.LogColor.COLOR_FAIL,
            )
            return False
        if not self.toppingmaker_wizard.topping_maker.create_target(
            projectname, mainfolder, subfolder
        ):
            self.toppingmaker_wizard.log_panel.print_info(
                self.tr("Target cannot be created."),
                gui_utils.LogColor.COLOR_FAIL,
            )
            return False
        return super().validatePage()
