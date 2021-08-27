# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 25.08.2021
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

from enum import Enum
import xml.etree.ElementTree as ET
import re
import os

from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt, pyqtSignal, QStringListModel

from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.ilicache import (
    IliCache,
)
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError

IliExtensions = ["ili"]
TransferExtensions = [
    "xtf",
    "XTF",
    "itf",
    "ITF",
    "pdf",
    "PDF",
    "xml",
    "XML",
    "xls",
    "XLS",
    "xlsx",
    "XLSX",
]

DEFAULT_DATASETNAME = "Baseset"

class PageIds():
    Intro = 1
    ImportSourceSeletion = 2
    ImportDatabaseSelection = 3
    GenerateDatabaseSelection = 4
    ImportSchemaConfiguration = 5
    ImportSchemaExecution = 6
    ImportDataConfiguration = 7
    ImportDataExecution = 8
    ExportDatabaseSelection = 9
    ExportDataConfiguration = 10
    ExportDataExecution = 11
    ProjectCreation = 12
class SourceModel(QStandardItemModel):
    """
    Model providing the data sources (files or repository items like models) and meta information like path or the chosen dataset
    """

    print_info = pyqtSignal([str], [str, str])

    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3
        DATASET_NAME = Qt.UserRole + 5

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)

    def flags(self, index):
        if index.column() > 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return "↑ ↓"
        return QStandardItemModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if role == Qt.DisplayRole:
            if index.column() > 0:
                return item.data(int(SourceModel.Roles.DATASET_NAME))
            if item.data(int(SourceModel.Roles.TYPE)) != "model":
                return self.tr("{} ({})").format(
                    item.data(int(Qt.DisplayRole)),
                    item.data(int(SourceModel.Roles.PATH)),
                )
        if role == Qt.DecorationRole:
            if index.column() == 0:
                type = "data"
                if item.data(int(SourceModel.Roles.TYPE)) and item.data(
                    int(SourceModel.Roles.TYPE)
                ).lower() in ["model", "ili", "xtf", "xml"]:
                    type = item.data(int(SourceModel.Roles.TYPE)).lower()
                return QIcon(
                    os.path.join(
                        os.path.dirname(__file__), f"../../images/file_types/{type}.png"
                    )
                )
        return item.data(int(role))

    def add_source(self, name, type, path):
        if self._source_in_model(name, type, path):
            self.print_info.emit(
                self.tr("Source alread added {} ({})").format(
                    name, path if path else "repository"
                )
            )
            return

        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow([item, QStandardItem()])

        self.print_info.emit(
            self.tr("Add source {} ({})").format(name, path if path else "repository")
        )

    def setData(self, index, data, role):
        if index.column() > 0:
            return QStandardItemModel.setData(
                self, index, data, int(SourceModel.Roles.DATASET_NAME)
            )
        return QStandardItemModel.setData(self, index, data, role)

    def remove_sources(self, indices):
        for index in sorted(indices):
            path = index.data(int(SourceModel.Roles.PATH))
            self.print_info.emit(
                self.tr("Remove source {} ({})").format(
                    index.data(int(SourceModel.Roles.NAME)),
                    path if path else "repository",
                )
            )
            self.removeRow(index.row())

    def _source_in_model(self, name, type, path):
        match_existing = self.match(
            self.index(0, 0), SourceModel.Roles.NAME, name, -1, Qt.MatchExactly
        )
        if (
            match_existing
            and type == match_existing[0].data(int(SourceModel.Roles.TYPE))
            and path == match_existing[0].data(int(SourceModel.Roles.PATH))
        ):
            return True
        return False

