import mmap
import os
import pathlib
import re
import warnings
import xml.etree.cElementTree as CET
from enum import Enum, IntEnum

from qgis.PyQt.QtCore import (
    QModelIndex,
    QSortFilterProxyModel,
    QStringListModel,
    Qt,
    pyqtSignal,
)
from qgis.PyQt.QtGui import QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QCheckBox, QLineEdit, QListView
from qgis.PyQt.uic import loadUiType

from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import IliCache
from QgisModelBaker.libs.modelbaker.utils.qt_utils import slugify
from QgisModelBaker.utils.globals import CATALOGUE_DATASETNAME


# globals
class DropMode(Enum):
    YES = 1
    NO = 2
    ASK = 3


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

TRANSFERFILE_MODELS_BLACKLIST = [
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

# style
VALID_COLOR = "#adde9b"

VALID_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #adde9b; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """

INVALID_COLOR = "#de9b9b"

INVALID_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #de9b9b; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """

DEFAULT_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #9bcade; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """


class LogColor:
    COLOR_INFO = "#000000"
    COLOR_SUCCESS = "#004905"
    COLOR_FAIL = "#aa2222"
    COLOR_TOPPING = "#341d5c"


class SchemaDataFilterMode(IntEnum):
    NO_FILTER = 1
    MODEL = 2
    DATASET = 3
    BASKET = 4


class PageIds:
    Intro = 1
    ImportSourceSelection = 2
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


class ToppingMakerPageIds:
    Target = 1
    Models = 2
    Layers = 3
    ReferenceData = 4
    Ili2dbSettings = 5
    Generation = 6


# Util functions
def get_ui_class(ui_file):
    """Get UI Python class from .ui file.
       Can be filename.ui or subdirectory/filename.ui
    :param ui_file: The file of the ui in svir.ui
    :type ui_file: str
    """
    os.path.sep.join(ui_file.split("/"))
    ui_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "ui", ui_file)
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return loadUiType(ui_file_path)[0]


# Extended GUI components and used models
class CompletionLineEdit(QLineEdit):
    """
    Extended LineEdit for completion reason punching it on entering or mouse press to open popup.
    """

    punched = pyqtSignal()

    def __init__(self, parent=None):
        super(CompletionLineEdit, self).__init__(parent)
        self.readyToEdit = True

    def focusInEvent(self, e):
        super(CompletionLineEdit, self).focusInEvent(e)
        self.punched.emit()

    def mouseReleaseEvent(self, e):
        super(CompletionLineEdit, self).mouseReleaseEvent(e)
        self.punched.emit()


class SemiTristateCheckbox(QCheckBox):
    """
    Checkbox that does never get the Qt.PartialCheckState on clicked (by user) but can get the Qt.PartialCheckState by direct setCheckState() (by program)
    """

    def __init__(self, parent=None):
        super(SemiTristateCheckbox, self).__init__(parent)

    def nextCheckState(self) -> None:
        if self.checkState() == Qt.Checked:
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(Qt.Checked)


