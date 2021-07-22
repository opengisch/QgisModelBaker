# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 29/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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
import webbrowser

import re
import configparser
import yaml
import time
from psycopg2 import OperationalError

from QgisModelBaker.gui.options import OptionsDialog, CompletionLineEdit
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.multiple_models import MultipleModelsDialog
from QgisModelBaker.gui.edit_command import EditCommandDialog
from QgisModelBaker.libili2db.globals import CRS_PATTERNS, displayDbIliMode, DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import SchemaImportConfiguration, ImportDataConfiguration
from QgisModelBaker.libili2db.ilicache import (
    IliCache,
    ModelCompleterDelegate,
    IliMetaConfigCache,
    IliMetaConfigItemModel,
    MetaConfigCompleterDelegate,
    IliToppingFileCache,
    IliToppingFileItemModel
)
from QgisModelBaker.libili2db.ili2dbutils import color_log_text, JavaNotFoundError
from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    Validators,
    FileValidator,
    NonEmptyStringValidator,
    OverrideCursor
)
from qgis.PyQt.QtGui import (
    QColor,
    QDesktopServices,
    QValidator
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QCompleter,
    QSizePolicy,
    QGridLayout,
    QMessageBox,
    QAction,
    QToolButton
)
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    Qt,
    QLocale,
    QModelIndex,
    QTimer,
    QEventLoop
)

from qgis.core import (
    QgsProject,
    QgsCoordinateReferenceSystem,
    Qgis
)
from qgis.gui import (
    QgsMessageBar,
    QgsGui
)
from ..utils import get_ui_class
from ..libili2db import iliimporter
from ..libili2db.globals import DbIliMode
from ..libqgsprojectgen.generator.generator import Generator
from ..libqgsprojectgen.dataobjects import Project
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError

DIALOG_UI = get_ui_class('generate_project.ui')

#log colors
COLOR_SUCCESS = '#aa2222'
COLOR_FAIL = '#004905'
COLOR_TOPPING = '#341d5c'

