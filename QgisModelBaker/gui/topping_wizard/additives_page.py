# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-12-07
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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import CheckEntriesModel

PAGE_UI = gui_utils.get_ui_class("topping_wizard/additives.ui")


class AdditivesPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.setTitle(title)

        self.mapthemes_model = CheckEntriesModel()
        self.mapthemes_view.setModel(self.mapthemes_model)
        self.mapthemes_view.clicked.connect(self.mapthemes_view.model().check)
        self.mapthemes_view.space_pressed.connect(self.mapthemes_view.model().check)
        self.variables_model = CheckEntriesModel()
        self.variables_view.setModel(self.variables_model)
        self.variables_view.clicked.connect(self.variables_view.model().check)
        self.variables_view.space_pressed.connect(self.variables_view.model().check)
        self.layouts_model = CheckEntriesModel()
        self.layouts_view.setModel(self.layouts_model)
        self.layouts_view.clicked.connect(self.layouts_view.model().check)
        self.layouts_view.space_pressed.connect(self.layouts_view.model().check)

    def initializePage(self) -> None:
        maptheme_collection = QgsProject.instance().mapThemeCollection()
        self.mapthemes_model.setStringList(maptheme_collection.mapThemes())
        self.mapthemes_model.check_all(Qt.Checked)
        self.mapthemes_view.setEnabled(self.mapthemes_model.rowCount())

        variables_keys = []
        variables_keys = QgsProject.instance().customVariables().keys()
        self.variables_model.setStringList(variables_keys)
        self.variables_model.check_all(Qt.Checked)
        self.mapthemes_view.setEnabled(self.variables_model.rowCount())

        layout_manager = QgsProject.instance().layoutManager()
        layout_names = [layout.name() for layout in layout_manager.printLayouts()]
        self.layouts_model.setStringList(layout_names)
        self.layouts_model.check_all(Qt.Checked)
        self.layouts_view.setEnabled(self.layouts_model.rowCount())
        return super().initializePage()

    def validatePage(self) -> bool:
        self.topping_wizard.topping.export_settings.mapthemes = (
            self.mapthemes_model.checked_entries()
        )
        self.topping_wizard.topping.export_settings.variables = (
            self.variables_model.checked_entries()
        )
        self.topping_wizard.topping.export_settings.layouts = (
            self.layouts_model.checked_entries()
        )
        return super().validatePage()