class FileDropListView(QListView):
    """
    List view allowing to drop ili and transfer files.
    """

    ValidExtenstions = ["xtf", "XTF", "itf", "ITF", "ili", "XML", "xml"]

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super(FileDropListView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListView.InternalMove)

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if (
                pathlib.Path(url.toLocalFile()).suffix[1:]
                in FileDropListView.ValidExtenstions
            ):
                event.acceptProposedAction()
                break

    def dropEvent(self, event):
        dropped_files = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if pathlib.Path(url.toLocalFile()).suffix[1:]
            in FileDropListView.ValidExtenstions
        ]
        self.files_dropped.emit(dropped_files)
        event.acceptProposedAction()


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
        IS_CATALOGUE = Qt.UserRole + 6
        ORIGIN_INFO = Qt.UserRole + 7

        def __int__(self):
            return self.value

    class Columns(IntEnum):
        SOURCE = 0
        IS_CATALOGUE = 1
        DATASET = 2

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return "↑ ↓"
        return QStandardItemModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if item:
            if role == Qt.DisplayRole:
                if index.column() == SourceModel.Columns.SOURCE:
                    return "{}{}".format(
                        item.data(int(Qt.DisplayRole)),
                        f" ({item.data(int(SourceModel.Roles.PATH))})"
                        if item.data(int(SourceModel.Roles.TYPE)) != "model"
                        else "",
                    )
                if index.column() == SourceModel.Columns.DATASET:
                    if self.index(index.row(), SourceModel.Columns.IS_CATALOGUE).data(
                        int(SourceModel.Roles.IS_CATALOGUE)
                    ):
                        return "---"
                    else:
                        return item.data(int(SourceModel.Roles.DATASET_NAME))

            if role == Qt.DecorationRole:
                if index.column() == SourceModel.Columns.SOURCE:
                    type = "data"
                    if item.data(int(SourceModel.Roles.TYPE)) and item.data(
                        int(SourceModel.Roles.TYPE)
                    ).lower() in ["model", "ili", "xtf", "xml"]:
                        type = item.data(int(SourceModel.Roles.TYPE)).lower()
                    return QIcon(
                        os.path.join(
                            os.path.dirname(__file__),
                            f"../images/file_types/{type}.png",
                        )
                    )
            return item.data(int(role))

    def add_source(self, name, type, path, origin_info=None):
        if self._source_in_model(name, type, path):
            return False

        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(origin_info, int(SourceModel.Roles.ORIGIN_INFO))
        self.appendRow([item, QStandardItem()])

        self.print_info.emit(
            self.tr("Add source {} ({}) {}").format(
                name, path if path else "repository", origin_info
            )
        )
        return True

    def setData(self, index, data, role):
        if index.column() == SourceModel.Columns.IS_CATALOGUE:
            return QStandardItemModel.setData(
                self, index, data, int(SourceModel.Roles.IS_CATALOGUE)
            )
        if index.column() == SourceModel.Columns.DATASET:
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
            self.index(0, 0), int(SourceModel.Roles.NAME), name, -1, Qt.MatchExactly
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
        self.print_info.emit(self.tr("Refresh available models:"))
        self.clear()
        previously_checked_models = self._checked_models
        self._checked_models = {}

        # models from db
        db_modelnames = self._db_modelnames(db_connector)

        # models from the repos
        filtered_source_model.setFilterFixedString("model")
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(
                r, SourceModel.Columns.SOURCE
            )
            modelname = filtered_source_model_index.data(int(SourceModel.Roles.NAME))
            if modelname:
                enabled = modelname not in db_modelnames
                self.add_source(
                    modelname,
                    filtered_source_model_index.data(int(SourceModel.Roles.TYPE)),
                    filtered_source_model_index.data(int(SourceModel.Roles.PATH)),
                    filtered_source_model_index.data(
                        int(SourceModel.Roles.ORIGIN_INFO)
                    ),
                    previously_checked_models.get(
                        (
                            modelname,
                            filtered_source_model_index.data(
                                int(SourceModel.Roles.PATH)
                            ),
                        ),
                        Qt.Checked,
                    )
                    if enabled
                    and modelname not in self.checked_models()
                    and self._LV95_equivalent_name(modelname)
                    not in self.checked_models()
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
            filtered_source_model_index = filtered_source_model.index(
                r, SourceModel.Columns.SOURCE
            )
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
                        filtered_source_model_index.data(
                            int(SourceModel.Roles.ORIGIN_INFO)
                        ),
                        previously_checked_models.get(
                            (
                                model["name"],
                                filtered_source_model_index.data(
                                    int(SourceModel.Roles.PATH)
                                ),
                            ),
                            Qt.Checked
                            if model is models[-1]
                            and enabled
                            and model["name"] not in self.checked_models()
                            and self._LV95_equivalent_name(model["name"])
                            not in self.checked_models()
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
            filtered_source_model_index = filtered_source_model.index(
                r, SourceModel.Columns.SOURCE
            )
            data_file_path = filtered_source_model_index.data(
                int(SourceModel.Roles.PATH)
            )
            models = self._transfer_file_models(data_file_path)
            for model in models:
                if model["name"]:
                    enabled = model["name"] not in db_modelnames
                    self.add_source(
                        model["name"],
                        filtered_source_model_index.data(int(SourceModel.Roles.TYPE)),
                        filtered_source_model_index.data(int(SourceModel.Roles.PATH)),
                        filtered_source_model_index.data(
                            int(SourceModel.Roles.ORIGIN_INFO)
                        ),
                        previously_checked_models.get(
                            (
                                model["name"],
                                filtered_source_model_index.data(
                                    int(SourceModel.Roles.PATH)
                                ),
                            ),
                            Qt.Checked
                            if enabled
                            and model["name"] not in self.checked_models()
                            and self._LV95_equivalent_name(model["name"])
                            not in self.checked_models()
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
                                data_file_path,
                            )
                        )

        return self.rowCount()

    def _transfer_file_models(self, data_file_path):
        """
        Get model names from an ITF file does a regex parse with mmap (to avoid long parsing time).
        Get model names from an XTF file. Since XTF can be very large, we follow this strategy:
        1. Parse line by line.
            1.a. Compare parsed line with the regular expression to get the Header Section. (escape after 100 lines)
            1.b. If found, stop parsing the XTF file and go to 2. If not found, append the new line to parsed lines and go
                to next line.
        2. Give the Header Section to an XML parser and extract models. Note that we don't give the full XTF file to the XML
        parser because it will read it completely, which may be not optimal.
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

        # parse models from XTF
        start_string = "<HEADERSECTION"
        end_string = "</HEADERSECTION>"
        text_found = ""
        with open(data_file_path, "r") as f:
            lines = ""
            for line_number, line in enumerate(f):
                lines += line
                start_pos = lines.find(start_string)
                end_pos = lines.find(end_string)
                if end_pos > start_pos:
                    text_found = lines[start_pos : end_pos + len(end_string)]
                    break
                if line_number > 100:
                    break

        if text_found:
            try:
                root = CET.fromstring(text_found)
                element = root.find("MODELS")
                if element:
                    for sub_element in element:
                        if (
                            "NAME" in sub_element.attrib
                            and sub_element.attrib["NAME"]
                            not in TRANSFERFILE_MODELS_BLACKLIST
                        ):
                            model = {}
                            model["name"] = sub_element.attrib["NAME"]
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

    def _db_modelnames(self, db_connector=None):
        modelnames = list()
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                for db_model in db_models:
                    for modelname in regex.split(db_model["modelname"]):
                        modelnames.append(modelname.strip())
        return modelnames

    def _LV95_equivalent_name(self, model):
        if "lv03" in model:
            return model.replace("lv03", "lv95")
        if "LV03" in model:
            return model.replace("LV03", "LV95")

    def add_source(self, name, type, path, origin_info, checked, enabled):
        item = QStandardItem()
        self._checked_models[(name, path)] = checked
        item.setFlags(
            Qt.ItemIsSelectable | Qt.ItemIsEnabled if enabled else Qt.NoItemFlags
        )
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(origin_info, int(SourceModel.Roles.ORIGIN_INFO))
        self.appendRow(item)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return "{}{}".format(
                ""
                if index.flags() & Qt.ItemIsEnabled
                else self.tr("Already in the database: "),
                SourceModel.data(self, index, (Qt.DisplayRole)),
            )
        if role == Qt.ToolTipRole:
            return self.data(index, int(SourceModel.Roles.ORIGIN_INFO))
        if role == Qt.CheckStateRole:
            return self._checked_models[
                (
                    self.data(index, int(SourceModel.Roles.NAME)),
                    self.data(index, int(SourceModel.Roles.PATH)),
                )
            ]
        return SourceModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self.beginResetModel()
            self._checked_models[
                (
                    self.data(index, int(SourceModel.Roles.NAME)),
                    self.data(index, int(SourceModel.Roles.PATH)),
                )
            ] = data
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
            item = self.index(r, SourceModel.Columns.SOURCE)
            if item.data(int(Qt.Checked)):
                type = item.data(int(SourceModel.Roles.TYPE))
                model = item.data(int(SourceModel.Roles.NAME))
                source = (
                    item.data(int(SourceModel.Roles.PATH))
                    if type == "ili"
                    else "repository " + model
                )

                if (
                    self._checked_models[
                        (model, item.data(int(SourceModel.Roles.PATH)))
                    ]
                    == Qt.Checked
                ):
                    models = []
                    if source in sessions:
                        models = sessions[source]["models"]
                    else:
                        sessions[source] = {}
                    models.append(model)
                    sessions[source]["models"] = models
        return sessions

    def checked_models(self):
        # return a list of the model names
        return [
            key[0]
            for key in self._checked_models.keys()
            if self._checked_models[key] == Qt.Checked
        ]


class ImportDataModel(QSortFilterProxyModel):
    """
    Model providing the import data files given by a filtered SourceModel and the import_session function to return a sorted list of execution session information
    """

    print_info = pyqtSignal([str], [str, str])

    def __init__(self):
        super().__init__()

    def flags(self, index):
        if index.column() == SourceModel.Columns.IS_CATALOGUE:
            return Qt.ItemIsEnabled
        if index.column() == SourceModel.Columns.DATASET:
            if self.index(index.row(), SourceModel.Columns.IS_CATALOGUE).data(
                int(SourceModel.Roles.IS_CATALOGUE)
            ):
                return Qt.ItemIsEnabled
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def import_sessions(self, order_list) -> dict():
        sessions = {}
        i = 0
        for r in order_list:
            source = self.index(r, SourceModel.Columns.SOURCE).data(
                int(SourceModel.Roles.PATH)
            )
            is_catalogue = self.index(r, SourceModel.Columns.IS_CATALOGUE).data(
                int(SourceModel.Roles.IS_CATALOGUE)
            )
            dataset = (
                self.index(r, SourceModel.Columns.DATASET).data(
                    int(SourceModel.Roles.DATASET_NAME)
                )
                if not is_catalogue
                else CATALOGUE_DATASETNAME
            )
            sessions[source] = {}
            sessions[source]["datasets"] = [dataset]
            i += 1
        return sessions


class SpaceCheckListView(QListView):
    """
    List view allowing to check/uncheck items by space press
    """

    space_pressed = pyqtSignal(QModelIndex)

    def __init__(self, parent=None):
        super(QListView, self).__init__(parent)
        self.space_pressed.connect(self.update)

    # to act when space is pressed
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            _selected_indexes = self.selectedIndexes()
            self.space_pressed.emit(_selected_indexes[0])
        super(SpaceCheckListView, self).keyPressEvent(e)


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
        self._emit_data_changed()

    def check_all(self, state):
        for name in self.stringList():
            self._checked_entries[name] = state
        self._emit_data_changed()

    def _emit_data_changed(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0))

    def checked_entries(self):
        return [
            name
            for name in self.stringList()
            if self._checked_entries[name] == Qt.Checked
        ]


class SchemaModelsModel(CheckEntriesModel):
    """
    Model providing all the models from the database (except the blacklisted ones) and it's checked state used to filter data according to models
    Multiple db_connectors can be passed to scan multiple sources.
    """

    def __init__(self):
        super().__init__()

    def refresh_model(self, db_connectors=[]):
        modelnames = []

        for db_connector in db_connectors:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                for db_model in db_models:
                    for modelname in regex.split(db_model["modelname"]):
                        name = modelname.strip()
                        if (
                            name
                            and name not in TRANSFERFILE_MODELS_BLACKLIST
                            and name not in modelnames
                        ):
                            modelnames.append(name)

        self.setStringList(modelnames)

        self._checked_entries = {modelname: Qt.Checked for modelname in modelnames}

        return self.rowCount()


class SchemaDatasetsModel(CheckEntriesModel):
    """
    Model providing all the datasets from the database and it's checked state used to filter data according to datasets
    """

    def __init__(self):
        super().__init__()

    def refresh_model(self, db_connector=None):
        datasetnames = []

        if db_connector and db_connector.db_or_schema_exists():
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                if record["datasetname"] == CATALOGUE_DATASETNAME:
                    continue
                datasetnames.append(record["datasetname"])
        self.setStringList(datasetnames)

        self._checked_entries = {
            datasetname: Qt.Checked for datasetname in datasetnames
        }

        return self.rowCount()


class SchemaBasketsModel(CheckEntriesModel):
    """
    Model providing all the baskets from the database and it's checked state used to filter data according to baskets
    """

    def __init__(self):
        super().__init__()
        self._basket_ids = None

    def refresh_model(self, db_connector=None):
        basketnames = []
        self._basket_ids = {}

        if db_connector and db_connector.db_or_schema_exists():
            baskets_info = db_connector.get_baskets_info()
            for record in baskets_info:
                basketname = f"{record['datasetname']}-{record['topic']} ({record['basket_t_ili_tid']})"
                basketnames.append(basketname)
                self._basket_ids[basketname] = record["basket_t_ili_tid"]
        self.setStringList(basketnames)

        self._checked_entries = {basketname: Qt.Checked for basketname in basketnames}

        return self.rowCount()

    def checked_entries(self):
        return [
            self._basket_ids[name]
            for name in self.stringList()
            if self._checked_entries[name] == Qt.Checked and name in self._basket_ids
        ]


class DatasetModel(QStandardItemModel):
    """
    ItemModel providing all the datasets from the database.
    """

    class Roles(Enum):
        TID = Qt.UserRole + 1
        DATASETNAME = Qt.UserRole + 2

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def refresh_model(self, db_connector=None):
        self.beginResetModel()
        self.clear()
        if db_connector:
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                if record["datasetname"] == CATALOGUE_DATASETNAME:
                    continue
                item = QStandardItem()
                item.setData(record["datasetname"], int(Qt.DisplayRole))
                item.setData(record["datasetname"], int(DatasetModel.Roles.DATASETNAME))
                item.setData(record["t_id"], int(DatasetModel.Roles.TID))
                self.appendRow(item)
        self.endResetModel()


class BasketSourceModel(QStandardItemModel):
    """
    Model providing the baskets described by topic and datasets.
    The data is keeped per schema/topic during the QGIS session to avoid to many database requests.
    """

    class Roles(Enum):
        DATASETNAME = Qt.UserRole + 1
        MODEL_TOPIC = Qt.UserRole + 2
        BASKET_TID = Qt.UserRole + 3
        # The SCHEMA_TOPIC_IDENTIFICATOR is a combination of db parameters and the topic
        # This because a dataset is usually valid per topic and db schema
        SCHEMA_TOPIC_IDENTIFICATOR = Qt.UserRole + 4

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.schema_baskets = {}

    def refresh(self):
        self.beginResetModel()
        self.clear()
        for schema_identificator in self.schema_baskets.keys():
            for basket in self.schema_baskets[schema_identificator]:
                item = QStandardItem()
                item.setData(basket["datasetname"], int(Qt.DisplayRole))
                item.setData(
                    basket["datasetname"], int(BasketSourceModel.Roles.DATASETNAME)
                )
                item.setData(basket["topic"], int(BasketSourceModel.Roles.MODEL_TOPIC))
                item.setData(
                    basket["basket_t_id"], int(BasketSourceModel.Roles.BASKET_TID)
                )
                item.setData(
                    f"{schema_identificator}_{slugify(basket['topic'])}",
                    int(BasketSourceModel.Roles.SCHEMA_TOPIC_IDENTIFICATOR),
                )
                self.appendRow(item)
        self.endResetModel()

    def reload_schema_baskets(self, db_connector, schema_identificator):
        baskets_info = db_connector.get_baskets_info()
        baskets = []
        for record in baskets_info:
            if record["datasetname"] == CATALOGUE_DATASETNAME:
                continue
            basket = {}
            basket["datasetname"] = record["datasetname"]
            basket["topic"] = record["topic"]
            basket["basket_t_id"] = record["basket_t_id"]
            baskets.append(basket)
        self.schema_baskets[schema_identificator] = baskets
        self.refresh()

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if role == Qt.DisplayRole:
            return f"{item.data(int(role))} ({item.data(int(BasketSourceModel.Roles.MODEL_TOPIC))})"
        return item.data(int(role))

    def clear_schema_baskets(self):
        self.schema_baskets = {}

    def schema_baskets_loaded(self, schema_identificator):
        return schema_identificator in self.schema_baskets

    def model_topics(self, schema_identificator):
        model_topics = {""}
        for basket in self.schema_baskets[schema_identificator]:
            model_topics.add(basket.get("topic", ""))
        return list(model_topics)
