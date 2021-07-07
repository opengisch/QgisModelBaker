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

from QgisModelBaker.libili2db.ilicache import (
    IliMetaConfigCache,
    IliMetaConfigItemModel,
    MetaConfigCompleterDelegate,
    IliToppingFileCache,
    IliToppingFileItemModel
)
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

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

    def __init__(self, base_config, parent=None):
        QWizardPage.__init__(self, parent)
        
        self.setupUi(self)
        self.base_configuration = base_config

        self.setTitle(self.tr("Schema import configuration"))

        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.crsSelector.crsChanged.connect(self.crs_changed)

        '''
        self.ilimetaconfigcache = IliMetaConfigCache(self.base_configuration)
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