class GenerateProjectDialog(QDialog, DIALOG_UI):

    ValidExtensions = ['ili']

    def __init__(self, iface, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)

        self.create_text = self.tr('Create')
        self.set_button_to_create_action = QAction(self.create_text, None)
        self.set_button_to_create_action.triggered.connect(self.set_button_to_create)

        self.create_without_constraints_text = self.tr('Create without constraints')
        self.set_button_to_create_without_constraints_action = QAction(self.create_without_constraints_text, None)
        self.set_button_to_create_without_constraints_action.triggered.connect(self.set_button_to_create_without_constraints)

        self.edit_command_action = QAction(self.tr('Edit ili2db command'), None)
        self.edit_command_action.triggered.connect(self.edit_command)

        self.create_tool_button.addAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_text)
        self.create_tool_button.clicked.connect(self.accepted)

        self.buttonBox.accepted.disconnect()
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)

        self.create_constraints = True

        self.create_button.setText(self.tr('Create'))
        self.create_button.clicked.connect(self.accepted)
        self.ili_file_browse_button.clicked.connect(
            make_file_selector(self.ili_file_line_edit, title=self.tr('Open Interlis Model'),
                               file_filter=self.tr('Interlis Model File (*.ili *.ILI)')))
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)
        self.multiple_models_dialog = MultipleModelsDialog(self)
        self.multiple_models_button.clicked.connect(
            self.multiple_models_dialog.open)
        self.multiple_models_dialog.accepted.connect(
            self.fill_models_line_edit)

        self.type_combo_box.clear()
        self._lst_panel = dict()

        for db_id in self.db_simple_factory.get_db_list(True):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)

        for db_id in self.db_simple_factory.get_db_list(False):
            db_factory = self.db_simple_factory.create_factory(db_id)
            item_panel = db_factory.get_config_panel(self, DbActionType.GENERATE)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.type_combo_box.currentIndexChanged.connect(self.type_changed)
        self.txtStdout.anchorClicked.connect(self.link_activated)
        self.crsSelector.crsChanged.connect(self.crs_changed)
        self.base_configuration = base_config

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()
        fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_empty=True)

        self.restore_configuration()

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

        self.ili_models_line_edit.setValidator(nonEmptyValidator)
        self.ili_file_line_edit.setValidator(fileValidator)

        self.ili_models_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_models_line_edit.textChanged.emit(
            self.ili_models_line_edit.text())
        self.ili_models_line_edit.textChanged.connect(self.on_model_changed)
        self.ili_models_line_edit.textChanged.connect(self.complete_models_completer)
        self.ili_models_line_edit.punched.connect(self.complete_models_completer)

        self.ilicache = IliCache(self.base_configuration)
        self.model_delegate = ModelCompleterDelegate()
        self.refresh_ili_models_cache()
        self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model from repository]'))

        self.ili_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_file_line_edit.textChanged.connect(self.ili_file_changed)
        self.ili_file_line_edit.textChanged.emit(
            self.ili_file_line_edit.text())

    def set_button_to_create(self):
        """
        Changes the text of the button to create (with validation) and sets the validate_data to true.
        So on clicking the button the creation will start with validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.create_constraints = True
        self.create_tool_button.removeAction(self.set_button_to_create_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_text)

    def set_button_to_create_without_constraints(self):
        """
        Changes the text of the button to create without validation and sets the validate_data to false.
        So on clicking the button the creation will start without validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.create_constraints = False
        self.create_tool_button.removeAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_without_constraints_text)

    def edit_command(self):
        """
        A dialog opens giving the user the possibility to edit the ili2db command used for the creation
        """
        importer = iliimporter.Importer()
        importer.tool = self.type_combo_box.currentData()
        importer.configuration = self.updated_configuration()
        command = importer.command(True)
        edit_command_dialog = EditCommandDialog(self)
        edit_command_dialog.command_edit.setPlainText(command)
        if edit_command_dialog.exec_():
            edited_command = edit_command_dialog.command_edit.toPlainText()
            self.accepted(edited_command)

    def accepted(self, edited_command=None):
        configuration = self.updated_configuration()

        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili
        interlis_mode = ili_mode & DbIliMode.ili

        if not edited_command:
            if interlis_mode:
                if not self.ili_file_line_edit.text().strip():
                    if not self.ili_models_line_edit.text().strip():
                        self.txtStdout.setText(
                            self.tr('Please set a valid INTERLIS model before creating the project.'))
                        self.ili_models_line_edit.setFocus()
                        return

                if self.ili_file_line_edit.text().strip() and \
                    self.ili_file_line_edit.validator().validate(configuration.ilifile, 0)[0] != QValidator.Acceptable:

                    self.txtStdout.setText(
                        self.tr('Please set a valid INTERLIS file before creating the project. {}').format(self.ili_file_line_edit.validator().error))
                    self.ili_file_line_edit.setFocus()
                    return

            res, message = self._lst_panel[db_id].is_valid()

            if not res:
                self.txtStdout.setText(message)
                return

        configuration.dbschema = configuration.dbschema or configuration.database
        self.save_configuration(configuration)

        db_factory = self.db_simple_factory.create_factory(db_id)

        try:
            # raise warning when the schema or the database file already exists
            config_manager = db_factory.get_db_command_config_manager(configuration)
            db_connector = db_factory.get_db_connector(
                config_manager.get_uri(configuration.db_use_super_login) or config_manager.get_uri(), configuration.dbschema)

            if db_connector.db_or_schema_exists():
                if interlis_mode:
                    warning_box = QMessageBox(self)
                    warning_box.setIcon(QMessageBox.Information)
                    warning_title = self.tr("{} already exists").format(
                        db_factory.get_specific_messages()['db_or_schema']
                    ).capitalize()
                    warning_box.setWindowTitle(warning_title)
                    warning_box.setText(self.tr("{warning_title}:\n{db_or_schema_name}\n\nDo you want to "
                                                "import into the existing {db_or_schema}?").format(
                        warning_title=warning_title,
                        db_or_schema=db_factory.get_specific_messages()['db_or_schema'].capitalize(),
                        db_or_schema_name=configuration.dbschema or config_manager.get_uri()
                    ))
                    warning_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    warning_box_result = warning_box.exec_()
                    if warning_box_result == QMessageBox.No:
                        return
        except (DBConnectorError, FileNotFoundError):
            # we don't mind when the database file is not yet created
            pass

        # create schema with superuser
        res, message = db_factory.pre_generate_project(configuration)
        if not res:
            self.txtStdout.setText(message)
            return


        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))

            if interlis_mode:
                importer = iliimporter.Importer( )
                importer.tool = self.type_combo_box.currentData()
                importer.configuration = configuration
                importer.stdout.connect(self.print_info)
                importer.stderr.connect(self.on_stderr)
                importer.process_started.connect(self.on_process_started)
                importer.process_finished.connect(self.on_process_finished)
                try:
                    if importer.run(edited_command) != iliimporter.Importer.SUCCESS:
                        self.enable()
                        self.progress_bar.hide()
                        return
                except JavaNotFoundError as e:
                    self.txtStdout.setTextColor(QColor('#000000'))
                    self.txtStdout.clear()
                    self.txtStdout.setText(e.error_string)
                    self.enable()
                    self.progress_bar.hide()
                    return

            try:
                config_manager = db_factory.get_db_command_config_manager(configuration)
                uri = config_manager.get_uri()
                mgmt_uri = config_manager.get_uri(configuration.db_use_super_login)
                generator = Generator(configuration.tool, uri,
                                      configuration.inheritance, configuration.dbschema, mgmt_uri=mgmt_uri)
                generator.stdout.connect(self.print_info)
                generator.new_message.connect(self.show_message)
                self.progress_bar.setValue(30)
            except (DBConnectorError, FileNotFoundError):
                self.txtStdout.setText(
                    self.tr('There was an error connecting to the database. Check connection parameters.'))
                self.enable()
                self.progress_bar.hide()
                return

            if not interlis_mode:
                if not generator.db_or_schema_exists():
                    self.txtStdout.setText(
                        self.tr('Source {} does not exist. Check connection parameters.').format(
                            db_factory.get_specific_messages()['db_or_schema']
                        ))
                    self.enable()
                    self.progress_bar.hide()
                    return

            res, message = db_factory.post_generate_project_validations(configuration)

            if not res:
                self.txtStdout.setText(message)
                self.enable()
                self.progress_bar.hide()
                return

            self.print_info(
                self.tr('\nObtaining available layers from the database…'))

            available_layers = generator.layers()

            if not available_layers:
                text = self.tr('The {} has no layers to load into QGIS.').format(
                            db_factory.get_specific_messages()['layers_source'])

                self.txtStdout.setText(text)
                self.enable()
                self.progress_bar.hide()
                return

            self.progress_bar.setValue(40)
            self.print_info(
                self.tr('Obtaining relations from the database…'))
            relations, bags_of_enum = generator.relations(available_layers)
            self.progress_bar.setValue(45)

            self.print_info(self.tr('Arranging layers into groups…'))
            legend = generator.legend(available_layers)

            custom_layer_order_structure = list()
            # Toppings legend and layers: collect, download and apply
            if 'CONFIGURATION' in self.metaconfig.sections():
                configuration_section = self.metaconfig['CONFIGURATION']
                if 'qgis.modelbaker.layertree' in configuration_section:
                    self.print_info(self.tr('Metaconfig contains a layertree structure topping.'), COLOR_TOPPING)
                    layertree_data_list = configuration_section['qgis.modelbaker.layertree'].split(';')
                    layertree_data_file_path_list = self.get_topping_file_list( layertree_data_list)
                    for layertree_file_path in layertree_data_file_path_list:
                        self.print_info(
                            self.tr('Parse layertree structure {}…').format(layertree_file_path), COLOR_TOPPING)

                        with open(layertree_file_path, 'r') as stream:
                            try:
                                layertree_data = yaml.safe_load(stream)
                                if 'legend' in layertree_data:
                                    legend = generator.legend(available_layers, layertree_structure=layertree_data['legend'])
                                if 'layer-order' in layertree_data:
                                    custom_layer_order_structure = layertree_data['layer-order']
                            except yaml.YAMLError as exc:
                                self.print_info(
                                    self.tr('Unable to parse layertree structure: {}').format(exc), COLOR_TOPPING)

            self.progress_bar.setValue(55)

            project = Project()
            project.layers = available_layers
            project.relations = relations
            project.bags_of_enum = bags_of_enum
            project.legend = legend
            project.custom_layer_order_structure = custom_layer_order_structure

            self.print_info(self.tr('Configure forms and widgets…'))
            project.post_generate()

            qgis_project = QgsProject.instance()

            self.print_info(self.tr('Generate QGIS project…'))
            project.create(None, qgis_project)

            # Set the extent of the mapCanvas from the first layer extent found
            for layer in project.layers:
                if layer.extent is not None:
                    self.iface.mapCanvas().setExtent(layer.extent)
                    self.iface.mapCanvas().refresh()
                    break

            self.progress_bar.setValue(60)
            # Toppings QMLs: collect, download and apply
            if 'qgis.modelbaker.qml' in self.metaconfig.sections():
                self.print_info(self.tr('Metaconfig contains QML toppings.'), COLOR_TOPPING)
                qml_section = dict(self.metaconfig['qgis.modelbaker.qml'])
                qml_file_model = self.get_topping_file_model(list(qml_section.values()))
                for layer in project.layers:
                    if any(layer.alias.lower() == s for s in qml_section):
                        layer_qml = layer.alias.lower()
                    elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                        layer_qml = f'"{layer.alias.lower()}"'
                    else:
                        continue
                    matches = qml_file_model.match(qml_file_model.index(0, 0), Qt.DisplayRole,
                                                   qml_section[layer_qml], 1)
                    if matches:
                        style_file_path = matches[0].data(int(IliToppingFileItemModel.Roles.LOCALFILEPATH))
                        self.print_info(self.tr('Apply QML topping on layer {}:{}…').format(layer.alias, style_file_path),
                                        COLOR_TOPPING)
                        layer.layer.loadNamedStyle(style_file_path)

            self.progress_bar.setValue(80)

            # Cataloges and Transferfiles: collect, download and import
            if 'CONFIGURATION' in self.metaconfig.sections():
                configuration_section = self.metaconfig['CONFIGURATION']
                if 'ch.interlis.referenceData' in configuration_section:
                    self.print_info(self.tr('Metaconfig contains transfer or catalogue toppings (reference data).'), COLOR_TOPPING)
                    reference_data_list = configuration_section['ch.interlis.referenceData'].split(';')
                    referencedata_file_path_list = self.get_topping_file_list(reference_data_list)
                    for referencedata_file_path in referencedata_file_path_list:
                        self.print_info(
                            self.tr('Import reference data file {}…').format(referencedata_file_path))

                        configuration = self.updated_referencedata_import_configuration(referencedata_file_path)

                        # create schema with superuser
                        db_factory = self.db_simple_factory.create_factory(db_id)
                        res, message = db_factory.pre_generate_project(configuration)

                        if not res:
                            self.txtStdout.setText(message)
                            return

                        with OverrideCursor(Qt.WaitCursor):

                            dataImporter = iliimporter.Importer(dataImport=True)

                            dataImporter.tool = self.type_combo_box.currentData()
                            dataImporter.configuration = configuration

                            dataImporter.stdout.connect(self.print_info)
                            dataImporter.stderr.connect(self.on_stderr)
                            dataImporter.process_started.connect(self.on_process_started)
                            dataImporter.process_finished.connect(self.on_process_finished)

                            try:
                                if dataImporter.run(edited_command) != iliimporter.Importer.SUCCESS:
                                    self.enable()
                                    self.progress_bar.hide()
                                    return
                            except JavaNotFoundError as e:
                                self.txtStdout.setTextColor(QColor('#000000'))
                                self.txtStdout.clear()
                                self.txtStdout.setText(e.error_string)
                                self.enable()
                                self.progress_bar.hide()
                                return

            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
            self.progress_bar.setValue(100)
            self.print_info(self.tr('\nDone!'), '#004905')

    def print_info(self, text, text_color='#000000'):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)
        self.advance_progress_bar_by_text(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.print_info(self.tr('\n--- Process ---'))
        self.print_info(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = COLOR_SUCCESS
            message = self.tr(
                'Interlis model(s) successfully imported into the database!')
        else:
            color = COLOR_FAIL
            message = self.tr('Finished with errors!')

        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(message)

    def db_ili_version(self, configuration):
        """
        Returns the ili2db version the database has been created with or None if the database
        could not be detected as a ili2db database
        """
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
            db_connector.new_message.connect(self.show_message)
            return db_connector.ili_version()
        except (DBConnectorError, FileNotFoundError):
            return None

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = SchemaImportConfiguration()

        mode = self.type_combo_box.currentData()
        db_id = mode & ~DbIliMode.ili

        self._lst_panel[db_id].get_fields(configuration)

        configuration.tool = mode
        configuration.srs_auth = self.srs_auth
        configuration.srs_code = self.srs_code
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()
        configuration.db_ili_version = self.db_ili_version(configuration)
        configuration.metaconfig = self.metaconfig
        configuration.metaconfig_id = self.current_metaconfig_id

        configuration.base_configuration = self.base_configuration
        if self.ili_file_line_edit.text().strip():
            configuration.ilifile = self.ili_file_line_edit.text().strip()

        if self.ili_models_line_edit.text().strip():
            configuration.ilimodels = self.ili_models_line_edit.text().strip()

        if not self.create_constraints:
            configuration.disable_validation = True

        return configuration

    def updated_referencedata_import_configuration(self, file):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = ImportDataConfiguration()

        mode = self.type_combo_box.currentData()

        db_id = mode & ~DbIliMode.ili
        self._lst_panel[db_id].get_fields(configuration)

        configuration.tool = mode
        configuration.xtffile = file
        configuration.delete_data = False
        configuration.base_configuration = self.base_configuration
        configuration.with_schemaimport = False
        #if not self.validate_data:
        #    configuration.disable_validation = True
        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgisModelBaker/ili2db/ilifile',
                          configuration.ilifile)
        settings.setValue('QgisModelBaker/ili2db/srs_auth', self.srs_auth)
        settings.setValue('QgisModelBaker/ili2db/srs_code', self.srs_code)
        settings.setValue('QgisModelBaker/importtype',
                          self.type_combo_box.currentData().name)

        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()

    def restore_configuration(self):
        settings = QSettings()

        self.ili_file_line_edit.setText(
            settings.value('QgisModelBaker/ili2db/ilifile'))
        srs_auth = settings.value('QgisModelBaker/ili2db/srs_auth', 'EPSG')
        srs_code = settings.value('QgisModelBaker/ili2db/srs_code', 21781, int)
        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self.fill_toml_file_info_label()
        self.update_crs_info()

        for db_id in self.db_simple_factory.get_db_list(False):
            configuration = SchemaImportConfiguration()
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value('QgisModelBaker/importtype')
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.type_changed()
        self.crs_changed()

    def disable(self):
        self.type_combo_box.setEnabled(False)
        for key, value in self._lst_panel.items():
            value.setEnabled(False)
        self.ili_config.setEnabled(False)
        self.buttonBox.setEnabled(False)

    def enable(self):
        self.type_combo_box.setEnabled(True)
        for key, value in self._lst_panel.items():
            value.setEnabled(True)
        self.ili_config.setEnabled(True)
        self.buttonBox.setEnabled(True)

    def type_changed(self):
        self.txtStdout.clear()
        self.progress_bar.hide()

        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili
        interlis_mode = bool(ili_mode & DbIliMode.ili)

        self.ili_config.setVisible(interlis_mode)
        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        self.create_button.setVisible(not interlis_mode)
        self.create_tool_button.setVisible(interlis_mode)

        # Refresh panels
        for key, value in self._lst_panel.items():
            value.interlis_mode = interlis_mode
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()

    def on_model_changed(self, text):
        if not text:
            self.update_metaconfig_completer(0)
            return
        for pattern, crs in CRS_PATTERNS.items():
            if re.search(pattern, text):
                self.crs = QgsCoordinateReferenceSystem.fromEpsgId(int(crs))
                self.update_crs_info()
                break
        self.ili2db_options.set_toml_file_key(text)
        self.fill_toml_file_info_label()
        self.ilimetaconfigcache = IliMetaConfigCache(self.base_configuration, text)
        self.ilimetaconfigcache.file_download_succeeded.connect(lambda dataset_id, path: self.on_metaconfig_received(path))
        self.ilimetaconfigcache.file_download_failed.connect(self.on_metaconfig_failed)
        self.ilimetaconfigcache.model_refreshed.connect(self.update_metaconfig_completer)
        self.refresh_ili_metaconfig_cache()

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgisModelBaker/ili2db')
                self.base_configuration.save(settings)
        else:
            QDesktopServices.openUrl(link)

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

    def ili_file_changed(self):
        # If ili file is valid, models is optional
        if self.ili_file_line_edit.text().strip() and \
                self.ili_file_line_edit.validator().validate(self.ili_file_line_edit.text().strip(), 0)[0] == QValidator.Acceptable:
            self.ili_models_line_edit.setValidator(None)
            self.ili_models_line_edit.textChanged.emit(
                self.ili_models_line_edit.text())

            # Update completer to add models from given ili file
            self.ilicache = IliCache(None, self.ili_file_line_edit.text().strip())
            self.refresh_ili_models_cache()
            models = self.ilicache.process_ili_file(self.ili_file_line_edit.text().strip())
            try:
                self.ili_models_line_edit.setText(models[-1]['name'])
                self.ili_models_line_edit.setPlaceholderText(models[-1]['name'])
            except IndexError:
                self.ili_models_line_edit.setText('')
                self.ili_models_line_edit.setPlaceholderText(self.tr('[No models found in ili file]'))
        else:
            nonEmptyValidator = NonEmptyStringValidator()
            self.ili_models_line_edit.setValidator(nonEmptyValidator)
            self.ili_models_line_edit.textChanged.emit(
                self.ili_models_line_edit.text())

            # Update completer to add models from given ili file
            self.ilicache = IliCache(self.base_configuration)
            self.refresh_ili_models_cache()
            self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model from repository]'))

    def refresh_ili_models_cache(self):
        self.ilicache.new_message.connect(self.show_message)
        self.ilicache.refresh()
        self.update_models_completer()

    def complete_models_completer(self):
        if not self.ili_models_line_edit.text():
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.ili_models_line_edit.completer().complete()
        else:
            match_contains = self.ili_models_line_edit.completer().completionModel().match(self.ili_models_line_edit.completer().completionModel().index(0, 0),
                                            Qt.DisplayRole, self.ili_models_line_edit.text(), -1, Qt.MatchContains)
            if len(match_contains) > 1:
                self.ili_models_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)
                self.ili_models_line_edit.completer().complete()

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.ili_models_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.model_delegate)
        self.ili_models_line_edit.setCompleter(completer)
        self.multiple_models_dialog.models_line_edit.setCompleter(completer)

    def refresh_ili_metaconfig_cache(self):
        self.ilimetaconfigcache.new_message.connect(self.show_message)
        self.ilimetaconfigcache.refresh()

    def complete_metaconfig_completer(self):
        if not self.ili_metaconfig_line_edit.text():
            self.clean_metaconfig()
            self.ili_metaconfig_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.ili_metaconfig_line_edit.completer().complete()
        else:
            if ';' not in self.ili_metaconfig_line_edit.text():
                match_contains = self.ili_metaconfig_line_edit.completer().completionModel().match(self.ili_metaconfig_line_edit.completer().completionModel().index(0, 0),
                                                Qt.DisplayRole, self.ili_metaconfig_line_edit.text(), -1, Qt.MatchContains)
                if len(match_contains) > 1:
                    self.ili_metaconfig_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)
                    self.ili_metaconfig_line_edit.completer().complete()

    def update_metaconfig_completer(self, rows):
        self.ili_metaconfig_line_edit.completer().setModel(self.ilimetaconfigcache.model)
        self.ili_metaconfig_line_edit.setEnabled(bool(rows))
        if self.ili_models_line_edit.text() != self.current_models:
            self.ili_metaconfig_line_edit.clear()

    def on_metaconfig_completer_activated(self, text=None):
        matches = self.ilimetaconfigcache.model.match(self.ilimetaconfigcache.model.index(0, 0),
                                            Qt.DisplayRole, self.ili_metaconfig_line_edit.text(), 1, Qt.MatchExactly)
        if matches:
            model_index = matches[0]
            metaconfig_id = self.ilimetaconfigcache.model.data(model_index, int(IliMetaConfigItemModel.Roles.ID))
            
            if self.current_metaconfig_id == metaconfig_id:
                return
            self.current_metaconfig_id = metaconfig_id
            self.metaconfig_file_info_label.setText(self.tr('Current Metaconfig File: {} ({})').format(
                self.ilimetaconfigcache.model.data(model_index, Qt.DisplayRole),
                metaconfig_id))
            self.metaconfig_file_info_label.setStyleSheet('color: #341d5c')
            repository = self.ilimetaconfigcache.model.data(model_index, int(IliMetaConfigItemModel.Roles.ILIREPO))
            url = self.ilimetaconfigcache.model.data(model_index, int(IliMetaConfigItemModel.Roles.URL))
            path = self.ilimetaconfigcache.model.data(model_index, int(IliMetaConfigItemModel.Roles.RELATIVEFILEPATH))
            dataset_id = self.ilimetaconfigcache.model.data(model_index, int(IliMetaConfigItemModel.Roles.ID))
            # disable the create button while downloading
            self.create_tool_button.setEnabled(False)
            if path:
                self.ilimetaconfigcache.download_file(repository, url, path, dataset_id)
            else:
                self.print_info(self.tr('File not specified for metaconfig with id {}.').format(dataset_id), COLOR_TOPPING)

            self.set_metaconfig_line_edit_state(True)
        else:
            self.set_metaconfig_line_edit_state(not self.ili_metaconfig_line_edit.text())
            self.clean_metaconfig()

    def clean_metaconfig(self):
        self.current_metaconfig_id = None
        self.metaconfig.clear()
        self.metaconfig_file_info_label.setText('')
        self.txtStdout.clear()

    def set_metaconfig_line_edit_state(self, valid ):
        self.ili_metaconfig_line_edit.setStyleSheet('QLineEdit {{ background-color: {} }}'.format('#ffffff' if valid else '#ffd356'))

    def on_metaconfig_received(self, path):
        self.txtStdout.clear()
        self.print_info(self.tr('Metaconfig file successfully downloaded: {}').format(path), COLOR_TOPPING)
        # parse metaconfig
        self.metaconfig.clear()
        with open(path) as metaconfig_file:
            self.metaconfig.read_file(metaconfig_file)
            self.load_metaconfig()
            # enable the tool button again
            self.create_tool_button.setEnabled(True)
            self.fill_toml_file_info_label()
            self.print_info(self.tr('Metaconfig successfully loaded.'), COLOR_TOPPING)

    def on_metaconfig_failed(self, dataset_id, error_msg):
        self.print_info(self.tr('Download of metaconfig file failed: {}.').format(error_msg), COLOR_TOPPING)
        # enable the tool button again
        self.create_tool_button.setEnabled(True)

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
        # load ili2db parameters to the GUI and into the configuration
        if 'ch.ehi.ili2db' in self.metaconfig.sections():
            self.print_info(
                self.tr('Load the ili2db configurations from the metaconfig…'), COLOR_TOPPING)

            ili2db_metaconfig = self.metaconfig['ch.ehi.ili2db']

            if 'defaultSrsAuth' in ili2db_metaconfig or 'defaultSrsCode' in ili2db_metaconfig:
                self.load_crs_from_metaconfig( ili2db_metaconfig )
                self.print_info(self.tr('- Loaded CRS'), COLOR_TOPPING)

            if 'models' in ili2db_metaconfig:
                model_list = self.ili_models_line_edit.text().strip().split(';') + ili2db_metaconfig.get(
                    'models').strip().split(';')
                self.current_models = ';'.join(set(model_list))
                self.ili_models_line_edit.setText(self.current_models)
                self.print_info(self.tr('- Loaded models'), COLOR_TOPPING)

            self.ili2db_options.load_metaconfig(ili2db_metaconfig)
            self.print_info(self.tr('- Loaded ili2db options'), COLOR_TOPPING)

            # get iliMetaAttrs (toml)
            if 'iliMetaAttrs' in ili2db_metaconfig:
                self.print_info(self.tr('- Seek for iliMetaAttrs (toml) files:'), COLOR_TOPPING)
                ili_meta_attrs_list = ili2db_metaconfig.get('iliMetaAttrs').split(';')
                ili_meta_attrs_file_path_list = self.get_topping_file_list(ili_meta_attrs_list)
                self.ili2db_options.load_toml_file_path(self.ili_models_line_edit.text(), ';'.join(ili_meta_attrs_file_path_list))
                self.print_info(self.tr('- Loaded iliMetaAttrs (toml) files'), COLOR_TOPPING)

            # get prescript (sql)
            if 'prescript' in ili2db_metaconfig:
                self.print_info(self.tr('- Seek for prescript (sql) files:'), COLOR_TOPPING)
                prescript_list = ili2db_metaconfig.get('prescript').split(';')
                prescript_file_path_list = self.get_topping_file_list(prescript_list)
                self.ili2db_options.load_pre_script_path(';'.join(prescript_file_path_list))
                self.print_info(self.tr('- Loaded prescript (sql) files'), COLOR_TOPPING)

            # get postscript (sql)
            if 'postscript' in ili2db_metaconfig:
                self.print_info(self.tr('- Seek for postscript (sql) files:'), COLOR_TOPPING)
                postscript_list = ili2db_metaconfig.get('postscript').split(';')
                postscript_file_path_list = self.get_topping_file_list(postscript_list)
                self.ili2db_options.load_post_script_path(';'.join(postscript_file_path_list))
                self.print_info(self.tr('- Loaded postscript (sql) files'), COLOR_TOPPING)

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)

    def fill_models_line_edit(self):
        self.ili_models_line_edit.setText(
            self.multiple_models_dialog.get_models_string())

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#generate-project".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#generate-project")

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models…':
            self.progress_bar.setValue(20)
        elif text.strip() == 'Info: create table structure…':
            self.progress_bar.setValue(30)

    def get_topping_file_list(self, id_list):
        topping_file_model = self.get_topping_file_model(id_list)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1)
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                self.print_info(
                    self.tr('- - Got file {}').format(file_path), COLOR_TOPPING)
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, id_list):
        topping_file_cache = IliToppingFileCache(self.base_configuration, id_list)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()
        self.print_info(self.tr('- - Downloading…'), COLOR_TOPPING)

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        if len(topping_file_cache.downloaded_files) == len(id_list):
            self.print_info(self.tr('- - All topping files successfully downloaded'), COLOR_TOPPING)
        else:
            missing_file_ids = id_list
            for downloaded_file_id in topping_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            self.print_info(self.tr('- - Some topping files where not successfully downloaded: {}').format(' '.join(missing_file_ids)), COLOR_TOPPING)

        return topping_file_cache.model
