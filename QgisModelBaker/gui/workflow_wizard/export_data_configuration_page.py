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


from qgis.PyQt.QtGui import QValidator
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.gui.panel.export_models_panel import ExportModelsPanel
from QgisModelBaker.gui.panel.filter_data_panel import FilterDataPanel
from QgisModelBaker.libs.modelbaker.utils.qt_utils import make_save_file_selector

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/export_data_configuration.ui")


class ExportDataConfigurationPage(QWizardPage, PAGE_UI):
    ValidExtensions = gui_utils.TransferExtensions

    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.filter_data_panel = FilterDataPanel(self.workflow_wizard)
        self.filter_layout.addWidget(self.filter_data_panel)

        self.export_models_panel = ExportModelsPanel(self.workflow_wizard)
        self.export_models_layout.addWidget(self.export_models_panel)

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

        self.validators = gui_utils.Validators()

        fileValidator = gui_utils.FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions],
            allow_non_existing=True,
        )

        self.xtf_file_line_edit.setValidator(fileValidator)
        self.xtf_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.connect(self._set_current_export_target)
        self.xtf_file_line_edit.textChanged.emit(self.xtf_file_line_edit.text())

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        if self.is_complete != complete:
            self.is_complete = complete
            self.completeChanged.emit()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def setup_dialog(self, basket_handling):
        self.filter_data_panel.setup_dialog(basket_handling)
        self.export_models_panel.setup_dialog()

    def _set_current_export_target(self, text):
        self.setComplete(
            self.xtf_file_line_edit.validator().validate(text, 0)[0]
            == QValidator.Acceptable
        )
        self.workflow_wizard.current_export_target = text

    def help_text(self):
        logline = self.tr(
            "You want to export your data to an xml-file? There are two big options..."
        )
        help_paragraphs = self.tr(
            """
        <h4>Filter</h4>
        <p align="justify">You can filter your data by the models, datasets or baskets in which it is stored.</p>
        <h4>Format</h4>
        <p align="justify">Still you can choose <b>Export data in another model</b>, which allows you to select a base model as the data format.<br />
        Even if the data is stored in an extended model.</p>
        """
        )
        docutext = self.tr(
            'Find more information about <b>exporting data</b> in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/export_workflow/#2-export-data">documentation</a>...'
        )
        return logline, help_paragraphs, docutext
