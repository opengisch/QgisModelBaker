# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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
import os.path
import re

from QgisModelBaker.gui.options import OptionsDialog, ModelListView
from QgisModelBaker.gui.edit_command import EditCommandDialog
from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from QgisModelBaker.libili2db.ili2dbutils import (
    color_log_text,
    JavaNotFoundError
)
from QgisModelBaker.utils.qt_utils import (
    make_save_file_selector,
    Validators,
    FileValidator,
    OverrideCursor
)
from qgis.PyQt.QtGui import QColor, QDesktopServices, QValidator
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QSizePolicy, QGridLayout, QAction, QToolButton
from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt, QLocale, QStringListModel, QTimer
from qgis.gui import QgsGui, QgsMessageBar
from qgis.core import Qgis
from ..utils import get_ui_class
from ..libili2db import iliexporter, ili2dbconfig
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError


DIALOG_UI = get_ui_class('export.ui')


class ExportModels(QStringListModel):

    blacklist = ['CHBaseEx_MapCatalogue_V1', 'CHBaseEx_WaterNet_V1', 'CHBaseEx_Sewage_V1', 'CHAdminCodes_V1',
                    'AdministrativeUnits_V1', 'AdministrativeUnitsCH_V1', 'WithOneState_V1',
                    'WithLatestModification_V1', 'WithModificationObjects_V1', 'GraphicCHLV03_V1', 'GraphicCHLV95_V1',
                    'NonVector_Base_V2', 'NonVector_Base_V3', 'NonVector_Base_LV03_V3_1', 'NonVector_Base_LV95_V3_1',
                    'GeometryCHLV03_V1', 'GeometryCHLV95_V1', 'InternationalCodes_V1', 'Localisation_V1',
                    'LocalisationCH_V1', 'Dictionaries_V1', 'DictionariesCH_V1', 'CatalogueObjects_V1',
                    'CatalogueObjectTrees_V1', 'AbstractSymbology', 'CodeISO', 'CoordSys', 'GM03_2_1Comprehensive',
                    'GM03_2_1Core', 'GM03_2Comprehensive', 'GM03_2Core', 'GM03Comprehensive', 'GM03Core',
                    'IliRepository09', 'IliSite09', 'IlisMeta07', 'IliVErrors', 'INTERLIS_ext', 'RoadsExdm2ben',
                    'RoadsExdm2ben_10', 'RoadsExgm2ien', 'RoadsExgm2ien_10', 'StandardSymbology', 'StandardSymbology',
                    'Time', 'Units']

    def __init__(self):
        super().__init__()
        self._checked_models = None

    def refresh_models(self, db_connector=None):
        modelnames = list()
        
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r'(?:\{[^\}]*\}|\s)')
                    for modelname in regex.split(db_model['modelname']):
                        if modelname and modelname not in ExportModels.blacklist:
                            modelnames.append(modelname.strip())

        self.setStringList(modelnames)

        self._checked_models = {modelname: Qt.Checked for modelname in modelnames}

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, Qt.DisplayRole)]
        else:
            return QStringListModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self._checked_models[self.data(index, Qt.DisplayRole)] = data
        else:
            QStringListModel.setData(self, index, role, data)

    def check(self, index):
        if self.data(index, Qt.CheckStateRole) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def checked_models(self):
        return [modelname for modelname in self.stringList() if self._checked_models[modelname] == Qt.Checked]


