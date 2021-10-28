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

from enum import IntEnum

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QValidator
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools
from QgisModelBaker.utils.qt_utils import (
    FileValidator,
    Validators,
    make_save_file_selector,
)

from ...utils import ui

PAGE_UI = ui.get_ui_class("workflow_wizard/export_data_configuration.ui")


class ExportDataConfigurationPage(QWizardPage, PAGE_UI):
    ValidExtensions = wizard_tools.TransferExtensions

    class FilterMode(IntEnum):
        NO_FILTER = 1
        MODEL = 2
        DATASET = 3
        BASKET = 4

    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.workflow_wizard = parent
        self.is_complete = False

        self.xtf_file_browse_button.clicked.connect(
            make_save_file_selector(
                self.xtf_file_line_edit,
                title=self.tr("Save in XTF Transfer File"),
                file_filter=self.tr(
                    "XTF Transfer File (*.xtf *XTF);;Interlis 1 Transfer File (*.itf *ITF);;XML (*.xml *XML);;GML (*.gml *GML)"
                ),
                extension=".xtf",
                extensions=["." + ext for ext in self.ValidExtensions],
            )
        )

        self.validators = Validators()

        fileValidator = FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions],
            allow_non_existing=True,
        )

        self.xtf_file_line_edit.setValidator(fileValidator)
        self.xtf_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.connect(self._set_current_export_target)
        self.xtf_file_line_edit.textChanged.emit(self.xtf_file_line_edit.text())

        self.filter_combobox.addItem(
            self.tr("Everything"), ExportDataConfigurationPage.FilterMode.NO_FILTER
        )
        self.filter_combobox.addItem(
            self.tr("Models"), ExportDataConfigurationPage.FilterMode.MODEL
        )
        self.filter_combobox.addItem(
            self.tr("Datasets"), ExportDataConfigurationPage.FilterMode.DATASET
        )
        self.filter_combobox.addItem(
            self.tr("Baskets"), ExportDataConfigurationPage.FilterMode.BASKET
        )

        self.filter_combobox.currentIndexChanged.connect(self._filter_changed)

        self.export_models_checkbox.setCheckState(Qt.Checked)
        self.export_models_checkbox.stateChanged.connect(self._select_all_models)
        self.workflow_wizard.export_models_model.dataChanged.connect(
            lambda: self._set_models_checkbox()
        )
        self.export_models_view.setModel(self.workflow_wizard.export_models_model)
        self.export_models_view.clicked.connect(
            self.workflow_wizard.export_models_model.check
        )
        self.export_models_view.space_pressed.connect(
            self.workflow_wizard.export_models_model.check
        )

        self.export_datasets_checkbox.setCheckState(Qt.Checked)
        self.export_datasets_checkbox.stateChanged.connect(self._select_all_datasets)
        self.workflow_wizard.export_datasets_model.dataChanged.connect(
            lambda: self._set_datasets_checkbox()
        )
        self.export_datasets_view.setModel(self.workflow_wizard.export_datasets_model)
        self.export_datasets_view.clicked.connect(
            self.workflow_wizard.export_datasets_model.check
        )
        self.export_datasets_view.space_pressed.connect(
            self.workflow_wizard.export_datasets_model.check
        )

        self.export_baskets_checkbox.setCheckState(Qt.Checked)
        self.export_baskets_checkbox.stateChanged.connect(self._select_all_baskets)
        self.workflow_wizard.export_baskets_model.dataChanged.connect(
            lambda: self._set_baskets_checkbox()
        )
        self.export_baskets_view.setModel(self.workflow_wizard.export_baskets_model)
        self.export_baskets_view.clicked.connect(
            self.workflow_wizard.export_baskets_model.check
        )
        self.export_baskets_view.space_pressed.connect(
            self.workflow_wizard.export_baskets_model.check
        )

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        if self.is_complete != complete:
            self.is_complete = complete
            self.completeChanged.emit()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def setup_dialog(self, basket_handling):
        self.export_datasets_label.setHidden(not basket_handling)
        self.export_datasets_checkbox.setHidden(not basket_handling)
        self.export_datasets_view.setHidden(not basket_handling)

    def _filter_changed(self):
        self.filter_combobox.currentData()

    def _set_current_export_target(self, text):
        self.setComplete(
            self.xtf_file_line_edit.validator().validate(text, 0)[0]
            == QValidator.Acceptable
        )
        self.workflow_wizard.current_export_target = text

    def _select_all_models(self, state):
        if state != Qt.PartiallyChecked:
            self.workflow_wizard.export_models_model.check_all(state)

    def _set_models_checkbox(self):
        self.export_models_checkbox.setCheckState(
            self._evaluated_check_state(self.workflow_wizard.export_models_model)
        )

    def _select_all_datasets(self, state):
        if state != Qt.PartiallyChecked:
            self.workflow_wizard.export_datasets_model.check_all(state)

    def _set_datasets_checkbox(self):
        self.export_datasets_checkbox.setCheckState(
            self._evaluated_check_state(self.workflow_wizard.export_datasets_model)
        )

    def _select_all_baskets(self, state):
        if state != Qt.PartiallyChecked:
            self.workflow_wizard.export_baskets_model.check_all(state)

    def _set_baskets_checkbox(self):
        self.export_baskets_checkbox.setCheckState(
            self._evaluated_check_state(self.workflow_wizard.export_baskets_model)
        )

    def _evaluated_check_state(self, model):
        nbr_of_checked = len(model.checked_entries())
        if nbr_of_checked:
            if nbr_of_checked == model.rowCount():
                return Qt.Checked
            return Qt.PartiallyChecked
        return Qt.Unchecked
