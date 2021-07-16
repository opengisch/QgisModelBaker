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
import pathlib

from qgis.PyQt.QtCore import (
    Qt
)

from qgis.PyQt.QtWidgets import (
    QCompleter,
    QWizardPage
)

from QgisModelBaker.libili2db.ilicache import (
    IliCache, 
    ModelCompleterDelegate
)

from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    QValidator,
    FileValidator
)

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_source_selection.ui')

class ImportSourceSeletionPage(QWizardPage, PAGE_UI):

    ValidExtensions = ['ili', 'xtf', 'XTF', 'itf', 'ITF', 'pdf', 'PDF', 'xml', 'XML', 'xls', 'XLS', 'xlsx', 'XLSX']

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)

        self.import_wizard = parent
        
        self.setupUi(self)
        self.setFixedSize(800,600)
        self.setTitle(self.tr("Source Selection")) 

        self.file_browse_button.clicked.connect( make_file_selector(self.input_line_edit, title=self.tr('Open Interlis Model, Transfer or Catalogue File'), file_filter=self.tr('Interlis Model File (*.ili);;Transfer File (*.xtf *.itf *.XTF *.ITF);;Catalogue File (*.xml *.XML *.xls *.XLS *.xlsx *.XLSX)')))
        
        self.fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_empty=False)

        self.ilicache = IliCache(self.import_wizard.import_schema_configuration.base_configuration)
        self.model_delegate = ModelCompleterDelegate()
        self.refresh_ili_models_cache()
        self.input_line_edit.setPlaceholderText(self.tr('[Browse for file or search model from repository]'))

        # very unhappy about this behavior, but okay for prototype
        self.first_time_punched = False
        self.input_line_edit.punched.connect(self.first_time_punch)

        self.source_list_view.setModel(self.import_wizard.source_model)
        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_selected_rows)

        self.add_button.setEnabled(self.valid_source())
        self.input_line_edit.textChanged.connect(lambda: self.add_button.setEnabled(self.valid_source()))
        self.remove_button.setEnabled(self.valid_selection())
        self.source_list_view.clicked.connect(lambda: self.remove_button.setEnabled(self.valid_selection()))

    def first_time_punch(self):
        # might could be nices
        self.input_line_edit.punched.disconnect(self.first_time_punch)
        self.input_line_edit.textChanged.emit( self.input_line_edit.text())
        self.input_line_edit.textChanged.connect(self.complete_models_completer)
        self.input_line_edit.punched.connect(self.complete_models_completer)
        self.first_time_punched = True
    
    def disconnect_punch_slots(self):
        # might could be nices
        if self.first_time_punched:
            self.input_line_edit.textChanged.disconnect(self.complete_models_completer)
            self.input_line_edit.punched.disconnect(self.complete_models_completer)
            self.input_line_edit.punched.connect(self.first_time_punch)
            self.first_time_punched = False

    def refresh_ili_models_cache(self):
        self.ilicache.new_message.connect(self.import_wizard.log_panel.show_message)
        self.ilicache.refresh()
        self.update_models_completer()

    def complete_models_completer(self):
        if self.input_line_edit.hasFocus():
            if not self.input_line_edit.text():
                self.input_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
                self.input_line_edit.completer().complete()
            else:
                match_contains = self.input_line_edit.completer().completionModel().match(self.input_line_edit.completer().completionModel().index(0, 0),
                                                Qt.DisplayRole, self.input_line_edit.text(), -1, Qt.MatchContains)
                if len(match_contains) > 1:
                    self.input_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)
                    self.input_line_edit.completer().complete()

    def valid_source(self):
        match_contains = self.input_line_edit.completer().completionModel().match(self.input_line_edit.completer().completionModel().index(0, 0),
                                                Qt.DisplayRole, self.input_line_edit.text(), -1, Qt.MatchExactly)
        return len(match_contains) == 1 or self.fileValidator.validate(self.input_line_edit.text(),0)[0] == QValidator.Acceptable
    
    def valid_selection(self):
        return bool(len(self.source_list_view.selectedIndexes()))

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.input_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.model_delegate)
        self.input_line_edit.setCompleter(completer)

    def add_row(self):
        source = self.input_line_edit.text()
        if os.path.isfile(source):
            name = pathlib.Path(source).name
            type = pathlib.Path(source).suffix[1:]
            path = source
        else:
            name = source
            type = 'model'
            path = None
        self.source_list_view.model().add_source(name, type, path)
        self.input_line_edit.clearFocus()
        self.input_line_edit.clear()

    def remove_selected_rows(self):
        indices = self.source_list_view.selectionModel().selectedIndexes()
        self.source_list_view.model().remove_sources(indices)
        self.remove_button.setEnabled(self.valid_selection())

    def nextId(self):
        self.disconnect_punch_slots()
        return self.import_wizard.next_id()