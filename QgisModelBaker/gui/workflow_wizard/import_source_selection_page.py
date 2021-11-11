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


from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QCompleter, QWizardPage

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools
from QgisModelBaker.libili2db.ilicache import IliCache, ModelCompleterDelegate
from QgisModelBaker.utils.qt_utils import FileValidator, QValidator, make_file_selector

from ...utils import ui

PAGE_UI = ui.get_ui_class("workflow_wizard/import_source_selection.ui")


class ImportSourceSelectionPage(QWizardPage, PAGE_UI):

    ValidExtensions = wizard_tools.IliExtensions + wizard_tools.TransferExtensions

    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.file_browse_button.clicked.connect(
            make_file_selector(
                self.input_line_edit,
                title=self.tr("Open Interlis Model, Transfer or Catalogue File"),
                file_filter=self.tr(
                    "Interlis Model / Transfer / Catalogue File (*.ili *.xtf *.itf *.XTF *.ITF *.xml *.XML *.xls *.XLS *.xlsx *.XLSX)"
                ),
            )
        )

        self.fileValidator = FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions], allow_empty=False
        )

        self.ilicache = IliCache(
            self.workflow_wizard.import_schema_configuration.base_configuration
        )
        self.model_delegate = ModelCompleterDelegate()
        self._refresh_ili_models_cache()
        self.input_line_edit.setPlaceholderText(
            self.tr("[Browse for file or search model from repository]")
        )

        # very unhappy about this behavior, but okay for prototype
        self.first_time_punched = False
        self.input_line_edit.punched.connect(self._first_time_punch)

        self.source_list_view.setModel(self.workflow_wizard.source_model)
        self.add_button.clicked.connect(self._add_row)
        self.remove_button.clicked.connect(self._remove_selected_rows)

        self.add_button.setEnabled(self._valid_source())
        self.input_line_edit.textChanged.connect(
            lambda: self.add_button.setEnabled(self._valid_source())
        )
        self.remove_button.setEnabled(self._valid_selection())
        self.source_list_view.clicked.connect(
            lambda: self.remove_button.setEnabled(self._valid_selection())
        )
        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.remove_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))
        self.source_list_view.files_dropped.connect(
            self.workflow_wizard.append_dropped_files
        )

    def nextId(self):
        self._disconnect_punch_slots()
        return self.workflow_wizard.next_id()

    def _first_time_punch(self):
        # might be nicer
        self.input_line_edit.punched.disconnect(self._first_time_punch)
        self.input_line_edit.textChanged.emit(self.input_line_edit.text())
        self.input_line_edit.textChanged.connect(self._complete_models_completer)
        self.input_line_edit.punched.connect(self._complete_models_completer)
        self.first_time_punched = True

    def _disconnect_punch_slots(self):
        # might be nicer
        if self.first_time_punched:
            self.input_line_edit.textChanged.disconnect(self._complete_models_completer)
            self.input_line_edit.punched.disconnect(self._complete_models_completer)
            self.input_line_edit.punched.connect(self._first_time_punch)
            self.first_time_punched = False

    def _refresh_ili_models_cache(self):
        self.ilicache.new_message.connect(self.workflow_wizard.log_panel.show_message)
        self.ilicache.refresh()
        self.update_models_completer()

    def _complete_models_completer(self):
        if self.input_line_edit.hasFocus():
            if not self.input_line_edit.text():
                self.input_line_edit.completer().setCompletionMode(
                    QCompleter.UnfilteredPopupCompletion
                )
                self.input_line_edit.completer().complete()
            else:
                match_contains = (
                    self.input_line_edit.completer()
                    .completionModel()
                    .match(
                        self.input_line_edit.completer().completionModel().index(0, 0),
                        Qt.DisplayRole,
                        self.input_line_edit.text(),
                        -1,
                        Qt.MatchContains,
                    )
                )
                if len(match_contains) > 1:
                    self.input_line_edit.completer().setCompletionMode(
                        QCompleter.PopupCompletion
                    )
                    self.input_line_edit.completer().complete()

    def _valid_source(self):
        match_contains = (
            self.input_line_edit.completer()
            .completionModel()
            .match(
                self.input_line_edit.completer().completionModel().index(0, 0),
                Qt.DisplayRole,
                self.input_line_edit.text(),
                -1,
                Qt.MatchExactly,
            )
        )
        return (
            len(match_contains) == 1
            or self.fileValidator.validate(self.input_line_edit.text(), 0)[0]
            == QValidator.Acceptable
        )

    def _valid_selection(self):
        return bool(self.source_list_view.selectedIndexes())

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.input_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.model_delegate)
        self.input_line_edit.setCompleter(completer)

    def _add_row(self):
        source = self.input_line_edit.text()
        self.workflow_wizard.add_source(
            source, self.tr("Added by user over the wizard.")
        )
        self.input_line_edit.clearFocus()
        self.input_line_edit.clear()

    def _remove_selected_rows(self):
        indices = self.source_list_view.selectionModel().selectedIndexes()
        self.source_list_view.model().remove_sources(indices)
        self.remove_button.setEnabled(self._valid_selection())
