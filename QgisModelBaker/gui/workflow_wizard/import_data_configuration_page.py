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

from PyQt5.uic.uiparser import _parse_alignment

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QHeaderView
)

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

from ...utils import get_ui_class

PAGE_UI = get_ui_class('workflow_wizard/import_data_configuration.ui')


class ImportDataConfigurationPage(QWizardPage, PAGE_UI):

    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setMinimumSize(600, 500)
        self.setTitle(title)

        self.workflow_wizard = parent

        self.workflow_wizard.import_data_file_model.sourceModel(
        ).setHorizontalHeaderLabels([self.tr('Import File'), self.tr('Dataset')])
        self.file_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table_view.setModel(
            self.workflow_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)

        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index))
        return order_list

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(
                self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def restore_configuration(self):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        # since delete data should be turned off the only left thingy is the toml-file
        self.fill_toml_file_info_label()
        # set chk_delete_data always to unchecked because otherwise the user could delete the data accidentally
        self.chk_delete_data.setChecked(False)

    def update_configuration(self, configuration):
        # takes settings from the GUI and provides it to the configuration
        configuration.delete_data = self.chk_delete_data.isChecked()
        # ili2db_options
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()

    def nextId(self):
        return self.workflow_wizard.next_id()
