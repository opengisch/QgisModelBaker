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
import mmap
import os
import pathlib
import re
import xml.etree.ElementTree as CET

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QObject, QStandardPaths
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget

from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper import iliexecutable, iliimporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2CCommandConfiguration,
    ImportDataConfiguration,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import MODELS_BLACKLIST


class QuickVisualizer(QObject):
    """
    This class provides the functionality for a quick import of dropped xtf files.
    It generates a GeoPackage in the temporary directory withouth any constraints and imports the data without any validation.
    The project layers are then generated with raw sql names.
    """

    def __init__(self, parent=None):
        super().__init__(parent.iface.mainWindow())
        self.parent = parent
        self.logger = logging.getLogger("qgismodelbaker")
        self.message_bar = self.parent.iface.messageBar()

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

    def handle_dropped_files(self, dropped_files):

        """
        Main function receiving the files and trigger import to single GeoPackages.
        After that it generates the layer via modelbaker generator.
        """

        data_files = []
        model_files = []

        # separate data files from ini files
        for file in dropped_files:
            if os.path.isfile(file):
                if pathlib.Path(file).suffix[1:] in gui_utils.TransferExtensions:
                    data_files.append(file)
                else:
                    model_files.append(file)

        # one GeoPackage per file
        status_map = {}
        suc_files = set()
        failed_files = set()

        if len(data_files) == 0:
            self.push_message_bar(
                self.tr(
                    "Nothing to import with Quick Visualizer (use the Model Baker wizard instead)."
                ),
                False,
                Qgis.MessageLevel.Warning,
                15,
            )
            return suc_files, failed_files

        if len(model_files):
            self.log(
                f"Dropped model files are ignored {model_files} (but if not available in repo, they are used because they are in the same directory as the transfer files)."
            )

        self.push_message_bar(
            self.tr("Quick'n'dirty XTF import with QuickVisualizer starts..."), True
        )

        for file in data_files:
            self.push_message_bar(self.tr("Import {}").format(file), True)
            status, db_file = self.import_file(file, self.parent.ili2db_configuration)
            status_map[file] = {}
            status_map[file]["status"] = status
            status_map[file]["db_file"] = db_file
            if status:
                suc_files.add(file)
            else:
                failed_files.add(file)

        # this is a fallback: in case we have a custom model directory defined, it could be that we didn't found the model in the tranferfile's directory
        if (
            len(failed_files) > 0
            and self.parent.ili2db_configuration.custom_model_directories_enabled
            and "%XTF_DIR"
            not in self.parent.ili2db_configuration.custom_model_directories
        ):
            self.log(
                "Retry failed XTF imports with models in the same directory as the datafile"
            )
            base_config = self.parent.ili2db_configuration
            base_config.custom_model_directories += ";%XTF_DIR"
            failed_files_to_handle = failed_files.copy()
            for file in failed_files_to_handle:
                status, db_file = self.import_file(file, base_config)
                if status:
                    self.log(f"Succeeded to import {file} with model in directory")
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
        return suc_files, failed_files

    def import_file(self, single_file, base_config):
        """
        Function to create a GeoPackage in the temporary directory without any constraints and import the data without any validation.
        """
        importer = iliimporter.Importer(dataImport=True)

        configuration = ImportDataConfiguration()
        configuration.base_configuration = base_config
        configuration.tool = DbIliMode.ili2gpkg
        configuration.xtffile = single_file
        configuration.dbfile = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            "temp_db_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )

        # parameters to import the data "dirty" (without validation and constraints)
        configuration.inheritance = "smart2"
        configuration.disable_validation = True
        configuration.skip_reference_errors = True
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

    def generate_project(self, db_file):
        generator = Generator(DbIliMode.ili2gpkg, db_file, None)

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
        log_text = f"QuickVisualizer: {message}"
        if level == Qgis.MessageLevel.Warning:
            self.logger.warning(message)
        elif level == Qgis.MessageLevel.Critical:
            self.logger.error(message)
        else:
            self.logger.info(message)


