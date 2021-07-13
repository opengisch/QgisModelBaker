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
import configparser

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.ilicache import (
    IliMetaConfigCache,
    IliMetaConfigItemModel,
    MetaConfigCompleterDelegate,
    IliToppingFileCache,
    IliToppingFileItemModel
)
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.options import ModelListView

from qgis.PyQt.QtCore import Qt, QSettings

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QCompleter,
    QSizePolicy,
    QGridLayout,
    QMessageBox,
    QAction,
    QToolButton
)
from qgis.PyQt.QtGui import QPixmap
from qgis.gui import QgsGui, QgsMessageBar
from qgis.core import QgsCoordinateReferenceSystem

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_schema_configuration.ui')

class ImportSchemaConfigurationPage(QWizardPage, PAGE_UI):

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)
        
        self.setupUi(self)
        self.setFixedSize(1200,800)
        self.setTitle(self.tr("Schema import configuration"))
        self.log_panel = LogPanel()
        layout = self.layout()
        layout.addWidget(self.log_panel)
        self.setLayout(layout)
        
        self.model_list_view.setModel(parent.import_models_model)
        self.model_list_view.clicked.connect(parent.import_models_model.check)
        self.model_list_view.space_pressed.connect(parent.import_models_model.check)

        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.crsSelector.crsChanged.connect(self.crs_changed)

        '''
        self.ilimetaconfigcache = IliMetaConfigCache(parent.configuration.base_configuration)
        self.metaconfig_delegate = MetaConfigCompleterDelegate()
        self.metaconfig = configparser.ConfigParser()
        self.current_models = None
        self.current_metaconfig_id = None
        self.ili_metaconfig_line_edit.setPlaceholderText(self.tr('[Search metaconfig / topping from UsabILIty Hub]'))
        self.ili_metaconfig_line_edit.setEnabled(False)
        completer = QCompleter(self.ilimetaconfigcache.model, self.ili_metaconfig_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.metaconfig_delegate)
        self.ili_metaconfig_line_edit.setCompleter(completer)
        self.ili_metaconfig_line_edit.textChanged.emit(self.ili_metaconfig_line_edit.text())
        self.ili_metaconfig_line_edit.textChanged.connect(self.complete_metaconfig_completer)
        self.ili_metaconfig_line_edit.punched.connect(self.complete_metaconfig_completer)
        self.ili_metaconfig_line_edit.textChanged.connect(self.on_metaconfig_completer_activated)
        '''

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())
    
    def update_crs_info(self):
        self.crsSelector.setCrs(self.crs)

    def crs_changed(self):
        self.srs_auth = 'EPSG'  # Default
        self.srs_code = 21781  # Default
        srs_auth, srs_code = self.crsSelector.crs().authid().split(":")
        if  srs_auth == 'USER':
            self.crs_label.setStyleSheet('color: orange')
            self.crs_label.setToolTip(
                self.tr('Please select a valid Coordinate Reference System.\nCRSs from USER are valid for a single computer and therefore, a default EPSG:21781 will be used instead.'))
        else:
            self.crs_label.setStyleSheet('')
            self.crs_label.setToolTip(self.tr('Coordinate Reference System'))
            try:
                self.srs_code = int(srs_code)
                self.srs_auth = srs_auth
            except ValueError:
                # Preserve defaults if srs_code is not an integer
                self.crs_label.setStyleSheet('color: orange')
                self.crs_label.setToolTip(
                    self.tr("The srs code ('{}') should be an integer.\nA default EPSG:21781 will be used.".format(srs_code)))

    def restore_configuration(self, configuration):
        settings = QSettings()
        srs_auth = settings.value('QgisModelBaker/ili2db/srs_auth', 'EPSG')
        srs_code = settings.value('QgisModelBaker/ili2db/srs_code', 21781, int)
        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self.fill_toml_file_info_label()
        self.update_crs_info()
        self.crs_changed()

    def update_configuration(self, configuration):
        configuration.srs_auth = self.srs_auth
        configuration.srs_code = self.srs_code
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()
        #configuration.metaconfig = self.metaconfig
        #configuration.metaconfig_id = self.current_metaconfig_id

        #if not self.create_constraints:
        #    configuration.disable_validation = True

    def save_configuration(self, configuration):
        self.update_configuration(configuration)
        settings = QSettings()
        settings.setValue('QgisModelBaker/ili2db/srs_auth', self.srs_auth)
        settings.setValue('QgisModelBaker/ili2db/srs_code', self.srs_code)
