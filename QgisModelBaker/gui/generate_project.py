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
from psycopg2 import OperationalError

from QgisModelBaker.gui.options import OptionsDialog, CompletionLineEdit
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.multiple_models import MultipleModelsDialog
from QgisModelBaker.gui.edit_command import EditCommandDialog
from QgisModelBaker.libili2db.globals import CRS_PATTERNS, displayDbIliMode, DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import SchemaImportConfiguration
from QgisModelBaker.libili2db.ilicache import IliCache, ModelCompleterDelegate
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
    QLocale
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


class GenerateProjectDialog(QDialog, DIALOG_UI):

    ValidExtensions = ['ili', 'ILI']

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
        self.refresh_ili_cache()
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
                        self.tr('Please set a valid INTERLIS file before creating the project.'))
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
            self.txtStdout.clear()

            if interlis_mode:
                importer = iliimporter.Importer()
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
                self.progress_bar.setValue(50)
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

            self.progress_bar.setValue(70)
            self.print_info(
                self.tr('Obtaining relations from the database…'))
            relations, bags_of_enum = generator.relations(available_layers)
            self.progress_bar.setValue(75)
            self.print_info(self.tr('Arranging layers into groups…'))
            legend = generator.legend(available_layers)
            self.progress_bar.setValue(85)

            project = Project()
            project.layers = available_layers
            project.relations = relations
            project.bags_of_enum = bags_of_enum
            project.legend = legend
            self.print_info(self.tr('Configuring forms and widgets…'))
            project.post_generate()
            self.progress_bar.setValue(90)

            qgis_project = QgsProject.instance()

            self.print_info(self.tr('Generating QGIS project…'))
            project.create(None, qgis_project)

            # Set the extent of the mapCanvas from the first layer extent found
            for layer in project.layers:
                if layer.extent is not None:
                    self.iface.mapCanvas().setExtent(layer.extent)
                    self.iface.mapCanvas().refresh()
                    break

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
        self.txtStdout.setText(command)
        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = '#004905'
            message = self.tr(
                'Interlis model(s) successfully imported into the database!')
        else:
            color = '#aa2222'
            message = self.tr('Finished with errors!')

        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(message)
        self.progress_bar.setValue(50)

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

        configuration.base_configuration = self.base_configuration
        if self.ili_file_line_edit.text().strip():
            configuration.ilifile = self.ili_file_line_edit.text().strip()

        if self.ili_models_line_edit.text().strip():
            configuration.ilimodels = self.ili_models_line_edit.text().strip()

        if not self.create_constraints:
            configuration.disable_validation = True

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
            return
        for pattern, crs in CRS_PATTERNS.items():
            if re.search(pattern, text):
                self.crs = QgsCoordinateReferenceSystem.fromEpsgId(int(crs))
                self.update_crs_info()
                break
        self.ili2db_options.set_toml_file_key(text)
        self.fill_toml_file_info_label()

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
            self.refresh_ili_cache()
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
            self.refresh_ili_cache()
            self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model from repository]'))

    def refresh_ili_cache(self):
        self.ilicache.new_message.connect(self.show_message)
        self.ilicache.refresh()
        self.update_models_completer()

    def complete_models_completer(self):
        if not self.ili_models_line_edit.text():
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.ili_models_line_edit.completer().complete()
        else:
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.ili_models_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.delegate = ModelCompleterDelegate()
        completer.popup().setItemDelegate(self.delegate)
        self.ili_models_line_edit.setCompleter(completer)
        self.multiple_models_dialog.models_line_edit.setCompleter(completer)

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