class ExportDialog(QDialog, DIALOG_UI):
    ValidExtensions = ['xtf', 'XTF', 'itf', 'ITF', 'gml', 'GML', 'xml', 'XML']

    def __init__(self, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.buttonBox.accepted.disconnect()
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)

        self.export_text = self.tr('Export')
        self.set_button_to_export_action = QAction(self.export_text, None)
        self.set_button_to_export_action.triggered.connect(self.set_button_to_export)

        self.export_without_validation_text = self.tr('Export without validation')
        self.set_button_to_export_without_validation_action = QAction(self.export_without_validation_text, None)
        self.set_button_to_export_without_validation_action.triggered.connect(self.set_button_to_export_without_validation)

        self.edit_command_action = QAction(self.tr('Edit ili2db command'), None)
        self.edit_command_action.triggered.connect(self.edit_command)

        self.export_tool_button.addAction(self.set_button_to_export_without_validation_action)
        self.export_tool_button.addAction(self.edit_command_action)
        self.export_tool_button.setText(self.export_text)
        self.export_tool_button.clicked.connect(self.accepted)

        self.xtf_file_browse_button.clicked.connect(
            make_save_file_selector(self.xtf_file_line_edit, title=self.tr('Save in XTF Transfer File'),
                                    file_filter=self.tr('XTF Transfer File (*.xtf *XTF);;Interlis 1 Transfer File (*.itf *ITF);;XML (*.xml *XML);;GML (*.gml *GML)'),
                                    extension='.xtf',
                                    extensions=['.' + ext for ext in self.ValidExtensions]))
        self.xtf_file_browse_button.clicked.connect(
            self.xtf_browser_opened_to_true)
        self.xtf_browser_was_opened = False

        self.type_combo_box.clear()
        self._lst_panel = dict()

        for db_id in self.db_simple_factory.get_db_list(False):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)
            db_factory = self.db_simple_factory.create_factory(db_id)
            item_panel = db_factory.get_config_panel(self, DbActionType.EXPORT)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.validators = Validators()

        fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_non_existing=True)

        self.xtf_file_line_edit.setValidator(fileValidator)
        self.xtf_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.connect(
            self.xtf_browser_opened_to_false)
        self.xtf_file_line_edit.textChanged.emit(
            self.xtf_file_line_edit.text())

        # Reset to export as default text
        self.xtf_file_line_edit.textChanged.connect(self.set_button_to_export)

        #refresh the models on changing values but avoid massive db connects by timer
        self.refreshTimer = QTimer()
        self.refreshTimer.setSingleShot(True)
        self.refreshTimer.timeout.connect(self.refresh_models)

        for key, value in self._lst_panel.items():
            value.notify_fields_modified.connect(self.request_for_refresh_models)

        self.validate_data = True # validates exported data by default, We use --disableValidation when is False
        self.base_configuration = base_config
        self.restore_configuration()

        self.export_models_model = ExportModels()
        self.export_models_view.setModel(self.export_models_model)
        self.export_models_view.clicked.connect(self.export_models_model.check)
        self.export_models_view.space_pressed.connect(self.export_models_model.check)
        self.request_for_refresh_models()

        self.type_combo_box.currentIndexChanged.connect(self.type_changed)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

    def request_for_refresh_models(self):
        # hold refresh back
        self.refreshTimer.start(500)

    def refresh_models(self):
        self.refreshed_export_models_model()

    def refreshed_export_models_model(self):
        tool = self.type_combo_box.currentData() & ~DbIliMode.ili
        
        configuration = self.updated_configuration()
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        db_connector = None

        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            # when wrong connection parameters entered, there should just be returned an empty model - so let it pass
            pass

        self.export_models_model.refresh_models(db_connector)

    def db_ili_version(self, configuration):
        """
        Returns the ili2db version the database has been created with or None if the database
        could not be detected as a ili2db database
        """
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        db_connector = None

        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
            return db_connector.ili_version()
        except (DBConnectorError, FileNotFoundError):
            return None

    def set_button_to_export(self):
        """
        Changes the text of the button to export (with validation) and sets the validate_data to true.
        So on clicking the button the export will start with validation.
        The buttons actions are changed to be able to switch the without-validation mode.
        """
        self.validate_data = True
        self.export_tool_button.removeAction(self.set_button_to_export_action)
        self.export_tool_button.removeAction(self.edit_command_action)
        self.export_tool_button.addAction(self.set_button_to_export_without_validation_action)
        self.export_tool_button.addAction(self.edit_command_action)
        self.export_tool_button.setText(self.export_text)

    def set_button_to_export_without_validation(self):
        """
        Changes the text of the button to export without validation and sets the validate_data to false.
        So on clicking the button the export will start without validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.validate_data = False
        self.export_tool_button.removeAction(self.set_button_to_export_without_validation_action)
        self.export_tool_button.removeAction(self.edit_command_action)
        self.export_tool_button.addAction(self.set_button_to_export_action)
        self.export_tool_button.addAction(self.edit_command_action)
        self.export_tool_button.setText(self.export_without_validation_text)

    def edit_command(self):
        """
        A dialog opens giving the user the possibility to edit the ili2db command used for the export
        """
        exporter = iliexporter.Exporter()
        exporter.tool = self.type_combo_box.currentData()
        exporter.configuration = self.updated_configuration()
        command = exporter.command(True)
        edit_command_dialog = EditCommandDialog(self)
        edit_command_dialog.command_edit.setPlainText(command)
        if edit_command_dialog.exec_():
            edited_command = edit_command_dialog.command_edit.toPlainText()
            self.accepted(edited_command)

    def accepted(self, edited_command=None):
        configuration = self.updated_configuration()

        db_id = self.type_combo_box.currentData()

        if not edited_command:
            if not self.xtf_file_line_edit.validator().validate(configuration.xtffile, 0)[0] == QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set a valid INTERLIS XTF file before exporting data.'))
                self.xtf_file_line_edit.setFocus()
                return
            if not configuration.ilimodels:
                self.txtStdout.setText(
                    self.tr('Please set a model before exporting data.'))
                self.export_models_view.setFocus()
                return

            res, message = self._lst_panel[db_id].is_valid()

            if not res:
                self.txtStdout.setText(message)
                return

        # If xtf browser was opened and the file exists, the user already chose
        # to overwrite the file
        if os.path.isfile(self.xtf_file_line_edit.text().strip()) and not self.xtf_browser_was_opened:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setText(self.tr("{filename} already exists.\nDo you want to replace it?").format(filename=os.path.basename(self.xtf_file_line_edit.text().strip())))
            self.msg.setWindowTitle(self.tr("Save in XTF Transfer File"))
            self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box = self.msg.exec_()
            if msg_box == QMessageBox.No:
                return

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))
            self.txtStdout.clear()

            exporter = iliexporter.Exporter()
            exporter.tool = self.type_combo_box.currentData()
            exporter.configuration = configuration

            self.save_configuration(configuration)

            exporter.stdout.connect(self.print_info)
            exporter.stderr.connect(self.on_stderr)
            exporter.process_started.connect(self.on_process_started)
            exporter.process_finished.connect(self.on_process_finished)

            self.progress_bar.setValue(25)

            try:
                if exporter.run(edited_command) != iliexporter.Exporter.SUCCESS:
                    if configuration.db_ili_version == 3:
                        # failed with a db created by ili2db version 3
                        if not edited_command:
                            # fallback because of issues with --export3 argument
                            self.show_message(Qgis.Warning, self.tr('Tried export with ili2db version 3.x.x (fallback)'))

                            exporter.version = 3
                            # ... and enforce the Exporter to use ili2db version 3.x.x
                            if exporter.run() != iliexporter.Exporter.SUCCESS:
                                self.enable()
                                self.progress_bar.hide()
                                return
                        else:
                            self.show_message(Qgis.Warning, self.tr('Tried export with ili2db version 3.x.x (no fallback with editted command)'))
                            return
                    else:
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

    def print_info(self, text):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)
        self.advance_progress_bar_by_text(text)
        QCoreApplication.processEvents()

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)

    def on_process_started(self, command):
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        color = '#004905' if exit_code == 0 else '#aa2222'
        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(self.tr('Finished ({})'.format(exit_code)))
        if result == iliexporter.Exporter.SUCCESS:
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            if self.export_without_validate():
                self.set_button_to_export_without_validation()
            self.enable()

    def export_without_validate(self):
        """
        Valid if an error occurred that prevents executing the export without validations
        :return: True if you can execute the export without validations, False in other case
        """
        log = self.txtStdout.toPlainText().lower()
        if "permission denied" in log or "access is denied" in log:
            return False
        return True

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = ili2dbconfig.ExportConfiguration()

        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)

        configuration.tool = mode
        configuration.xtffile = self.xtf_file_line_edit.text().strip()
        configuration.ilimodels = ';'.join(self.export_models_model.checked_models())
        configuration.base_configuration = self.base_configuration
        configuration.db_ili_version = self.db_ili_version(configuration)

        if not self.validate_data:
            configuration.disable_validation = True
        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue(
            'QgisModelBaker/ili2pg/xtffile_export', configuration.xtffile)
        settings.setValue('QgisModelBaker/importtype',
                          self.type_combo_box.currentData().name)

        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()

    def restore_configuration(self):
        settings = QSettings()

        for db_id in self.db_simple_factory.get_db_list(False):
            configuration = iliexporter.ExportConfiguration()
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value('QgisModelBaker/importtype')
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.refresh_db_panel()

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
        self.set_button_to_export()
        self.refresh_db_panel()
        self.refresh_models()
        self.txtStdout.clear()

    def refresh_db_panel(self):
        self.progress_bar.hide()

        db_id = self.type_combo_box.currentData()
        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        # Refresh panels
        for key, value in self._lst_panel.items():
            value.interlis_mode = False
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgisModelBaker/ili2db')
                self.base_configuration.save(settings)
        else:
            QDesktopServices.openUrl(link)

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#export-an-interlis-transfer-file-xtf".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#export-an-interlis-transfer-file-xtf")

    def xtf_browser_opened_to_true(self):
        """
        Slot. Sets a flag to true to eventually avoid asking a user whether to overwrite a file.
        """
        self.xtf_browser_was_opened = True

    def xtf_browser_opened_to_false(self):
        """
        Slot. Sets a flag to false to eventually ask a user whether to overwrite a file.
        """
        self.xtf_browser_was_opened = False

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models…':
            self.progress_bar.setValue(50)
        elif text.strip() == 'Info: create table structure…':
            self.progress_bar.setValue(75)
