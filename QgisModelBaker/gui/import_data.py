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

import webbrowser
import re

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.options import OptionsDialog, CompletionLineEdit
from QgisModelBaker.gui.multiple_models import MultipleModelsDialog
from QgisModelBaker.libili2db.ilicache import IliCache, ModelCompleterDelegate
from QgisModelBaker.libili2db.ili2dbutils import (
    color_log_text,
    JavaNotFoundError
)
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType

from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    Validators,
    FileValidator,
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
    QGridLayout
)
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    Qt,
    QLocale
)
from ..utils import get_ui_class
from ..libili2db import (
    iliimporter,
    ili2dbconfig
)

from qgis.gui import (
    QgsMessageBar,
    QgsGui
)

from qgis.core import Qgis

DIALOG_UI = get_ui_class('import_data.ui')


class ImportDataDialog(QDialog, DIALOG_UI):

    ValidExtensions = ['xtf', 'XTF', 'itf', 'ITF', 'pdf', 'PDF', 'xml', 'XML', 'xls', 'XLS', 'xlsx', 'XLSX']

    ModelMissingRegExp = re.compile('Error: failed to query .*\.t_ili2db_seq')

    def __init__(self, iface, base_config, parent=None):

        QDialog.__init__(self, parent)
        self.iface = iface
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self);
        self.db_simple_factory = DbSimpleFactory()
        self.buttonBox.accepted.disconnect()
        self.buttonBox.clicked.connect(self.button_box_clicked)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)

        self.import_button_name = self.tr('Import Data')
        self.import_without_validate_button_name = self.tr('Import without validation')

        self.buttonBox.addButton(self.import_button_name, QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.xtf_file_browse_button.clicked.connect(
            make_file_selector(self.xtf_file_line_edit, title=self.tr('Open Transfer or Catalog File'),
                               file_filter=self.tr('Transfer File (*.xtf *.itf *.XTF *.ITF);;Catalogue File (*.xml *.XML *.xls *.XLS *.xlsx *.XLSX)')))

        self.type_combo_box.clear()
        self._lst_panel = dict()

        for db_id in self.db_simple_factory.get_db_list(False):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)
            db_factory = self.db_simple_factory.create_factory(db_id)
            item_panel = db_factory.get_config_panel(self, DbActionType.IMPORT_DATA)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.type_combo_box.currentIndexChanged.connect(self.type_changed)
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.multiple_models_dialog = MultipleModelsDialog(self)
        self.multiple_models_button.clicked.connect(
            self.multiple_models_dialog.open)
        self.multiple_models_dialog.accepted.connect(
            self.fill_models_line_edit)

        self.validate_data = True # validates imported data by default, We use --disableValidation when is False
        self.base_configuration = base_config
        self.restore_configuration()

        self.validators = Validators()
        fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions])

        self.xtf_file_line_edit.setValidator(fileValidator)

        self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model in repository]'))
        self.ili_models_line_edit.textChanged.connect(self.complete_models_completer)
        self.ili_models_line_edit.punched.connect(self.complete_models_completer)

        self.xtf_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.emit(
            self.xtf_file_line_edit.text())

        # Remove import without validate button when xtf changes
        self.xtf_file_line_edit.textChanged.connect(
            self.remove_import_without_validate_button)

        settings = QSettings()
        ilifile = settings.value('QgisModelBaker/ili2db/ilifile')
        self.ilicache = IliCache(base_config, ilifile or None)
        self.update_models_completer()
        self.ilicache.refresh()

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

    def button_box_clicked(self, button):
        if self.buttonBox.buttonRole(button) == QDialogButtonBox.AcceptRole:
            if button.text() == self.import_button_name:
                self.validate_data = True
            elif button.text() == self.import_without_validate_button_name:
                self.validate_data = False
            self.accepted()

    def accepted(self):
        configuration = self.updated_configuration()

        if not self.xtf_file_line_edit.validator().validate(configuration.xtffile, 0)[0] == QValidator.Acceptable:
            self.txtStdout.setText(
                self.tr('Please set a valid INTERLIS transfer or catalogue file before importing data.'))
            self.xtf_file_line_edit.setFocus()
            return

        db_id = self.type_combo_box.currentData()
        res, message = self._lst_panel[db_id].is_valid()

        if not res:
            self.txtStdout.setText(message)
            return

        # create schema with superuser
        db_factory = self.db_simple_factory.create_factory(db_id)
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

            dataImporter = iliimporter.Importer(dataImport=True)

            dataImporter.tool = self.type_combo_box.currentData()
            dataImporter.configuration = configuration

            self.save_configuration(configuration)

            dataImporter.stdout.connect(self.print_info)
            dataImporter.stderr.connect(self.on_stderr)
            dataImporter.process_started.connect(self.on_process_started)
            dataImporter.process_finished.connect(self.on_process_finished)

            self.progress_bar.setValue(25)

            try:
                if dataImporter.run() != iliimporter.Importer.SUCCESS:
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

            self.refresh_layers()

    def refresh_layers(self):
        # refresh layers
        try:
            for layer in self.iface.mapCanvas().layers():
                layer.dataProvider().reloadData()
            self.iface.layerTreeView().layerTreeModel().recursivelyEmitDataChanged()
        except AttributeError:
            pass

    def print_info(self, text, text_color='#000000'):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)
        match = re.match(ImportDataDialog.ModelMissingRegExp, text)
        if match:
            color_log_text('=======================================================================', self.txtStdout)
            color_log_text(self.tr('It looks like the required schema for the imported data has not been generated.'), self.txtStdout)
            color_log_text(self.tr('Did you generate the model in the database?'), self.txtStdout)
            color_log_text(self.tr('Note: the model for a catalogue may be different from the data model itself.'), self.txtStdout)
            color_log_text('=======================================================================', self.txtStdout)
        self.advance_progress_bar_by_text(text)

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
        self.txtStdout.append('Finished ({})'.format(exit_code))
        if result == iliimporter.Importer.SUCCESS:
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            if self.import_without_validate():

                # button is removed to define order in GUI
                for button in self.buttonBox.buttons():
                    if button.text() == self.import_button_name:
                        self.buttonBox.removeButton(button)
                # Check if button was previously added
                self.remove_import_without_validate_button()

                self.buttonBox.addButton(self.import_without_validate_button_name,
                                         QDialogButtonBox.AcceptRole).setStyleSheet("color: #aa2222;")
                self.buttonBox.addButton(self.import_button_name, QDialogButtonBox.AcceptRole)

            self.enable()

    def import_without_validate(self):
        """
        Valid if an error occurred that prevents executing the import without validations
        :return: True if you can execute the import without validations, False in other case
        """
        log = self.txtStdout.toPlainText().lower()
        if "no models given" in log:
            return False
        if "attribute bid missing in basket" in log:
            return False
        return True

    def remove_import_without_validate_button(self):
        for button in self.buttonBox.buttons():
            if button.text() == self.import_without_validate_button_name:
                self.buttonBox.removeButton(button)
                self.validate_data = True

    def db_ili_version(self, configuration):
        """
        Returns the ili2db version the database has been created with or None if the database
        could not be detected as a ili2db database
        """
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri()

        db_connector = None

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
        configuration = ili2dbconfig.ImportDataConfiguration()

        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)

        configuration.tool = mode
        configuration.xtffile = self.xtf_file_line_edit.text().strip()
        configuration.delete_data = self.chk_delete_data.isChecked()
        configuration.ilimodels = self.ili_models_line_edit.text().strip()
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.base_configuration = self.base_configuration
        configuration.db_ili_version = self.db_ili_version(configuration)

        if not self.validate_data:
            configuration.disable_validation = True
        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue(
            'QgisModelBaker/ili2pg/xtffile_import', configuration.xtffile)
        settings.setValue(
            'QgisModelBaker/ili2pg/deleteData', configuration.delete_data)
        settings.setValue(
            'QgisModelBaker/importtype', self.type_combo_box.currentData().name)

        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()

    def restore_configuration(self):
        settings = QSettings()

        self.fill_toml_file_info_label()
        self.xtf_file_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/xtffile_import'))
        self.chk_delete_data.setChecked(settings.value(
            'QgisModelBaker/ili2pg/deleteData', False, bool))

        for db_id in self.db_simple_factory.get_db_list(False):
            configuration = iliimporter.ImportDataConfiguration()
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value('QgisModelBaker/importtype')
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.type_changed()

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
        self.remove_import_without_validate_button()
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
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#import-an-interlis-transfer-file-xtf".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#import-an-interlis-transfer-file-xtf")

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models...':
            self.progress_bar.setValue(50)
            QCoreApplication.processEvents()
        elif text.strip() == 'Info: create table structure...':
            self.progress_bar.setValue(75)
            QCoreApplication.processEvents()
