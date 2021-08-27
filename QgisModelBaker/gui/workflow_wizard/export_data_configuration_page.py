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

from enum import Enum
import os
import re
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QCheckBox, QGridLayout, QToolButton
from PyQt5.uic.uiparser import _parse_alignment

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QHeaderView,
    QStyledItemDelegate,
    QComboBox,
    QAction,
    QWidget,
    QHBoxLayout,
    QStyle,
    QStyleOptionComboBox,
    QApplication,
    QLayout,
    QFrame,
)

from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem, QValidator

from qgis.PyQt.QtCore import Qt, QVariant

from QgisModelBaker.utils.qt_utils import (
    make_save_file_selector,
    Validators,
    FileValidator,
    OverrideCursor,
)
import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.dataset_manager import DatasetManagerDialog
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

from ...utils import get_ui_class

PAGE_UI = get_ui_class("workflow_wizard/export_data_configuration.ui")
class ExportDataConfigurationPage(QWizardPage, PAGE_UI):
    ValidExtensions = wizard_tools.TransferExtensions

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

        self.export_models_checkbox.setCheckState(Qt.Checked)
        self.export_models_checkbox.stateChanged.connect(self._select_all_models)
        self.workflow_wizard.export_models_model.dataChanged.connect(lambda: self._set_models_checkbox())
        self.export_models_view.setModel(self.workflow_wizard.export_models_model)
        self.export_models_view.clicked.connect(
            self.workflow_wizard.export_models_model.check
        )
        self.export_models_view.space_pressed.connect(
            self.workflow_wizard.export_models_model.check
        )

        self.export_datasets_checkbox.setCheckState(Qt.Checked)
        self.export_datasets_checkbox.stateChanged.connect(self._select_all_datasets)
        self.workflow_wizard.export_datasets_model.dataChanged.connect(lambda: self._set_datasets_checkbox())
        self.export_datasets_view.setModel(self.workflow_wizard.export_datasets_model)
        self.export_datasets_view.clicked.connect(
            self.workflow_wizard.export_datasets_model.check
        )
        self.export_datasets_view.space_pressed.connect(
            self.workflow_wizard.export_datasets_model.check
        )

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        if self.is_complete != complete:
            self.is_complete = complete 
            self.completeChanged.emit()

    def setup_dialog(self, basket_handling):
        self.export_datasets_label.setHidden(not basket_handling)
        self.export_datasets_checkbox.setHidden(not basket_handling)
        self.export_datasets_view.setHidden(not basket_handling)

    def _set_current_export_target(self, text):
        self.setComplete(self.xtf_file_line_edit.validator().validate(text, 0)[0] == QValidator.Acceptable)
        self.workflow_wizard.current_export_target = text

    def _select_all_models(self, state):
        if state != Qt.PartiallyChecked:
            self.workflow_wizard.export_models_model.check_all(state)

    def _set_models_checkbox(self):
        self.export_models_checkbox.setCheckState(self._evaluated_check_state(self.workflow_wizard.export_models_model))

    def _select_all_datasets(self, state):
        if state != Qt.PartiallyChecked:
            self.workflow_wizard.export_datasets_model.check_all(state)

    def _set_datasets_checkbox(self):
        self.export_datasets_checkbox.setCheckState(self._evaluated_check_state(self.workflow_wizard.export_datasets_model))

    def _evaluated_check_state(self, model):
        nbr_of_checked = len( model.checked_entries() )
        if nbr_of_checked:
            if nbr_of_checked == model.rowCount():
                return Qt.Checked
            return Qt.PartiallyChecked
        return Qt.Unchecked

    def nextId(self):
        return self.workflow_wizard.next_id()
