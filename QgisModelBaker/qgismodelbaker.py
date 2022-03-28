# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2017-01-27
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
import configparser
import datetime
import locale
import os
import pathlib
import webbrowser

import pyplugin_installer
from qgis.core import QgsProject
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QEvent,
    QLocale,
    QObject,
    QSettings,
    QStandardPaths,
    Qt,
    QTranslator,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.utils import available_plugins

from QgisModelBaker.gui.dataset_manager import DatasetManagerDialog
from QgisModelBaker.gui.drop_message import DropMessageDialog
from QgisModelBaker.gui.export import ExportDialog
from QgisModelBaker.gui.generate_project import GenerateProjectDialog
from QgisModelBaker.gui.import_data import ImportDataDialog
from QgisModelBaker.gui.options import OptionsDialog
from QgisModelBaker.gui.panel.dataset_selector import DatasetSelector
from QgisModelBaker.gui.validate import ValidateDock
from QgisModelBaker.gui.workflow_wizard.workflow_wizard import WorkflowWizardDialog
from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration
from QgisModelBaker.utils.gui_utils import DropMode


class QgisModelBakerPlugin(QObject):
    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.generate_dlg = None
        self.export_dlg = None
        self.importdata_dlg = None
        self.workflow_wizard_dlg = None
        self.datasetmanager_dlg = None

        self.__generate_action = None
        self.__export_action = None
        self.__importdata_action = None
        self.__workflow_wizard_action = None
        self.__datasetmanager_action = None
        self.__validate_action = None
        self.__configure_action = None
        self.__help_action = None
        self.__about_action = None
        self.__separator = None
        self.__dataset_selector_action = None
        self.__dataset_selector = None
        self.__validate_dock = None
        basepath = pathlib.Path(__file__).parent.absolute()
        metadata = configparser.ConfigParser()
        metadata.read(os.path.join(basepath, "metadata.txt"))
        self.__version__ = metadata["general"]["version"]
        if locale.getlocale() == (None, None):
            locale.setlocale(locale.LC_ALL, "")

        # initialize translation
        qgis_locale_id = str(QSettings().value("locale/userLocale"))
        qgis_locale = QLocale(qgis_locale_id)
        locale_path = os.path.join(self.plugin_dir, "i18n")
        self.translator = QTranslator()
        self.translator.load(qgis_locale, "QgisModelBaker", "_", locale_path)
        QCoreApplication.installTranslator(self.translator)

        self.ili2db_configuration = BaseConfiguration()
        settings = QSettings()
        settings.beginGroup("QgisModelBaker/ili2db")
        self.ili2db_configuration.restore(settings)

        self.event_filter = DropFileFilter(self)

    def register_event_filter(self):
        if not self.event_filter:
            self.event_filter = DropFileFilter(self)
        self.iface.mainWindow().installEventFilter(self.event_filter)

    def unregister_event_filter(self):
        if self.event_filter:
            self.iface.mainWindow().removeEventFilter(self.event_filter)
            self.event_filter.deleteLater()

    def initGui(self):
        pyplugin_installer.installer.initPluginInstaller()
        pyplugin_installer.installer_data.plugins.rebuild()

        if "projectgenerator" in available_plugins:
            pyplugin_installer.instance().uninstallPlugin(
                "projectgenerator", quiet=True
            )
        self.__generate_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__), "images/QgisModelBaker-generate-icon.svg"
                )
            ),
            self.tr("Generate"),
            None,
        )
        self.__export_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "images/QgisModelBaker-xtf-export-icon.svg",
                )
            ),
            self.tr("Export Interlis Transfer File (.xtf)"),
            None,
        )
        self.__importdata_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "images/QgisModelBaker-xtf-import-icon.svg",
                )
            ),
            self.tr("Import Interlis Transfer File (.xtf)"),
            None,
        )
        self.__datasetmanager_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "images/QgisModelBaker-datasetmanager-icon.svg",
                )
            ),
            self.tr("Dataset Manager"),
            None,
        )
        self.__validate_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "images/QgisModelBaker-validator_icon.svg",
                )
            ),
            self.tr("Data Validator"),
            None,
        )
        self.__workflow_wizard_action = QAction(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__), "images/QgisModelBaker-wizard.svg"
                )
            ),
            self.tr("Import/Export Wizard"),
            None,
        )
        self.__configseparator = QAction(None)
        self.__configseparator.setSeparator(True)
        self.__dataset_selector_action = QAction(self.tr("Dataset Selector"))
        self.__configure_action = QAction(self.tr("Settings"), None)
        self.__infoseparator = QAction(None)
        self.__infoseparator.setSeparator(True)
        self.__help_action = QAction(self.tr("Help"), None)
        self.__about_action = QAction(self.tr("About"), None)

        # set these actions checkable to visualize that the dialog is open
        self.__generate_action.setCheckable(True)
        self.__export_action.setCheckable(True)
        self.__importdata_action.setCheckable(True)
        self.__workflow_wizard_action.setCheckable(True)
        self.__datasetmanager_action.setCheckable(True)
        self.__validate_action.setCheckable(True)

        self.__generate_action.triggered.connect(self.show_generate_dialog)
        self.__configure_action.triggered.connect(self.show_options_dialog)
        self.__importdata_action.triggered.connect(self.show_importdata_dialog)
        self.__datasetmanager_action.triggered.connect(self.show_datasetmanager_dialog)
        self.__validate_action.triggered.connect(self.show_validate_dock)
        self.__export_action.triggered.connect(self.show_export_dialog)
        self.__workflow_wizard_action.triggered.connect(
            self.show_workflow_wizard_dialog
        )
        self.__help_action.triggered.connect(self.show_help_documentation)
        self.__about_action.triggered.connect(self.show_about_dialog)

        self.iface.addPluginToDatabaseMenu(
            self.tr("Model Baker"), self.__workflow_wizard_action
        )
        self.iface.addPluginToDatabaseMenu(
            self.tr("Model Baker"), self.__validate_action
        )
        self.iface.addPluginToDatabaseMenu(
            self.tr("Model Baker"), self.__configseparator
        )
        self.iface.addPluginToDatabaseMenu(
            self.tr("Model Baker"), self.__datasetmanager_action
        )
        self.iface.addPluginToDatabaseMenu(
            self.tr("Model Baker"), self.__configure_action
        )
        self.iface.addPluginToDatabaseMenu(self.tr("Model Baker"), self.__infoseparator)
        self.iface.addPluginToDatabaseMenu(self.tr("Model Baker"), self.__help_action)
        self.iface.addPluginToDatabaseMenu(self.tr("Model Baker"), self.__about_action)

        self.toolbar = self.iface.addToolBar(self.tr("Model Baker"))
        self.toolbar.setObjectName("ModelBakerToolbar")
        self.toolbar.setToolTip(self.tr("Model Baker Toolbar"))
        self.toolbar.addAction(self.__workflow_wizard_action)
        self.__dataset_selector = DatasetSelector()
        self.__dataset_selector_action = self.toolbar.addWidget(self.__dataset_selector)
        # connect trigger to refresh model of dataset combobox when layer changed
        self.iface.layerTreeView().currentLayerChanged.connect(
            self.__dataset_selector.set_current_layer
        )
        self.toolbar.addAction(self.__datasetmanager_action)
        self.init_validate_dock()
        self.register_event_filter()

    def unload(self):
        self.unregister_event_filter()
        self.iface.removePluginDatabaseMenu(
            self.tr("Model Baker"), self.__datasetmanager_action
        )
        self.iface.removePluginDatabaseMenu(
            self.tr("Model Baker"), self.__validate_action
        )
        self.iface.removePluginDatabaseMenu(
            self.tr("Model Baker"), self.__configure_action
        )
        self.iface.removePluginDatabaseMenu(self.tr("Model Baker"), self.__help_action)
        self.iface.removePluginDatabaseMenu(self.tr("Model Baker"), self.__about_action)
        self.toolbar.removeAction(self.__dataset_selector_action)

        self.iface.layerTreeView().currentLayerChanged.disconnect(
            self.__dataset_selector.set_current_layer
        )
        del self.__generate_action
        del self.__export_action
        del self.__importdata_action
        del self.__workflow_wizard_action
        del self.__datasetmanager_action
        del self.__validate_action
        del self.__configure_action
        del self.__help_action
        del self.__about_action
        del self.__dataset_selector_action
        del self.__dataset_selector
        # remove the toolbar
        del self.toolbar

        self.remove_validate_dock()

    def show_generate_dialog(self):
        if self.generate_dlg:
            self.generate_dlg.reject()
        else:
            self.generate_dlg = GenerateProjectDialog(
                self.iface, self.ili2db_configuration, self.iface.mainWindow()
            )
            self.generate_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.generate_dlg.setWindowFlags(self.generate_dlg.windowFlags() | Qt.Tool)
            self.generate_dlg.show()
            self.generate_dlg.finished.connect(self.generate_dialog_finished)
            self.__generate_action.setChecked(True)

    def generate_dialog_finished(self):
        self.__generate_action.setChecked(False)
        self.generate_dlg = None

    def show_export_dialog(self):
        if self.export_dlg:
            self.export_dlg.reject()
        else:
            self.export_dlg = ExportDialog(
                self.ili2db_configuration, self.iface.mainWindow()
            )
            self.export_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.export_dlg.setWindowFlags(self.export_dlg.windowFlags() | Qt.Tool)
            self.export_dlg.show()
            self.export_dlg.finished.connect(self.export_dialog_finished)
            self.__export_action.setChecked(True)

    def export_dialog_finished(self):
        self.__export_action.setChecked(False)
        self.export_dlg = None

    def show_workflow_wizard_dialog(self):
        if self.workflow_wizard_dlg:
            self.workflow_wizard_dlg.reject()
        else:
            self.workflow_wizard_dlg = WorkflowWizardDialog(
                self.iface, self.ili2db_configuration, self.iface.mainWindow()
            )
            self.workflow_wizard_dlg.show()

            self.workflow_wizard_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.workflow_wizard_dlg.setWindowFlags(
                self.workflow_wizard_dlg.windowFlags() | Qt.Tool
            )
            self.workflow_wizard_dlg.show()
            self.workflow_wizard_dlg.finished.connect(
                self.workflow_wizard_dialog_finished
            )
            self.__workflow_wizard_action.setChecked(True)

    def workflow_wizard_dialog_finished(self):
        self.__workflow_wizard_action.setChecked(False)
        self.workflow_wizard_dlg = None

    def show_importdata_dialog(self):
        if self.importdata_dlg:
            self.importdata_dlg.reject()
        else:
            self.importdata_dlg = ImportDataDialog(
                self.iface, self.ili2db_configuration, self.iface.mainWindow()
            )
            self.importdata_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.importdata_dlg.setWindowFlags(
                self.importdata_dlg.windowFlags() | Qt.Tool
            )
            self.importdata_dlg.show()
            self.importdata_dlg.finished.connect(self.importdata_dialog_finished)
            self.__importdata_action.setChecked(True)

    def importdata_dialog_finished(self):
        self.__importdata_action.setChecked(False)
        self.importdata_dlg = None

    def show_datasetmanager_dialog(self):
        if self.datasetmanager_dlg:
            self.datasetmanager_dlg.reject()
        else:
            self.datasetmanager_dlg = DatasetManagerDialog(
                self.iface, self.iface.mainWindow()
            )
            self.datasetmanager_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.datasetmanager_dlg.setWindowFlags(
                self.datasetmanager_dlg.windowFlags() | Qt.Tool
            )
            self.datasetmanager_dlg.show()
            self.datasetmanager_dlg.finished.connect(
                self.datasetmanager_dialog_finished
            )
            self.__datasetmanager_action.setChecked(True)

    def datasetmanager_dialog_finished(self):
        self.__dataset_selector.reset_model(self.iface.layerTreeView().currentLayer())
        self.__datasetmanager_action.setChecked(False)
        self.datasetmanager_dlg = None

    def show_validate_dock(self):
        self.__validate_dock.setVisible(not self.__validate_dock.isVisible())

    def show_options_dialog(self):
        dlg = OptionsDialog(self.ili2db_configuration)
        if dlg.exec_():
            settings = QSettings()
            settings.beginGroup("QgisModelBaker/ili2db")
            self.ili2db_configuration.save(settings)

    def show_help_documentation(self):
        os_language = QLocale(QSettings().value("locale/userLocale")).name()[:2]
        if os_language in ["es", "de"]:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/{}/".format(os_language)
            )
        else:
            webbrowser.open("https://opengisch.github.io/QgisModelBaker/index.html")

    def show_about_dialog(self):
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setTextFormat(Qt.RichText)
        self.msg.setWindowTitle(self.tr("About Model Baker"))
        self.msg.setText(
            """<h1>{title}</h1>
        <p align="justify"><small>{version}</small></p>
        <p align="justify">{p1}</p>
        <p align="justify">{p2}</p>
        <p align="justify">{p3}</p>""".format(
                title=self.tr("QGIS Model Baker"),
                version=self.tr("Version {version}").format(version=self.__version__),
                p1=self.tr(
                    "Configuring QGIS layers and forms manually is a tedious and error prone process. This plugin loads database schemas with various meta information to preconfigure the layer tree, widget configuration, relations and more."
                ),
                p2=self.tr(
                    'This project is open source under the terms of the GPLv2 or later and the source code can be found on <a href="https://github.com/opengisch/QgisModelBaker">github</a>.'
                ),
                p3=self.tr(
                    'This plugin is developed by <a href="https://www.opengis.ch/">OPENGIS.ch</a> in collaboration with <a href="https://swisstierrascolombia.com">SwissTierras Colombia</a>'
                ),
            )
        )
        self.msg.setStandardButtons(QMessageBox.Close)
        self.msg.exec_()

    def init_validate_dock(self):
        settings = QSettings()
        self.__validate_dock = ValidateDock(self.ili2db_configuration, self.iface)
        self.iface.addDockWidget(
            settings.value(
                "QgisModelBaker/validate_dock/area", Qt.RightDockWidgetArea, type=int
            ),
            self.__validate_dock,
        )
        self.__validate_dock.visibilityChanged.connect(
            self.__validate_action.setChecked
        )
        self.__validate_dock.setVisible(
            settings.value("QgisModelBaker/validate_dock/isVisible", False, type=bool)
        )
        self.iface.layerTreeView().currentLayerChanged.connect(
            self.__validate_dock.set_current_layer
        )

    def remove_validate_dock(self):
        settings = QSettings()
        settings.setValue(
            "QgisModelBaker/validate_dock/area",
            self.iface.mainWindow().dockWidgetArea(self.__validate_dock),
        )
        settings.setValue(
            "QgisModelBaker/validate_dock/isVisible", self.__validate_dock.isVisible()
        )
        self.__validate_dock.setVisible(False)
        self.iface.removeDockWidget(self.__validate_dock)
        self.iface.layerTreeView().currentLayerChanged.disconnect(
            self.__validate_dock.set_current_layer
        )
        del self.__validate_dock

    def get_generator(self):
        return Generator

    def create_project(
        self,
        layers,
        relations,
        bags_of_enum,
        legend,
        auto_transaction=True,
        evaluate_default_values=True,
        group=None,
    ):
        """
        Expose the main functionality from Model Baker to other plugins,
        namely, create a QGIS project from objects obtained from the Generator
        class.

        :param layers: layers object from generator.layers
        :param relations: relations object obtained from generator.relations
        :param bags_of_enum: bags_of_enum object from generator.relations
        :param legend: legend object obtained from generator.legend
        :param auto_transaction: whether transactions should be enabled or not
                                 when editing layers from supported DB like PG
        :param evaluate_default_values: should default values be evaluated on
                                        provider side when requested and not
                                        when committed. (from QGIS docs)
        """
        project = Project(auto_transaction, evaluate_default_values)
        project.layers = layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()
        qgis_project = QgsProject.instance()
        project.create(None, qgis_project, group)

    def handle_dropped_files(self, dropped_files):
        if not self.workflow_wizard_dlg:
            self._set_dropped_file_configuration()
            self.show_workflow_wizard_dialog()
        self.workflow_wizard_dlg.append_dropped_files(dropped_files)
        return True

    def _set_dropped_file_configuration(self):
        settings = QSettings()
        settings.setValue("QgisModelBaker/importtype", "gpkg")
        output_file_name = "temp_db_{:%Y%m%d%H%M%S%f}.gpkg".format(
            datetime.datetime.now()
        )
        settings.setValue(
            "QgisModelBaker/ili2gpkg/dbfile",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                output_file_name,
            ),
        )


class DropFileFilter(QObject):
    def __init__(self, parent=None):
        super(DropFileFilter, self).__init__(parent.iface.mainWindow())
        self.parent = parent

    def _is_handling_requested(self, dropped_files):
        settings = QSettings()
        drop_mode = DropMode[
            settings.value("QgisModelBaker/drop_mode", DropMode.ASK.name, str)
        ]
        if drop_mode == DropMode.ASK:
            drop_message_dialog = DropMessageDialog(dropped_files)
            return drop_message_dialog.exec_()
        return drop_mode == DropMode.YES

    def eventFilter(self, obj, event):
        """
        When files are dropped, then ask to use it in the model baker.
        """
        if event.type() == QEvent.Drop:
            dropped_files = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if pathlib.Path(url.toLocalFile()).suffix[1:]
                in ["xtf", "XTF", "itf", "ITF", "ili"]
            ]
            additional_xml_files = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if pathlib.Path(url.toLocalFile()).suffix[1:] in ["xml", "XML"]
            ]
            if dropped_files:
                if self._is_handling_requested(dropped_files + additional_xml_files):
                    if self.parent.handle_dropped_files(
                        dropped_files + additional_xml_files
                    ):
                        return True
        return False