class ImportModelsModel(SourceModel):
    """
    Model providing all the models to import from the repositories, ili-files and xtf-files and considering models already existing in the database
    Inherits SourceModel to use functions and signals like print_info etc.
    """
    def __init__(self):
        super().__init__()
        self._checked_models = {}

    def refresh_model(self, source_model, db_connector=None, silent=False):

        filtered_source_model = QSortFilterProxyModel()
        filtered_source_model.setSourceModel(source_model)
        filtered_source_model.setFilterRole(int(SourceModel.Roles.TYPE))

        self.clear()
        previously_checked_models = self._checked_models
        self._checked_models = {}

        # models from db
        db_modelnames = self._db_modelnames(db_connector)

        # models from the repos
        filtered_source_model.setFilterFixedString("model")
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r, 0)
            modelname = filtered_source_model_index.data(int(SourceModel.Roles.NAME))
            if modelname:
                enabled = modelname not in db_modelnames
                self.add_source(
                    modelname,
                    filtered_source_model_index.data(int(SourceModel.Roles.TYPE)),
                    filtered_source_model_index.data(int(SourceModel.Roles.PATH)),
                    previously_checked_models.get(modelname, Qt.Checked)
                    if enabled
                    else Qt.Unchecked,
                    enabled,
                )
                if not silent:
                    self.print_info.emit(
                        self.tr("- Append (repository) model {}{}").format(
                            modelname,
                            " (inactive because it already exists in the database)"
                            if not enabled
                            else "",
                        )
                    )

        # models from the files
        filtered_source_model.setFilterFixedString("ili")
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r, 0)
            ili_file_path = filtered_source_model_index.data(
                int(SourceModel.Roles.PATH)
            )
            self.ilicache = IliCache(None, ili_file_path)
            models = self.ilicache.process_ili_file(ili_file_path)
            for model in models:
                if model["name"]:
                    enabled = model["name"] not in db_modelnames
                    self.add_source(
                        model["name"],
                        filtered_source_model_index.data(int(SourceModel.Roles.TYPE)),
                        filtered_source_model_index.data(int(SourceModel.Roles.PATH)),
                        previously_checked_models.get(
                            model["name"],
                            Qt.Checked
                            if model is models[-1] and enabled
                            else Qt.Unchecked,
                        ),
                        enabled,
                    )
                    if not silent:
                        self.print_info.emit(
                            self.tr("- Append (file) model {}{} from {}").format(
                                model["name"],
                                " (inactive because it already exists in the database)"
                                if not enabled
                                else "",
                                ili_file_path,
                            )
                        )

        # models from the transfer files
        filtered_source_model.setFilterRegExp("|".join(TransferExtensions))
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r, 0)
            xtf_file_path = filtered_source_model_index.data(int(SourceModel.Roles.PATH))
            models = self._transfer_file_models(xtf_file_path)
            for model in models:
                if model["name"]:
                    enabled = model["name"] not in db_modelnames
                    self.add_source(
                        model["name"],
                        filtered_source_model_index.data(int(SourceModel.Roles.TYPE)),
                        filtered_source_model_index.data(int(SourceModel.Roles.PATH)),
                        previously_checked_models.get(
                            model["name"],
                            Qt.Checked
                            if model is models[-1] and enabled
                            else Qt.Unchecked,
                        ),
                        enabled,
                    )
                    if not silent:
                        self.print_info.emit(
                            self.tr("- Append (xtf file) model {}{} from {}").format(
                                model["name"],
                                " (inactive because it already exists in the database)"
                                if not enabled
                                else "",
                                xtf_file_path,
                            )
                        )

        return self.rowCount()

    def _transfer_file_models(self, xtf_file_path):
        models = []
        try:
            root = ET.parse(xtf_file_path).getroot()
            for model_element in root.iter('{http://www.interlis.ch/INTERLIS2.3}MODEL'):
                model = {}
                model['name']= model_element.get('NAME')
                models.append(model)
        except ET.ParseError as e:
            self.print_info.emit(
                self.tr('Could not parse transferfile file `{file}` ({exception})'.format(
                file=xtf_file_path, exception=str(e))))
        return models

    def _db_modelnames(self, db_connector=None):
        modelnames = list()
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                    for modelname in regex.split(db_model["modelname"]):
                        modelnames.append(modelname.strip())
        return modelnames

    def add_source(self, name, type, path, checked, enabled):
        item = QStandardItem()
        self._checked_models[name] = checked
        item.setFlags(
            Qt.ItemIsSelectable | Qt.ItemIsEnabled if enabled else Qt.NoItemFlags
        )
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow(item)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.tr("{}{}").format(
                SourceModel.data(self, index, (Qt.DisplayRole)),
                ""
                if index.flags() & Qt.ItemIsEnabled
                else " (already in the database)",
            )
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, int(SourceModel.Roles.NAME))]
        return SourceModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self.beginResetModel()
            self._checked_models[self.data(index, int(SourceModel.Roles.NAME))] = data
            self.endResetModel()

    def flags(self, index):
        item = self.item(index.row(), index.column())
        if item:
            return item.flags()
        return Qt.NoItemFlags

    def check(self, index):
        if index.flags() & Qt.ItemIsEnabled:
            if self.data(index, Qt.CheckStateRole) == Qt.Checked:
                self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
            else:
                self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def import_sessions(self):
        sessions = {}
        for r in range(0, self.rowCount()):
            item = self.index(r, 0)
            if item.data(int(Qt.Checked)):
                type = item.data(int(SourceModel.Roles.TYPE))
                model = item.data(int(SourceModel.Roles.NAME))
                source = (
                    item.data(int(SourceModel.Roles.PATH))
                    if type != "model"
                    else "repository " + model
                )

                if self._checked_models[model] == Qt.Checked:
                    models = []
                    if source in sessions:
                        models = sessions[source]["models"]
                    else:
                        sessions[source] = {}
                    models.append(model)
                    sessions[source]["models"] = models
        return sessions

    def checked_models(self):
        return [
            model
            for model in self._checked_models.keys()
            if self._checked_models[model] == Qt.Checked
        ]


