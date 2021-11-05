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

import os
import re

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QEvent, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QCompleter,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionComboBox,
    QWizardPage,
)

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools
import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.gui.dataset_manager import DatasetManagerDialog
from QgisModelBaker.libili2db.ilicache import (
    IliDataCache,
    IliDataItemModel,
    MetaConfigCompleterDelegate,
)

from ...utils import ui
from ...utils.ui import LogColor

PAGE_UI = ui.get_ui_class("workflow_wizard/import_data_configuration.ui")


class DatasetComboDelegate(QStyledItemDelegate):
    def __init__(self, parent, db_connector):
        super().__init__(parent)
        self.refresh_datasets(db_connector)

    def refresh_datasets(self, db_connector):
        if db_connector:
            datasets_info = db_connector.get_datasets_info()
            self.items = [
                record["datasetname"]
                for record in datasets_info
                if record["datasetname"] != wizard_tools.CATALOGUE_DATASETNAME
            ]

    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
        return self.editor

    def setEditorData(self, editor, index):
        value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
        num = self.items.index(value) if value in self.items else 0
        editor.setCurrentIndex(num)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, int(wizard_tools.SourceModel.Roles.DATASET_NAME))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        """
        Here it paints only the lable without a StyleItem for the ComboBox, because to edit it needs multiple clicks and the behavior gets confusing.
        """
        opt = QStyleOptionComboBox()
        opt.editable = False
        opt.rect = option.rect
        value = index.data(int(Qt.DisplayRole))
        opt.currentText = value
        QApplication.style().drawControl(QStyle.CE_ComboBoxLabel, opt, painter)


class CatalogueCheckDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            value = (
                index.data(int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)) or False
            )
            model.setData(
                index, not value, int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)
            )
            return True
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        opt = QStyleOptionButton()
        opt.rect = option.rect
        value = index.data(int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)) or False
        opt.state |= QStyle.State_On if value else QStyle.State_Off
        QApplication.style().drawControl(QStyle.CE_CheckBox, opt, painter)


class ImportDataConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.workflow_wizard = parent
        self.is_complete = True
        self.basket_handling = False

        self.ilireferencedatacache = IliDataCache(
            self.workflow_wizard.import_schema_configuration.base_configuration,
            "referenceData",
        )
        self.ilireferencedata_delegate = MetaConfigCompleterDelegate()
        self._refresh_ili_referencedata_cache()
        self.ilireferencedata_line_edit.setPlaceholderText(
            self.tr("[Search referenced data files from UsabILIty Hub]")
        )
        self.ilireferencedata_line_edit.setEnabled(False)
        completer = QCompleter(
            self.ilireferencedatacache.model, self.ilireferencedata_line_edit
        )
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.ilireferencedata_delegate)
        self.ilireferencedata_line_edit.setCompleter(completer)
        self.ilireferencedata_line_edit.textChanged.emit(
            self.ilireferencedata_line_edit.text()
        )
        self.ilireferencedata_line_edit.textChanged.connect(
            self._complete_referencedata_completer
        )
        self.ilireferencedata_line_edit.punched.connect(
            self._complete_referencedata_completer
        )

        self.add_button.clicked.connect(self._add_row)
        self.remove_button.clicked.connect(self._remove_selected_rows)

        self.add_button.setEnabled(False)
        self.ilireferencedata_line_edit.textChanged.connect(
            lambda: self.add_button.setEnabled(self._valid_referencedata())
        )
        self.remove_button.setEnabled(self._valid_selection())
        self.file_table_view.clicked.connect(
            lambda: self.remove_button.setEnabled(self._valid_selection())
        )

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.remove_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

        self.workflow_wizard.import_data_file_model.sourceModel().setHorizontalHeaderLabels(
            [self.tr("Import File"), self.tr("Catalogue"), self.tr("Dataset")]
        )
        self.file_table_view.setModel(self.workflow_wizard.import_data_file_model)
        self.file_table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.file_table_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.file_table_view.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )

        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)
        self.file_table_view.resizeColumnsToContents()
        self.workflow_wizard.import_data_file_model.dataChanged.connect(
            self._update_delegates
        )

        self.db_connector = None

        self.datasetmanager_dlg = None
        self.datasetmanager_button.setCheckable(True)
        self.datasetmanager_button.clicked.connect(self._show_datasetmanager_dialog)
        self.datasetmanager_button.setIcon(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "../../images/QgisModelBaker-datasetmanager-icon.svg",
                )
            )
        )

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.completeChanged.emit()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index)
            )
        return order_list

    def setup_dialog(self, basket_handling):
        self.db_connector = db_utils.get_db_connector(
            self.workflow_wizard.import_data_configuration
        )
        self.basket_handling = basket_handling

        if self.basket_handling:
            self._set_basket_defaults()
        else:
            self.file_table_view.setColumnHidden(1, True)
            self.file_table_view.setColumnHidden(2, True)
            self.datasetmanager_button.setHidden(True)

        self._update_ilireferencedatacache()

    def _set_basket_defaults(self):
        for row in range(self.workflow_wizard.source_model.rowCount()):
            index = self.workflow_wizard.source_model.index(row, 2)
            value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
            if not value:
                self.workflow_wizard.source_model.setData(
                    index,
                    wizard_tools.DEFAULT_DATASETNAME,
                    int(wizard_tools.SourceModel.Roles.DATASET_NAME),
                )
                is_xml = (
                    self.workflow_wizard.source_model.index(row, 0)
                    .data(int(wizard_tools.SourceModel.Roles.TYPE))
                    .lower()
                    == "xml"
                )
                self.workflow_wizard.source_model.setData(
                    self.workflow_wizard.source_model.index(row, 1),
                    is_xml,
                    int(wizard_tools.SourceModel.Roles.IS_CATALOGUE),
                )

            self.file_table_view.setItemDelegateForColumn(
                1, CatalogueCheckDelegate(self)
            )
            self.file_table_view.setItemDelegateForColumn(
                2, DatasetComboDelegate(self, self.db_connector)
            )

    def _update_ilireferencedatacache(self):
        self.ilireferencedatacache = IliDataCache(
            self.workflow_wizard.import_data_configuration.base_configuration,
            type="referenceData",
            models=";".join(self._db_modelnames()),
        )
        self.ilireferencedatacache.file_download_succeeded.connect(
            lambda dataset_id, path: self._on_referencedata_received(path)
        )
        self.ilireferencedatacache.file_download_failed.connect(
            self._on_referencedata_failed
        )
        self.ilireferencedatacache.model_refreshed.connect(
            self._update_referencedata_completer
        )
        self._refresh_ili_referencedata_cache()

    def _db_modelnames(self):
        modelnames = list()
        if self.db_connector:
            if (
                self.db_connector.db_or_schema_exists()
                and self.db_connector.metadata_exists()
            ):
                db_models = self.db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                    for modelname in regex.split(db_model["modelname"]):
                        modelnames.append(modelname.strip())
        return modelnames

    def _refresh_ili_referencedata_cache(self):
        self.ilireferencedatacache.new_message.connect(
            self.workflow_wizard.log_panel.show_message
        )
        self.ilireferencedatacache.refresh()

    def _complete_referencedata_completer(self):
        if self.ilireferencedata_line_edit.hasFocus():
            if not self.ilireferencedata_line_edit.text():
                self.ilireferencedata_line_edit.completer().setCompletionMode(
                    QCompleter.UnfilteredPopupCompletion
                )
                self.ilireferencedata_line_edit.completer().complete()
            else:
                match_contains = (
                    self.ilireferencedata_line_edit.completer()
                    .completionModel()
                    .match(
                        self.ilireferencedata_line_edit.completer()
                        .completionModel()
                        .index(0, 0),
                        Qt.DisplayRole,
                        self.ilireferencedata_line_edit.text(),
                        -1,
                        Qt.MatchContains,
                    )
                )
                if len(match_contains) > 1:
                    self.ilireferencedata_line_edit.completer().setCompletionMode(
                        QCompleter.PopupCompletion
                    )
                    self.ilireferencedata_line_edit.completer().complete()

    def _valid_referencedata(self):
        match_contains = (
            self.ilireferencedata_line_edit.completer()
            .completionModel()
            .match(
                self.ilireferencedata_line_edit.completer()
                .completionModel()
                .index(0, 0),
                Qt.DisplayRole,
                self.ilireferencedata_line_edit.text(),
                -1,
                Qt.MatchExactly,
            )
        )
        return len(match_contains) == 1

    def _valid_selection(self):
        return bool(self.file_table_view.selectedIndexes())

    def _update_referencedata_completer(self, rows):
        self.ilireferencedata_line_edit.completer().setModel(
            self.ilireferencedatacache.model
        )
        self.ilireferencedata_line_edit.setEnabled(bool(rows))

    def _add_row(self):
        self._get_referencedata()

    def _get_referencedata(self):
        matches = self.ilireferencedatacache.model.match(
            self.ilireferencedatacache.model.index(0, 0),
            Qt.DisplayRole,
            self.ilireferencedata_line_edit.text(),
            1,
            Qt.MatchExactly,
        )
        if matches:
            model_index = matches[0]
            repository = self.ilireferencedatacache.model.data(
                model_index, int(IliDataItemModel.Roles.ILIREPO)
            )
            url = self.ilireferencedatacache.model.data(
                model_index, int(IliDataItemModel.Roles.URL)
            )
            path = self.ilireferencedatacache.model.data(
                model_index, int(IliDataItemModel.Roles.RELATIVEFILEPATH)
            )
            dataset_id = self.ilireferencedatacache.model.data(
                model_index, int(IliDataItemModel.Roles.ID)
            )
            # disable the next buttton
            self.setComplete(False)
            if path:
                self.ilireferencedatacache.download_file(
                    repository, url, path, dataset_id
                )
            else:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("File not specified for metaconfig with id {}.").format(
                        dataset_id
                    ),
                    LogColor.COLOR_TOPPING,
                )

    def _on_referencedata_received(self, path):
        self.workflow_wizard.log_panel.print_info(
            self.tr("Referenced transfer file successfully downloaded: {}").format(
                path
            ),
            LogColor.COLOR_TOPPING,
        )
        if self.workflow_wizard.add_source(path) and self.basket_handling:
            self._set_basket_defaults()
        self.ilireferencedata_line_edit.clearFocus()
        self.ilireferencedata_line_edit.clear()
        self.setComplete(True)

    def _on_referencedata_failed(self, dataset_id, error_msg):
        self.workflow_wizard.log_panel.print_info(
            self.tr("Download of referenced transfer file failed: {}.").format(
                error_msg
            ),
            LogColor.COLOR_TOPPING,
        )
        # enable the next buttton
        self.setComplete(True)

    def _remove_selected_rows(self):
        indices = self.file_table_view.selectionModel().selectedIndexes()
        source_indices = [
            self.file_table_view.model().mapToSource(selected_index)
            for selected_index in indices
        ]
        self.workflow_wizard.source_model.remove_sources(source_indices)
        self.remove_button.setEnabled(self._valid_selection())

    def _update_delegates(self, top_left):
        if top_left.column() == 1:
            self.file_table_view.setItemDelegateForColumn(
                2, DatasetComboDelegate(self, self.db_connector)
            )

    def _show_datasetmanager_dialog(self):
        if self.datasetmanager_dlg:
            self.datasetmanager_dlg.reject()
        else:
            self.datasetmanager_dlg = DatasetManagerDialog(
                self.workflow_wizard.iface, self, True
            )
            self.datasetmanager_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.datasetmanager_dlg.setWindowFlags(
                self.datasetmanager_dlg.windowFlags() | Qt.Tool
            )
            self.datasetmanager_dlg.show()
            self.datasetmanager_dlg.finished.connect(
                self._datasetmanager_dialog_finished
            )
            self.datasetmanager_button.setChecked(True)

    def _datasetmanager_dialog_finished(self):
        self.datasetmanager_button.setChecked(False)
        self.datasetmanager_dlg = None
        self.file_table_view.setItemDelegateForColumn(
            2, DatasetComboDelegate(self, self.db_connector)
        )
