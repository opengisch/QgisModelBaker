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

from qgis.PyQt.QtCore import (
    Qt,
    QSettings
)

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QCompleter
)

from qgis.core import QgsCoordinateReferenceSystem

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.ilicache import (
    IliMetaConfigCache,
    IliMetaConfigItemModel,
    MetaConfigCompleterDelegate
)

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_schema_configuration.ui')


class ImportSchemaConfigurationPage(QWizardPage, PAGE_UI):

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setFixedSize(800, 600)
        self.setTitle(self.workflow_wizard.current_page_title())

        self.workflow_wizard = parent
        self.is_complete = True

        self.model_list_view.setModel(self.workflow_wizard.import_models_model)
        self.model_list_view.clicked.connect(
            self.workflow_wizard.import_models_model.check)
        self.model_list_view.space_pressed.connect(
            self.workflow_wizard.import_models_model.check)
        self.model_list_view.model().modelReset.connect(self.update_ilimetaconfigcache)

        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.crsSelector.crsChanged.connect(self.crs_changed)

        self.ilimetaconfigcache = IliMetaConfigCache(
            self.workflow_wizard.import_schema_configuration.base_configuration)
        self.metaconfig_delegate = MetaConfigCompleterDelegate()
        self.metaconfig = configparser.ConfigParser()
        self.current_models = None
        self.current_metaconfig_id = None
        self.ili_metaconfig_line_edit.setPlaceholderText(
            self.tr('[Search metaconfig / topping from UsabILIty Hub]'))
        self.ili_metaconfig_line_edit.setEnabled(False)
        completer = QCompleter(self.ilimetaconfigcache.model,
                               self.ili_metaconfig_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.metaconfig_delegate)
        self.ili_metaconfig_line_edit.setCompleter(completer)
        self.ili_metaconfig_line_edit.textChanged.emit(
            self.ili_metaconfig_line_edit.text())
        self.ili_metaconfig_line_edit.textChanged.connect(
            self.complete_metaconfig_completer)
        self.ili_metaconfig_line_edit.punched.connect(
            self.complete_metaconfig_completer)
        self.ili_metaconfig_line_edit.textChanged.connect(
            self.on_metaconfig_completer_activated)

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.completeChanged.emit()

    def update_ilimetaconfigcache(self):
        self.ilimetaconfigcache = IliMetaConfigCache(
            self.workflow_wizard.import_schema_configuration.base_configuration, ';'.join(self.model_list_view.model().checked_models()))
        self.ilimetaconfigcache.file_download_succeeded.connect(
            lambda dataset_id, path: self.on_metaconfig_received(path))
        self.ilimetaconfigcache.file_download_failed.connect(
            self.on_metaconfig_failed)
        self.ilimetaconfigcache.model_refreshed.connect(
            self.update_metaconfig_completer)
        self.refresh_ili_metaconfig_cache()

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(
                self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def update_crs_info(self):
        self.crsSelector.setCrs(self.crs)

    def crs_changed(self):
        self.srs_auth = 'EPSG'  # Default
        self.srs_code = 21781  # Default
        srs_auth, srs_code = self.crsSelector.crs().authid().split(":")
        if srs_auth == 'USER':
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

    def refresh_ili_metaconfig_cache(self):
        self.ilimetaconfigcache.new_message.connect(
            self.workflow_wizard.log_panel.show_message)
        self.ilimetaconfigcache.refresh()

    def complete_metaconfig_completer(self):
        if not self.ili_metaconfig_line_edit.text():
            self.clean_metaconfig()
            self.ili_metaconfig_line_edit.completer().setCompletionMode(
                QCompleter.UnfilteredPopupCompletion)
            self.ili_metaconfig_line_edit.completer().complete()
        else:
            if ';' not in self.ili_metaconfig_line_edit.text():
                match_contains = self.ili_metaconfig_line_edit.completer().completionModel().match(self.ili_metaconfig_line_edit.completer().completionModel().index(0, 0),
                                                                                                   Qt.DisplayRole, self.ili_metaconfig_line_edit.text(), -1, Qt.MatchContains)
                if len(match_contains) > 1:
                    self.ili_metaconfig_line_edit.completer(
                    ).setCompletionMode(QCompleter.PopupCompletion)
                    self.ili_metaconfig_line_edit.completer().complete()

    def update_metaconfig_completer(self, rows):
        self.ili_metaconfig_line_edit.completer().setModel(self.ilimetaconfigcache.model)
        self.ili_metaconfig_line_edit.setEnabled(bool(rows))

    def on_metaconfig_completer_activated(self, text=None):
        matches = self.ilimetaconfigcache.model.match(self.ilimetaconfigcache.model.index(0, 0),
                                                      Qt.DisplayRole, self.ili_metaconfig_line_edit.text(), 1, Qt.MatchExactly)
        if matches:
            model_index = matches[0]
            metaconfig_id = self.ilimetaconfigcache.model.data(
                model_index, int(IliMetaConfigItemModel.Roles.ID))

            if self.current_metaconfig_id == metaconfig_id:
                return
            self.current_metaconfig_id = metaconfig_id
            self.metaconfig_file_info_label.setText(self.tr('Current Metaconfig File: {} ({})').format(
                self.ilimetaconfigcache.model.data(
                    model_index, Qt.DisplayRole),
                metaconfig_id))
            self.metaconfig_file_info_label.setStyleSheet('color: #341d5c')
            repository = self.ilimetaconfigcache.model.data(
                model_index, int(IliMetaConfigItemModel.Roles.ILIREPO))
            url = self.ilimetaconfigcache.model.data(
                model_index, int(IliMetaConfigItemModel.Roles.URL))
            path = self.ilimetaconfigcache.model.data(
                model_index, int(IliMetaConfigItemModel.Roles.RELATIVEFILEPATH))
            dataset_id = self.ilimetaconfigcache.model.data(
                model_index, int(IliMetaConfigItemModel.Roles.ID))
            # disable the next buttton
            self.setComplete(False)
            if path:
                self.ilimetaconfigcache.download_file(
                    repository, url, path, dataset_id)
            else:
                self.workflow_wizard.log_panel.print_info(self.tr(
                    'File not specified for metaconfig with id {}.').format(dataset_id), LogPanel.COLOR_TOPPING)

            self.set_metaconfig_line_edit_state(True)
        else:
            self.set_metaconfig_line_edit_state(
                not self.ili_metaconfig_line_edit.text())
            self.clean_metaconfig()

    def clean_metaconfig(self):
        self.current_metaconfig_id = None
        self.metaconfig.clear()
        self.metaconfig_file_info_label.setText('')
        self.workflow_wizard.log_panel.txtStdout.clear()

    def set_metaconfig_line_edit_state(self, valid):
        self.ili_metaconfig_line_edit.setStyleSheet(
            'QLineEdit {{ background-color: {} }}'.format('#ffffff' if valid else '#ffd356'))

    def on_metaconfig_received(self, path):
        self.workflow_wizard.log_panel.txtStdout.clear()
        self.workflow_wizard.log_panel.print_info(self.tr(
            'Metaconfig file successfully downloaded: {}').format(path), LogPanel.COLOR_TOPPING)
        # parse metaconfig
        self.metaconfig.clear()
        with open(path) as metaconfig_file:
            self.metaconfig.read_file(metaconfig_file)
            self.load_metaconfig()
            # enable the next buttton
            self.setComplete(True)
            self.fill_toml_file_info_label()
            self.workflow_wizard.log_panel.print_info(
                self.tr('Metaconfig successfully loaded.'), LogPanel.COLOR_TOPPING)

    def on_metaconfig_failed(self, dataset_id, error_msg):
        self.workflow_wizard.log_panel.print_info(self.tr(
            'Download of metaconfig file failed: {}.').format(error_msg), LogPanel.COLOR_TOPPING)
        # enable the next buttton
        self.setComplete(True)

    def load_crs_from_metaconfig(self, ili2db_metaconfig):
        srs_auth = self.srs_auth
        srs_code = self.srs_code
        if 'defaultSrsAuth' in ili2db_metaconfig:
            srs_auth = ili2db_metaconfig.get('defaultSrsAuth')
        if 'defaultSrsCode' in ili2db_metaconfig:
            srs_code = ili2db_metaconfig.get('defaultSrsCode')

        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self.update_crs_info()
        self.crs_changed()

    def load_metaconfig(self):
        # load ili2db parameters to the GUI
        if 'ch.ehi.ili2db' in self.metaconfig.sections():
            self.workflow_wizard.log_panel.print_info(
                self.tr('Load the ili2db configurations from the metaconfig…'), LogPanel.COLOR_TOPPING)

            ili2db_metaconfig = self.metaconfig['ch.ehi.ili2db']

            if 'defaultSrsAuth' in ili2db_metaconfig or 'defaultSrsCode' in ili2db_metaconfig:
                self.load_crs_from_metaconfig(ili2db_metaconfig)
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Loaded CRS'), LogPanel.COLOR_TOPPING)

            if 'models' in ili2db_metaconfig:
                for model in ili2db_metaconfig.get('models').strip().split(';'):
                    self.workflow_wizard.source_model.add_source(
                        model, 'model', None)
                self.workflow_wizard.refresh_import_models_model()
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Loaded models'), LogPanel.COLOR_TOPPING)

            self.ili2db_options.load_metaconfig(ili2db_metaconfig)
            self.workflow_wizard.log_panel.print_info(
                self.tr('- Loaded ili2db options'), LogPanel.COLOR_TOPPING)

            # get iliMetaAttrs (toml)
            if 'iliMetaAttrs' in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Seek for iliMetaAttrs (toml) files:'), LogPanel.COLOR_TOPPING)
                ili_meta_attrs_list = ili2db_metaconfig.get(
                    'iliMetaAttrs').split(';')
                ili_meta_attrs_file_path_list = self.workflow_wizard.get_topping_file_list(
                    ili_meta_attrs_list, self.workflow_wizard.log_panel)
                self.ili2db_options.load_toml_file_path(';'.join(self.model_list_view.model(
                ).checked_models()), ';'.join(ili_meta_attrs_file_path_list))
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Loaded iliMetaAttrs (toml) files'), LogPanel.COLOR_TOPPING)

            # get prescript (sql)
            if 'prescript' in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Seek for prescript (sql) files:'), LogPanel.COLOR_TOPPING)
                prescript_list = ili2db_metaconfig.get('prescript').split(';')
                prescript_file_path_list = self.workflow_wizard.get_topping_file_list(
                    prescript_list, self.workflow_wizard.log_panel)
                self.ili2db_options.load_pre_script_path(
                    ';'.join(prescript_file_path_list))
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Loaded prescript (sql) files'), LogPanel.COLOR_TOPPING)

            # get postscript (sql)
            if 'postscript' in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Seek for postscript (sql) files:'), LogPanel.COLOR_TOPPING)
                postscript_list = ili2db_metaconfig.get(
                    'postscript').split(';')
                postscript_file_path_list = self.workflow_wizard.get_topping_file_list(
                    postscript_list, self.workflow_wizard.log_panel)
                self.ili2db_options.load_post_script_path(
                    ';'.join(postscript_file_path_list))
                self.workflow_wizard.log_panel.print_info(
                    self.tr('- Loaded postscript (sql) files'), LogPanel.COLOR_TOPPING)

        # get referenceData file and update the source model
        if 'CONFIGURATION' in self.metaconfig.sections():
            configuration_section = self.metaconfig['CONFIGURATION']
            if 'ch.interlis.referenceData' in configuration_section:
                self.workflow_wizard.log_panel.print_info(self.tr(
                    'Metaconfig contains transfer or catalogue toppings (reference data).'), LogPanel.COLOR_TOPPING)
                reference_data_list = configuration_section['ch.interlis.referenceData'].split(
                    ';')
                referencedata_file_path_list = self.workflow_wizard.get_topping_file_list(
                    reference_data_list, self.workflow_wizard.log_panel)
                for referencedata_file_path in referencedata_file_path_list:
                    if os.path.isfile(referencedata_file_path):
                        name = pathlib.Path(referencedata_file_path).name
                        type = pathlib.Path(referencedata_file_path).suffix[1:]
                        self.workflow_wizard.log_panel.print_info(self.tr('Append reference data file {}…').format(
                            referencedata_file_path), LogPanel.COLOR_TOPPING)
                        self.workflow_wizard.source_model.add_source(
                            name, type, referencedata_file_path)
                    else:
                        self.workflow_wizard.log_panel.print_info(self.tr('Could not append reference data file {}…').format(
                            referencedata_file_path), LogPanel.COLOR_TOPPING)

    def restore_configuration(self):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        settings = QSettings()
        srs_auth = settings.value('QgisModelBaker/ili2db/srs_auth', 'EPSG')
        srs_code = settings.value('QgisModelBaker/ili2db/srs_code', 21781, int)
        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self.update_crs_info()
        self.crs_changed()
        self.fill_toml_file_info_label()
        self.update_ilimetaconfigcache()

    def update_configuration(self, configuration):
        # takes settings from the GUI and provides it to the configuration
        configuration.srs_auth = self.srs_auth
        configuration.srs_code = self.srs_code
        configuration.metaconfig = self.metaconfig
        configuration.metaconfig_id = self.current_metaconfig_id
        # ili2db_options
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()
        configuration.tomlfile = self.ili2db_options.toml_file()

    def save_configuration(self, updated_configuration):
        # puts it to QSettings
        settings = QSettings()
        settings.setValue('QgisModelBaker/ili2db/srs_auth',
                          updated_configuration.srs_auth)
        settings.setValue('QgisModelBaker/ili2db/srs_code',
                          updated_configuration.srs_code)

    def nextId(self):
        return self.workflow_wizard.next_id()
