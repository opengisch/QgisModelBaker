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
import pathlib


from QgisModelBaker.libili2db.ilicache import (
    IliCache, 
    ModelCompleterDelegate
)

from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    Validators,
    FileValidator,
    NonEmptyStringValidator,
    OverrideCursor
)

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon,
    QColor,
    QDesktopServices,
    QValidator,
    QPixmap
)

from qgis.PyQt.QtWidgets import (
    QCompleter
)

from qgis.PyQt.QtCore import (
    Qt
)

# gui stuff
from qgis.PyQt.QtWidgets import QWizardPage, QWizard, QLabel, QVBoxLayout
from qgis.PyQt.QtGui import QPixmap

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_source_selection.ui')

class SourceModel(QStandardItemModel):
    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def data(self , index , role):
        if role == Qt.DisplayRole:
            if QStandardItemModel.data(self, index, int(SourceModel.Roles.TYPE)) != 'model':
                return self.tr('{} ({})'.format(QStandardItemModel.data(self, index, int(SourceModel.Roles.NAME)), QStandardItemModel.data(self, index, int(SourceModel.Roles.PATH))))
        return QStandardItemModel.data(self, index, role)

    def add_source(self, name, type, path):
        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(QIcon(os.path.join(os.path.dirname(__file__), f'../images/file_types/{type}.png')), Qt.DecorationRole)
        self.appendRow(item)
    
    def remove_sources(self, indices):
        for index in sorted(indices):
            self.removeRow(index.row()) 

class ImportSourceSeletionPage(QWizardPage, PAGE_UI):

    ValidExtensions = ['ili', 'xtf', 'XTF', 'itf', 'ITF', 'pdf', 'PDF', 'xml', 'XML', 'xls', 'XLS', 'xlsx', 'XLSX']

    def __init__(self, base_config, parent=None):
        QWizardPage.__init__(self, parent)
        self.setupUi(self)
        self.base_configuration = base_config

        self.setTitle(self.tr("Source Selection"))

        self.file_browse_button.clicked.connect( make_file_selector(self.input_line_edit, title=self.tr('Open Interlis Model, Transfer or Catalogue File'), file_filter=self.tr('Interlis Model File (*.ili);;Transfer File (*.xtf *.itf *.XTF *.ITF);;Catalogue File (*.xml *.XML *.xls *.XLS *.xlsx *.XLSX)')))
        
        # self.validators = Validators()
        # fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_empty=True)
        # self.input_line_edit.setValidator(fileValidator)
        # self.input_line_edit.textChanged.connect(self.validators.validate_line_edits)

        self.ilicache = IliCache(self.base_configuration)
        self.model_delegate = ModelCompleterDelegate()
        self.refresh_ili_models_cache()
        self.input_line_edit.setPlaceholderText(self.tr('[Browse for file or search model from repository]'))

        self.input_line_edit.punched.connect(self.first_time_punch)

        self.model = SourceModel()
        self.source_list_view.setModel(self.model)
        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_selected_rows)

        self.remove_button.setEnabled(self.model.rowCount())
        self.model.rowsInserted.connect( lambda: self.remove_button.setEnabled(self.model.rowCount()))
        self.model.rowsRemoved.connect( lambda: self.remove_button.setEnabled(self.model.rowCount()))
        
        # self.add_button.setEnabled(False)
        # self.restore_configuration()

    def first_time_punch(self):
        # might could be nices
        self.input_line_edit.punched.disconnect(self.first_time_punch)
        self.input_line_edit.textChanged.emit( self.input_line_edit.text())
        self.input_line_edit.textChanged.connect(self.complete_models_completer)
        self.input_line_edit.punched.connect(self.complete_models_completer)

    def refresh_ili_models_cache(self):
        # self.ilicache.new_message.connect(self.show_message)
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
        indices = self.source_list_view.selectionModel().selectedRows()
        self.source_list_view.model().remove_sources(indices)
