"""
/***************************************************************************
                              -------------------
        begin                : 16.06.2025
        git sha              : :%H$
        copyright            : (C) 2025 by Dave Signer
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

import datetime
import logging
import logging.handlers
import os

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QObject, QStandardPaths
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget

from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper import iliimporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    ImportDataConfiguration,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError


class QuickXtfBaker(QObject):
    """
    This class provides the functionality for a quick import of dropped xtf files.
    It generates a GeoPackage in the temporary directory withouth any constraints and imports the data without any validation.
    The project layers are then generated with raw sql names.
    """

    def __init__(self, parent=None):
        super().__init__(parent.iface.mainWindow())
        self.parent = parent
        self.iface = self.parent.iface
        self.message_bar = self.iface.messageBar()

    def push_message_bar(
        self,
        message,
        running=False,
        level=Qgis.MessageLevel.Info,
        timeout=0,
        show_log_button=False,
    ):
        """
        Function to push a widget to the QGIS message bar containing info text and busy bar.
        """
        layout = QHBoxLayout()

        if running:
            busy_bar = QProgressBar()
            busy_bar.setRange(0, 0)
            busy_bar.setVisible(True)
            layout.addWidget(busy_bar)

        text_label = QLabel()
        text_label.setText(message)
        layout.addWidget(text_label)

        if show_log_button:
            button = QPushButton()
            button.clicked.connect(lambda: self.parent.show_logs_folder())
            button.setText(self.tr("Show log folder"))
            layout.addWidget(button)

        message_widget = QWidget()
        message_widget.setLayout(layout)

        self.message_bar.clearWidgets()
        self.message_bar.pushWidget(message_widget, level, timeout)
        self.log(f"Push to message bar: {message}", level)

    def handle_dropped_files(self, dropped_files, dropped_ini_files):

        """
        Main function receiving the files and trigger import to single GeoPackages.
        After that it generates the layer via modelbaker generator.
        """

        self.push_message_bar(
            self.tr("Quick'n'dirty XTF import with QuickXtfBaker starts..."), True
        )
        # one GeoPackage per file

        status_map = {}
        suc_files = set()
        failed_files = set()

        for file in dropped_files:
            self.push_message_bar(self.tr("Import {}").format(file), True)
            status, db_file = self.import_file(file)
            status_map[file] = {}
            status_map[file]["status"] = status
            status_map[file]["db_file"] = db_file
            if status:
                suc_files.add(file)
            else:
                failed_files.add(file)

        if len(failed_files) > 0 and len(dropped_ini_files) > 0:
            self.log("Retry failed XTF imports with the dropped model files")
            for file in failed_files:
                status = False
                db_file = None
                for ini_file in dropped_ini_files:
                    status, db_file = self.import_file(ini_file)
                    if not status:
                        # on faile, try with the next model
                        continue
                    # otherwise try to import data to the resulting db_file
                    status, db_file = self.import_file(file, db_file)
                    if status:
                        break
                if status:
                    self.log(f"Succeeded to import {file} with model file")
                    status_map[file]["status"] = status
                    status_map[file]["db_file"] = db_file
                    failed_files.remove(file)
                    suc_files.add(file)

        for key in suc_files:
            self.push_message_bar(
                self.tr("Generate layers of {}").format(status_map[key]["db_file"]),
                True,
            )
            self.generate_project(status_map[key]["db_file"])

        self.push_message_bar(
            self.tr("Import of {} successful and {} failed.").format(
                len(suc_files), len(failed_files)
            ),
            False,
            Qgis.MessageLevel.Warning
            if len(failed_files) > 0
            else Qgis.MessageLevel.Success,
            15,
            bool(len(failed_files)),
        )
        return True

    def import_file(self, single_file, db_file=None):
        """
        Function to create a GeoPackage in the temporary directory without any constraints and import the data without any validation.
        """
        importer = iliimporter.Importer(dataImport=True)

        configuration = ImportDataConfiguration()
        base_config = (
            self.parent.ili2db_configuration
        )  # taking custom model repository if configured
        configuration.base_configuration = base_config
        configuration.tool = DbIliMode.ili2gpkg
        configuration.xtffile = single_file
        # in case a db_file is passed we take it and otherwise we don't
        configuration.dbfile = db_file or os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.TempLocation),
            "temp_db_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )

        # parameters to import the data "dirty" (without validation and constraints)
        configuration.inheritance = None
        configuration.disable_validation = True
        # in case a db_file is passed we don't create schema, otherwise we do
        if not db_file:
            configuration.with_schemaimport = True

        importer.configuration = configuration
        importer.tool = configuration.tool

        importer.stdout.connect(self.on_ili_stdout)
        importer.stderr.connect(self.on_ili_stderr)
        importer.process_started.connect(self.on_ili_process_started)
        importer.process_finished.connect(self.on_ili_process_finished)
        result = True

        try:
            if importer.run() != iliimporter.IliExecutable.SUCCESS:
                result = False
        except JavaNotFoundError as e:
            self.log(
                self.tr("Java not found error: {}").format(e.error_string),
                Qgis.MessageLevel.Warning,
            )
            result = False

        return result, importer.configuration.dbfile

    def import_model(self, single_model_file):
        """
        Function used as fallback in case we cannot work with doSchemaImport (in case model is not in repo).
        Here we create the schema without importing the data.
        """
        importer = iliimporter.Importer(dataImport=True)

        configuration = SchemaImportConfiguration()
        base_config = (
            self.parent.ili2db_configuration
        )  # taking custom model repository if configured
        configuration.base_configuration = base_config
        configuration.tool = DbIliMode.ili2gpkg
        configuration.ilifile = single_model_file
        configuration.dbfile = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.TempLocation),
            "temp_db_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )

        # parameters to import the data "dirty" (without validation and constraints)
        configuration.inheritance = None
        configuration.disable_validation = True

        importer.configuration = configuration
        importer.tool = configuration.tool

        importer.stdout.connect(self.on_ili_stdout)
        importer.stderr.connect(self.on_ili_stderr)
        importer.process_started.connect(self.on_ili_process_started)
        importer.process_finished.connect(self.on_ili_process_finished)
        result = True

        try:
            if importer.run() != iliimporter.IliExecutable.SUCCESS:
                result = False
        except JavaNotFoundError as e:
            self.log(
                self.tr("Java not found error: {}").format(e.error_string),
                Qgis.MessageLevel.Warning,
            )
            result = False

        return result, importer.configuration.dbfile

    def generate_project(self, db_file):
        generator = Generator(DbIliMode.ili2gpkg, db_file, None, raw_naming=True)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

    def on_ili_stdout(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"ili2db: {line}"
            self.log(text, Qgis.MessageLevel.Info)

    def on_ili_stderr(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"ili2db: {line}"
            self.log(text, Qgis.MessageLevel.Critical)

    def on_ili_process_started(self, command):
        text = f"ili2db: {command}"
        self.log(text, Qgis.MessageLevel.Info)

    def on_ili_process_finished(self, exit_code, result):
        if exit_code == 0:
            text = f"ili2db: Successfully performed command."
            self.log(text, Qgis.MessageLevel.Info)
        else:
            text = f"ili2db: Finished with errors: {result}"
            self.log(text, Qgis.MessageLevel.Critical)

    def log(self, message, level=Qgis.MessageLevel.Info):
        log_text = f"QuickXtfBaker: {message}"
        if level == Qgis.MessageLevel.Warning:
            logging.warning(message)
        elif level == Qgis.MessageLevel.Critical:
            logging.error(message)
        else:
            logging.info(message)
