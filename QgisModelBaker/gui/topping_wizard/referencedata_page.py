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
import pathlib

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.PyQt.QtWidgets import QCompleter, QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import (
    IliDataCache,
    IliDataFileCompleterDelegate,
    IliDataItemModel,
)
from QgisModelBaker.libs.modelbaker.utils.qt_utils import make_file_selector
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import SourceModel

PAGE_UI = gui_utils.get_ui_class("topping_wizard/referencedata.ui")


class ReferencedataPage(QWizardPage, PAGE_UI):

    ValidExtensions = gui_utils.TransferExtensions

    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.file_browse_button.clicked.connect(
            make_file_selector(
                self.input_line_edit,
                title=self.tr(" Transfer or Catalogue File"),
                file_filter=self.tr(
                    "Transfer / Catalogue File (*.xtf *.itf *.XTF *.ITF *.xml *.XML *.xls *.XLS *.xlsx *.XLSX)"
                ),
            )
        )

        self.fileValidator = gui_utils.FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions], allow_empty=False
        )

        self.ilireferencedatacache = IliDataCache(
            self.topping_wizard.base_config,
            "referenceData",
        )
        self.ilireferencedatacache.new_message.connect(
            self.topping_wizard.log_panel.show_message
        )

        self.ilireferencedata_delegate = IliDataFileCompleterDelegate()
        self.input_line_edit.setPlaceholderText(
            self.tr("[Search referenced data files from Repositories or Local System]")
        )
        completer = QCompleter(
            self.ilireferencedatacache.sorted_model,
            self.input_line_edit,
        )
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setModelSorting(QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.ilireferencedata_delegate)
        self.input_line_edit.setCompleter(completer)
        self.input_line_edit.textChanged.connect(self._complete_referencedata_completer)
        self.input_line_edit.punched.connect(self._complete_referencedata_completer)
        self.input_line_edit.textChanged.emit(self.input_line_edit.text())

        self.source_model = SourceModel()
        self.source_list_view.setModel(self.source_model)

        self.add_button.clicked.connect(self._add_row)
        self.remove_button.clicked.connect(self._remove_selected_rows)

        self.add_button.setEnabled(False)
        self.input_line_edit.textChanged.connect(
            lambda: self.add_button.setEnabled(self._valid_source())
        )
        self.remove_button.setEnabled(self._valid_selection())
        self.source_list_view.clicked.connect(
            lambda: self.remove_button.setEnabled(self._valid_selection())
        )

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.remove_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))
        self.source_list_view.files_dropped.connect(self.append_dropped_files)

    def initializePage(self) -> None:
        self.update_referecedata_cache_model(
            self.topping_wizard.topping.models, "referenceData"
        )
        return super().initializePage()

    def validatePage(self) -> bool:
        self.topping_wizard.topping.referencedata_paths = self._all_paths_from_model()
        if self.topping_wizard.topping.referencedata_paths:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "ReferenceData set: {referencedatapaths}".format(
                        referencedatapaths=", ".join(
                            self.topping_wizard.topping.referencedata_paths
                        )
                    )
                ),
                gui_utils.LogLevel.SUCCESS,
            )
        else:
            self.topping_wizard.log_panel.print_info(
                self.tr("No referenceData set."),
                gui_utils.LogLevel.SUCCESS,
            )
        return super().validatePage()

    def update_referecedata_cache_model(self, filter_models, type):
        # updates the model and waits for the end
        loop = QEventLoop()
        self.ilireferencedatacache.model_refreshed.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(3000)
        self.refresh_referencedata_cache(filter_models, type)
        loop.exec()
        return self.ilireferencedatacache.model

    def refresh_referencedata_cache(self, filter_models, type):
        self.ilireferencedatacache.base_configuration = self.topping_wizard.base_config
        self.ilireferencedatacache.filter_models = filter_models
        self.ilireferencedatacache.type = type
        self.ilireferencedatacache.refresh()

    def _complete_referencedata_completer(self):
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
            self.input_line_edit.completer().popup().scrollToTop()

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
            == gui_utils.QValidator.Acceptable
        )

    def _valid_selection(self):
        return bool(self.source_list_view.selectedIndexes())

    def _add_row(self):
        source = self.input_line_edit.text()
        self.add_source(source, self.tr("Added by user over the wizard."))
        self.input_line_edit.clearFocus()
        self.input_line_edit.clear()

    def _remove_selected_rows(self):
        indices = self.source_list_view.selectionModel().selectedIndexes()
        self.source_list_view.model().remove_sources(indices)
        self.remove_button.setEnabled(self._valid_selection())

    def append_dropped_files(self, dropped_files):
        if dropped_files:
            for dropped_file in dropped_files:
                self.add_source(
                    dropped_file, self.tr("Added by user with drag'n'drop.")
                )

    def add_source(self, source, origin_info):
        if os.path.isfile(source):
            name = pathlib.Path(source).name
            type = pathlib.Path(source).suffix[1:]
            path = source
        else:
            name = source
            type = "xtf"
            path = ""
            matches = self.ilireferencedatacache.model.match(
                self.ilireferencedatacache.model.index(0, 0),
                Qt.DisplayRole,
                self.input_line_edit.text(),
                1,
                Qt.MatchExactly,
            )
            if matches:
                model_index = matches[0]
                path = "ilidata:{}".format(
                    self.ilireferencedatacache.model.data(
                        model_index, int(IliDataItemModel.Roles.ID)
                    )
                )
        return self.source_model.add_source(name, type, path, origin_info)

    def _all_paths_from_model(self):
        paths = []
        for row in range(self.source_model.rowCount()):
            paths.append(
                self.source_model.index(row, 0).data(int(SourceModel.Roles.PATH))
            )
        return paths
