from projectgenerator.utils.qt_utils import make_file_selector
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtCore import QCoreApplication, QSettings
from qgis.core import QgsProject
from ..utils import get_ui_class
from ..libili2pg import iliimporter
from ..libqgsprojectgen.generator.postgres import Generator
from ..libqgsprojectgen.dataobjects import Project

DIALOG_UI = get_ui_class('generate_project.ui')


class GenerateProjectDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(self.tr('Create'), QDialogButtonBox.AcceptRole)
        self.ili_file_browse_button.clicked.connect(make_file_selector(self.ili_file_line_edit, title=self.tr('Open Interlis Model'), file_filter=self.tr('Interlis Model File (*.ili)')))
        self.type_combo_box.clear()
        self.type_combo_box.addItem(self.tr('Interlis'), 'ili')
        self.type_combo_box.addItem(self.tr('Postgis'), 'pg')
        self.type_combo_box.currentIndexChanged.connect(self.type_changed)

        self.restore_configuration()

    def accepted(self):
        configuration = iliimporter.Configuration()

        configuration.host = self.pg_host_line_edit.text()
        configuration.user = self.pg_user_line_edit.text()
        configuration.database = self.pg_database_line_edit.text()
        configuration.schema = self.pg_schema_line_edit.text()
        configuration.password = self.pg_password_line_edit.text()

        if self.type_combo_box.currentData() == 'ili':
            configuration.ilifile = self.ili_file_line_edit.text()

            importer = iliimporter.Importer()

            importer.configuration = configuration

            self.save_configuration(configuration)

            importer.stdout.connect(self.print_info)
            importer.stderr.connect(self.on_stderr)
            importer.process_started.connect(self.on_process_started)
            importer.process_finished.connect(self.on_process_finished)
            if importer.run() != iliimporter.Importer.SUCCESS:
                return

        generator = Generator(configuration.uri)
        available_layers = generator.layers()
        relations = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations

        qgis_project = QgsProject.instance()
        project.layer_added.connect(self.print_info)
        project.create(None, qgis_project)

    def print_info(self, text):
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        self.txtStdout.setTextColor(QColor('#aa2222'))
        self.txtStdout.append(text)
        self.txtStdout.setTextColor(QColor('#000000'))
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.disable()
        self.txtStdout.setTextColor(QColor('#777777'))
        self.txtStdout.setText(command)
        self.txtStdout.setTextColor(QColor('#000000'))
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        self.txtStdout.setTextColor(QColor('#777777'))
        self.txtStdout.append('Finished ({})'.format(exit_code))
        if result == iliimporter.Importer.SUCCESS:
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            self.enable()
        self.txtStdout.setTextColor(QColor('#000000'))

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2pg/ilifile', configuration.ilifile)
        settings.setValue('QgsProjectGenerator/ili2pg/host', configuration.host)
        settings.setValue('QgsProjectGenerator/ili2pg/user', configuration.user)
        settings.setValue('QgsProjectGenerator/ili2pg/database', configuration.database)
        settings.setValue('QgsProjectGenerator/ili2pg/schema', configuration.schema)
        settings.setValue('QgsProjectGenerator/ili2pg/password', configuration.password)
        settings.setValue('QgsProjectGenerator/importtype', self.type_combo_box.currentData())

    def restore_configuration(self):
        settings = QSettings()

        self.ili_file_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/ilifile'))
        self.pg_host_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/host', 'localhost'))
        self.pg_user_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/user'))
        self.pg_database_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/database'))
        self.pg_schema_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/schema'))
        self.pg_password_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/password'))
        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(settings.value('QgsProjectGenerator/importtype', 'pg')))
        self.type_changed()

    def disable(self):
        self.pg_config.setEnabled(False)
        self.ili_config.setEnabled(False)
        self.buttonBox.setEnabled(False)

    def enable(self):
        self.pg_config.setEnabled(True)
        self.ili_config.setEnabled(True)
        self.buttonBox.setEnabled(True)

    def type_changed(self):
        if self.type_combo_box.currentData() == 'ili':
            self.ili_config.show()
        else:
            self.ili_config.hide()