class ImportDataModel(QSortFilterProxyModel):
    """
    Model providing the import data files given by a filtered SourceModel and the import_session function to return a sorted list of execution session information
    """

    print_info = pyqtSignal([str], [str, str])

    def __init__(self):
        super().__init__()

    def import_sessions(self, order_list) -> dict():
        sessions = {}
        i = 0
        for r in order_list:
            source = self.index(r, 0).data(int(SourceModel.Roles.PATH))
            dataset = self.index(r, 1).data(int(SourceModel.Roles.DATASET_NAME))
            sessions[source] = {}
            sessions[source]["datasets"] = [dataset]
            i += 1
        return sessions

class CheckEntriesModel(QStringListModel):
    """
    A checkable string list model
    """

    def __init__(self):
        super().__init__()
        self._checked_entries = None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            return self._checked_entries[self.data(index, Qt.DisplayRole)]
        else:
            return QStringListModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self._checked_entries[self.data(index, Qt.DisplayRole)] = data
        else:
            QStringListModel.setData(self, index, role, data)

    def check(self, index):
        if self.data(index, Qt.CheckStateRole) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def check_all(self):
        for name in self.stringList():
            self._checked_entries[name] = Qt.Checked

    def checked_entries(self):
        return [
            name
            for name in self.stringList()
            if self._checked_entries[name] == Qt.Checked
        ]
class ExportModelsModel(CheckEntriesModel):
    """
    Model providing all the models from the database (except the blacklisted ones) and it's checked state
    """

    blacklist = [
        "CHBaseEx_MapCatalogue_V1",
        "CHBaseEx_WaterNet_V1",
        "CHBaseEx_Sewage_V1",
        "CHAdminCodes_V1",
        "AdministrativeUnits_V1",
        "AdministrativeUnitsCH_V1",
        "WithOneState_V1",
        "WithLatestModification_V1",
        "WithModificationObjects_V1",
        "GraphicCHLV03_V1",
        "GraphicCHLV95_V1",
        "NonVector_Base_V2",
        "NonVector_Base_V3",
        "NonVector_Base_LV03_V3_1",
        "NonVector_Base_LV95_V3_1",
        "GeometryCHLV03_V1",
        "GeometryCHLV95_V1",
        "InternationalCodes_V1",
        "Localisation_V1",
        "LocalisationCH_V1",
        "Dictionaries_V1",
        "DictionariesCH_V1",
        "CatalogueObjects_V1",
        "CatalogueObjectTrees_V1",
        "AbstractSymbology",
        "CodeISO",
        "CoordSys",
        "GM03_2_1Comprehensive",
        "GM03_2_1Core",
        "GM03_2Comprehensive",
        "GM03_2Core",
        "GM03Comprehensive",
        "GM03Core",
        "IliRepository09",
        "IliSite09",
        "IlisMeta07",
        "IliVErrors",
        "INTERLIS_ext",
        "RoadsExdm2ben",
        "RoadsExdm2ben_10",
        "RoadsExgm2ien",
        "RoadsExgm2ien_10",
        "StandardSymbology",
        "StandardSymbology",
        "Time",
        "Units",
    ]

    def __init__(self):
        super().__init__()

    def refresh_model(self, db_connector=None):
        modelnames = []

        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                    for modelname in regex.split(db_model["modelname"]):
                        if modelname and modelname not in ExportModelsModel.blacklist:
                            modelnames.append(modelname.strip())

        self.setStringList(modelnames)

        self._checked_entries = {modelname: Qt.Checked for modelname in modelnames}

        return self.rowCount()

class ExportDatasetsModel(CheckEntriesModel):
    """
    Model providing all the datasets from the database and it's checked state
    """
    def __init__(self):
        super().__init__()

    def refresh_model(self, db_connector=None):
        datasetnames = []

        if db_connector and db_connector.db_or_schema_exists():
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                datasetnames.append(record["datasetname"])
        self.setStringList(datasetnames)
        
        self._checked_entries = {datasetname: Qt.Checked for datasetname in datasetnames}

        return self.rowCount()