class Ili2Pythonizer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent.iface.mainWindow())
        self.parent = parent
        self.logger = logging.getLogger("qgismodelbaker")
        self.message_bar = self.parent.iface.messageBar()

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

    def handle_dropped_files(self, dropped_files):

        """
        Main function receiving the files process.
        """

        data_files = []
        model_files = []

        # separate data files from ini files
        for file in dropped_files:
            if os.path.isfile(file):
                if pathlib.Path(file).suffix[1:] in gui_utils.TransferExtensions:
                    data_files.append(file)
                else:
                    model_files.append(file)

        # one GeoPackage per file
        status_map = {}
        suc_files = set()
        failed_files = set()

        if len(data_files) == 0:
            self.log(f"No data to import but we parse the models from it.")

        if len(model_files):
            self.log(f"Dropped model are used as well.")

        self.push_message_bar(
            self.tr("Pythonizing with Ili2Pythonizer starts..."), True
        )

        for data_file in data_files:
            self.push_message_bar(self.tr("Import {}").format(data_file), True)
            modelnames = self._transfer_file_models(data_file)

            self.push_message_bar(
                self.tr(f"Found those models in file {modelnames}"), True
            )

            # paths = download_model_files(modelnames)

        for model_file in model_files:
            self.push_message_bar(self.tr("Import {}").format(model_file), True)
            status, imd_file = self.create_imd(model_file)
            status_map[file] = {}
            status_map[file]["status"] = status
            status_map[file]["imd_file"] = imd_file
            if status:
                suc_files.add(file)
            else:
                failed_files.add(file)

        for key in suc_files:
            self.push_message_bar(
                self.tr("Created {}").format(status_map[key]["imd_file"]),
                True,
            )

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
        return suc_files, failed_files

    def create_imd(self, single_file):
        compiler = iliexecutable.IliCompiler()

        configuration = Ili2CCommandConfiguration()
        configuration.base_configuration = self.parent.ili2db_configuration
        configuration.ilifile = single_file
        configuration.imdfile = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            "temp_imd_{:%Y%m%d%H%M%S%f}.imd".format(datetime.datetime.now()),
        )

        # parameters to import the data "dirty" (without validation and constraints)
        configuration.o = "IMD16"

        compiler.configuration = configuration

        compiler.stdout.connect(self.on_ili_stdout)
        compiler.stderr.connect(self.on_ili_stderr)
        compiler.process_started.connect(self.on_ili_process_started)
        compiler.process_finished.connect(self.on_ili_process_finished)
        result = True

        try:
            if compiler.run() != compiler.SUCCESS:
                result = False
        except JavaNotFoundError as e:
            self.log(
                self.tr("Java not found error: {}").format(e.error_string),
                Qgis.MessageLevel.Warning,
            )
            result = False

        return result, compiler.configuration.imdfile

    def _transfer_file_models(self, data_file_path):
        """
        Get model names from an ITF file does a regex parse with mmap (to avoid long parsing time).
        Get model names from an XTF file. Since XTF can be very large, we make an iterparse of the models element.
        According to the namespace we decide if it's INTERLIS 2.3 or 2.4
        :param xtf_path: Path to an XTF file
        :return: List of model names from the datafile
        """
        models = []

        # parse models from ITF
        with open(data_file_path) as f:
            s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            matches = re.findall(rb"MODL (.*)", s)
            if matches:
                for match in matches:
                    model = {}
                    model["name"] = match.rstrip().decode()
                    models.append(model)
                return models

        try:
            models_element = None
            for event, elem in CET.iterparse(data_file_path, events=("end",)):
                ns = elem.tag.split("}")[0].strip("{")
                name = elem.tag.split("}")[1]
                if name.lower() == "models":
                    models_element = elem
                    break

            if models_element:
                for model_element in models_element:
                    ns = model_element.tag.split("}")[0].strip("{")
                    tagname = model_element.tag.split("}")[1]
                    modelname = None
                    if ns in [
                        "http://www.interlis.ch/xtf/2.4/INTERLIS",
                        "https://www.interlis.ch/xtf/2.4/INTERLIS",
                    ]:
                        if tagname == "model" and model_element.text is not None:
                            modelname = model_element.text
                    else:
                        if tagname == "MODEL" and "NAME" in model_element.attrib:
                            modelname = model_element.attrib["NAME"]

                    if modelname and modelname not in MODELS_BLACKLIST:
                        model = {}
                        model["name"] = modelname
                        models.append(model)

        except CET.ParseError as e:
            self.print_info.emit(
                self.tr(
                    "Could not parse transferfile file `{file}` ({exception})".format(
                        file=data_file_path, exception=str(e)
                    )
                )
            )
        return models

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
        log_text = f"QuickVisualizer: {message}"
        if level == Qgis.MessageLevel.Warning:
            self.logger.warning(message)
        elif level == Qgis.MessageLevel.Critical:
            self.logger.error(message)
        else:
            self.logger.info(message)
