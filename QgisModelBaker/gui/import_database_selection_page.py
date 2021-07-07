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


from QgisModelBaker.libili2db.ilicache import (
    IliCache, 
    ModelCompleterDelegate
)

from qgis.PyQt.QtCore import Qt, QSettings

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.libili2db.ili2dbconfig import ImportDataConfiguration

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QSizePolicy,
    QGridLayout,
    QMessageBox,
    QAction,
    QToolButton
)
from qgis.PyQt.QtGui import QPixmap
from qgis.gui import QgsGui, QgsMessageBar

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_database_selection.ui')

class ImportDatabaseSelectionPage(QWizardPage, PAGE_UI):

    '''
    when there are no models - it should warn that the DB does not exist.
    when there are new models to be created, it should warn that the DB already exists.
    '''
    def __init__(self, base_config, parent=None):
        QWizardPage.__init__(self, parent)
        
        self.setupUi(self)
        self.base_configuration = base_config

        self.setTitle(self.tr("Database Selection"))

        self.type_combo_box.clear()
        self._lst_panel = dict()

        self.db_simple_factory = DbSimpleFactory()
        # can we remove get_db_list(True) in future?
        for db_id in self.db_simple_factory.get_db_list(False):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)
            db_factory = self.db_simple_factory.create_factory(db_id)
            # consider here the DbActionType - they won't be the same anymore
            item_panel = db_factory.get_config_panel(self, DbActionType.GENERATE)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.type_combo_box.currentIndexChanged.connect(self.type_changed)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.restore_configuration()
        self.completeChanged.connect(self.save_configuration)
        self.completeChanged.connect(self.next_btn)

    def next_btn(self):
        print("next")
        
    def type_changed(self):
        self.txtStdout.clear()

        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili

        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        # Refresh panels
        for key, value in self._lst_panel.items():
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()

        '''
        if not self.has_models:
            if not generator.db_or_schema_exists():
                self.txtStdout.setText(
                    self.tr('Source {} does not exist. Check connection parameters.').format(
                        db_factory.get_specific_messages()['db_or_schema']
                    ))
                self.enable()
                self.progress_bar.hide()
                return
        '''

    def restore_configuration(self):
        settings = QSettings()

        print("restore")
        for db_id in self.db_simple_factory.get_db_list(False):
            configuration = ImportDataConfiguration()
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value('QgisModelBaker/importtype')
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.type_changed()


    def updated_configuration(self):
        configuration = ImportDataConfiguration()

        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)
        configuration.tool = mode
        return configuration

    def save_configuration(self):
        configuration = self.updated_configuration()

        settings = QSettings()
        settings.setValue('QgisModelBaker/importtype',
                    self.type_combo_box.currentData().name)
        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()


        print("saved")
