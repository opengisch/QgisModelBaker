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
import os

from qgis.core import QgsExpressionContextUtils, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.ilitoppingmaker import IliTarget
from QgisModelBaker.libs.modelbaker.utils.qt_utils import (
    FileValidator,
    Validators,
    make_folder_selector,
    slugify,
)
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("topping_wizard/target.ui")


class TargetPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.projectname_line_edit.setPlaceholderText(
            slugify(QgsProject.instance().title() or "Topping Project")
        )
        self.owner_line_edit.setPlaceholderText(
            "mailto:{}".format(
                slugify(
                    QgsExpressionContextUtils.globalScope().variable(
                        "user_account_name"
                    )
                    or "Model Baker User"
                )
            )
        )
        self.main_folder_line_edit.setPlaceholderText(
            self.tr("Cannot be empty. Folder will be created if not existing.")
        )
        self.sub_folder_line_edit.setPlaceholderText(
            self.tr("Folder will be created if not existing.")
        )

        self.info_text_box.setStyleSheet(f"background-color: lightgray;")

        self.main_folder_browse_button.clicked.connect(
            make_folder_selector(
                self.main_folder_line_edit,
                title=self.tr("Target Folder Selection", "Open Main Target Folder"),
                parent=None,
            )
        )

        self.validators = Validators()
        self.folder_validator = FileValidator(allow_non_existing=True)
        self.main_folder_line_edit.setValidator(self.folder_validator)
        self.main_folder_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.main_folder_line_edit.textChanged.emit(self.main_folder_line_edit.text())

        self.projectname_line_edit.textChanged.connect(self._update_info_box)
        self.main_folder_line_edit.textChanged.connect(self._update_info_box)
        self.sub_folder_line_edit.textChanged.connect(self._update_info_box)

    def initializePage(self) -> None:
        return super().initializePage()

    def validatePage(self) -> bool:
        projectname = self.projectname_line_edit.text() or slugify(
            QgsProject.instance().title() or "Topping Project"
        )
        owner = self.owner_line_edit.text() or "mailto:{}".format(
            slugify(
                QgsExpressionContextUtils.globalScope().variable("user_account_name")
                or "Model Baker User"
            )
        )
        publishing_date = self.publishingdate_date_edit.date().toString(Qt.ISODate)
        version = self.version_date_edit.date().toString(Qt.ISODate)

        mainfolder = os.path.abspath(self.main_folder_line_edit.text())
        subfolder = self.sub_folder_line_edit.text()

        if not mainfolder:
            self.topping_wizard.log_panel.print_info(
                self.tr("Target Folder needs to be set."),
                gui_utils.LogColor.COLOR_FAIL,
            )
            return False
        self.topping_wizard.topping.target = IliTarget(
            projectname, mainfolder, subfolder, None, owner, publishing_date, version
        )
        self.topping_wizard.log_panel.print_info(
            self.tr("Target Object created."),
            gui_utils.LogColor.COLOR_SUCCESS,
        )
        return super().validatePage()

    def _update_info_box(self):
        mainfolder = self.main_folder_line_edit.text()
        subfolder = self.sub_folder_line_edit.text()
        projectname_slug = slugify(
            self.projectname_line_edit.text()
            or slugify(QgsProject.instance().title() or "Topping Project")
        )

        if mainfolder and subfolder:
            text = f"""{os.path.abspath(mainfolder)}/
├─ ilidata.xml
├─ {subfolder}/
    ├─ metaconfig/
    │  ├─ {projectname_slug}.ini
    ├─ qml/
    │  ├─ {projectname_slug}_name_of_the_layer.qml
    │  ├─ {projectname_slug}_name_of_another_layer.qml
    ├─ sql/
    │  ├─ the_script.sql
    ├─ etc.
            """
        elif mainfolder:
            text = f"""{os.path.abspath(mainfolder)}/
├─ ilidata.xml
├─ metaconfig/
│  ├─ {projectname_slug}.ini
├─ qml/
│  ├─ {projectname_slug}_name_of_the_layer.qml
│  ├─ {projectname_slug}_name_of_another_layer.qml
├─ sql/
│  ├─ the_script.sql
├─ etc.
            """
        else:
            text = ""
        self.info_text_box.setText(text)
