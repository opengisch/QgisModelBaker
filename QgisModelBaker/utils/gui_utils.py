import fnmatch
import mmap
import os
import pathlib
import re
import warnings
import xml.etree.ElementTree as CET
from enum import Enum, IntEnum

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import (
    QT_VERSION_STR,
    QEvent,
    QModelIndex,
    QObject,
    QRect,
    QSortFilterProxyModel,
    QStringListModel,
    Qt,
    pyqtSignal,
)
from qgis.PyQt.QtGui import (
    QColor,
    QIcon,
    QPalette,
    QStandardItem,
    QStandardItemModel,
    QValidator,
)
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QItemDelegate,
    QLabel,
    QLineEdit,
    QListView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
)
from qgis.PyQt.uic import loadUiType

from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import IliCache
from QgisModelBaker.libs.modelbaker.utils.globals import LogLevel
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

MODELS_BLACKLIST = [
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
    "Geometry_V1",
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
    "",
    "CHAdminCodes_V2",
    "AdministrativeUnits_V2",
    "AdministrativeUnitsCH_V2",
    "WithOneState_V2",
    "WithLatestModification_V2",
    "WithModificationObjects_V2",
    "GraphicCHLV03_V2",
    "GraphicCHLV95_V2",
    "GeometryCHLV03_V2",
    "GeometryCHLV95_V2",
    "Geometry_V2",
    "InternationalCodes_V2",
    "Localisation_V2",
    "LocalisationCH_V2",
    "Dictionaries_V2",
    "DictionariesCH_V2",
    "CatalogueObjects_V2",
    "CatalogueObjectTrees_V2",
]

# style
ORANGE = "#D1C28E"  # Not used
GREEN = "#A1DE9B"
BLUE = "#9BCADE"
PURPLE = "#B18BC9"  # Not used
RED = "#870808" if QgsApplication.themeName() == "Night Mapping" else "#EBB3A4"

SUCCESS_COLOR = GREEN

# Note SUCCESS_PROGRESSBAR_BG_COLOR and SUCCESS_COLOR differ for Night
# Mapping theme so that they are distinguishable in the validation list,
# since selected list items will have the SUCCESS_PROGRESSBAR_BG_COLOR.
SUCCESS_PROGRESSBAR_BG_COLOR = (
    "#0f6e00" if QgsApplication.themeName() == "Night Mapping" else GREEN
)
SUCCESS_STYLE = """
    QProgressBar::chunk {{background-color: {}; width: 20px;}}
    QProgressBar {{
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }}
    """.format(
    SUCCESS_PROGRESSBAR_BG_COLOR
)

ERROR_COLOR = RED

ERROR_STYLE = """
    QProgressBar::chunk {{background-color: {}; width: 20px;}}
    QProgressBar {{
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }}
    """.format(
    ERROR_COLOR
)

DEFAULT_PROGRESSBAR_BG_COLOR = (
    "#d7801a" if QgsApplication.themeName() == "Night Mapping" else BLUE
)
DEFAULT_STYLE = """
    QProgressBar::chunk {{background-color: {}; width: 20px;}}
    QProgressBar {{
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }}
    """.format(
    DEFAULT_PROGRESSBAR_BG_COLOR
)

INACTIVE_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #ECECEC; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """


def get_text_color(level: LogLevel = LogLevel.INFO) -> str:
    if level == LogLevel.INFO:
        return (
            QgsApplication.palette()
            .color(QPalette.ColorRole.WindowText)
            .name(QColor.NameFormat.HexRgb)
        )
    elif level == LogLevel.SUCCESS:
        return "#0f6e00"  # From night mapping theme
    elif level == LogLevel.WARNING:
        return "#d7801a"  # From night mapping theme
    elif level == LogLevel.FAIL:
        return "#ff0000"
    elif level == LogLevel.TOPPING:
        return "#5c34a2"  # Adjusted to night mapping theme


def get_text_color_object(level: LogLevel = LogLevel.INFO) -> QColor:
    return QColor(get_text_color(level))


def get_parsed_log_text_level(text) -> LogLevel:
    if text.startswith("Warning:"):
        return LogLevel.WARNING
    elif "error" in text.lower() or "failed" in text.lower():
        return LogLevel.FAIL
    return LogLevel.INFO


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
    DefaultBaskets = 7
    ImportDataConfiguration = 8
    ImportDataExecution = 9
    ExportDatabaseSelection = 10
    ExportDataConfiguration = 11
    ExportDataExecution = 12
    ProjectCreation = 13
    TIDConfiguration = 14


class ToppingWizardPageIds:
    Target = 1
    Models = 2
    Layers = 3
    Additives = 4
    ReferenceData = 5
    Ili2dbSettings = 6
    Generation = 7


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
        super().__init__(parent)
        self.readyToEdit = True

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.punched.emit()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.punched.emit()


class SemiTristateCheckbox(QCheckBox):
    """
    Checkbox that does never get the Qt.PartialCheckState on clicked (by user) but can get the Qt.PartialCheckState by direct setCheckState() (by program)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def nextCheckState(self) -> None:
        if self.checkState() == Qt.CheckState.Checked:
            self.setCheckState(Qt.CheckState.Unchecked)
        else:
            self.setCheckState(Qt.CheckState.Checked)


class FileDropListView(QListView):
    """
    List view allowing to drop ili and transfer files.
    """

    ValidExtenstions = ["xtf", "XTF", "itf", "ITF", "ili"]
    ValidXmlExtensions = ["XML", "xml"]
    ValidIniExtensions = ["ini", "INI", "toml", "TOML"]

    files_dropped = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListView.DragDropMode.InternalMove)

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if (
                pathlib.Path(url.toLocalFile()).suffix[1:]
                in FileDropListView.ValidExtenstions
                + FileDropListView.ValidIniExtensions
                + FileDropListView.ValidXmlExtensions
            ):
                event.acceptProposedAction()
                break

    def dropEvent(self, event):
        dropped_files, dropped_xml_files, dropped_ini_files = self.extractDroppedFiles(
            event.mimeData().urls()
        )

        dropped_files.extend(dropped_xml_files)
        self.files_dropped.emit(dropped_files, dropped_ini_files)
        event.acceptProposedAction()

    @staticmethod
    def extractDroppedFiles(url_list):
        dropped_interlis_files = []
        dropped_xml_files = []
        dropped_ini_files = []
        for url in url_list:
            local_file = url.toLocalFile()
            suffix = pathlib.Path(local_file).suffix[1:]
            if suffix in FileDropListView.ValidExtenstions:
                dropped_interlis_files.append(local_file)
                continue

            if suffix in FileDropListView.ValidXmlExtensions:
                dropped_xml_files.append(local_file)
                continue

            if suffix in FileDropListView.ValidIniExtensions:
                dropped_ini_files.append(local_file)

        return dropped_interlis_files, dropped_xml_files, dropped_ini_files


class SourceModel(QStandardItemModel):
    """
    Model providing the data sources (files or repository items like models) and meta information like path or the chosen dataset
    """

    print_info = pyqtSignal([str], [str, str])

    class Roles(Enum):
        # generally used
        NAME = Qt.ItemDataRole.UserRole + 1
        TYPE = Qt.ItemDataRole.UserRole + 2
        PATH = Qt.ItemDataRole.UserRole + 3
        # data import
        DATASET_NAME = Qt.ItemDataRole.UserRole + 5
        IS_CATALOGUE = Qt.ItemDataRole.UserRole + 6
        ORIGIN_INFO = Qt.ItemDataRole.UserRole + 7
        DELETE_DATA = Qt.ItemDataRole.UserRole + 8
        # generic (used for import models model)
        INFO = Qt.ItemDataRole.UserRole + 9

        def __int__(self):
            return self.value

    class Columns(IntEnum):
        SOURCE = 0
        DELETE_DATA = 1
        IS_CATALOGUE = 2
        DATASET = 3

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if (
            orientation == Qt.Orientation.Vertical
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return "↑ ↓"
        return QStandardItemModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if item:
            if role == Qt.ItemDataRole.DisplayRole:
                if index.column() == SourceModel.Columns.SOURCE:
                    return "{}{}".format(
                        item.data(int(Qt.ItemDataRole.DisplayRole)),
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

            if role == Qt.ItemDataRole.DecorationRole:
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
            if role == Qt.ItemDataRole.ToolTipRole:
                if index.column() == SourceModel.Columns.IS_CATALOGUE:
                    return self.tr(
                        "If the data is a catalog, it is imported into the corresponding dataset (called catalogueset)."
                    )
                if index.column() == SourceModel.Columns.DELETE_DATA:
                    return self.tr(
                        "If activated, the existing data is deleted before the import."
                    )

            return item.data(int(role))

    def add_source(self, name, type, path, origin_info=None):
        if self._source_in_model(name, type, path):
            return False

        item = QStandardItem()
        item.setData(name, int(Qt.ItemDataRole.DisplayRole))
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
        if index.column() == SourceModel.Columns.DELETE_DATA:
            return QStandardItemModel.setData(
                self, index, data, int(SourceModel.Roles.DELETE_DATA)
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
            self.index(0, 0),
            int(SourceModel.Roles.NAME),
            name,
            -1,
            Qt.MatchFlag.MatchExactly,
        )
        if (
            match_existing
            and type == match_existing[0].data(int(SourceModel.Roles.TYPE))
            and path == match_existing[0].data(int(SourceModel.Roles.PATH))
        ):
            return True
        return False


class ImportModelsHtmlDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def drawDisplay(self, painter, option, rect, text):
        label = QLabel()
        label.setText(text)
        label.setEnabled(option.state & QStyle.State_Enabled)
        label.setAttribute(Qt.WA_TranslucentBackground)
        label.setMargin(3)
        label.setWordWrap(True)

        painter.save()
        painter.translate(rect.topLeft())
        label.resize(rect.size())
        label.render(painter)
        painter.restore()

    def sizeHint(self, option, index):
        label = QLabel()
        display = index.model().data(index, Qt.DisplayRole)
        label.setText(display)
        label.setWordWrap(True)
        label.setFixedWidth(option.widget.size().width())
        label.setMargin(3)
        return label.sizeHint()


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
                    previously_checked_models.get(modelname, Qt.CheckState.Checked)
                    if enabled
                    and self._LV95_equivalent_name(modelname)
                    not in self.checked_models()
                    else Qt.CheckState.Unchecked,
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
                            model["name"],
                            Qt.CheckState.Checked
                            if model is models[-1]
                            and enabled
                            and self._LV95_equivalent_name(model["name"])
                            not in self.checked_models()
                            else Qt.CheckState.Unchecked,
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
        if QT_VERSION_STR < "5.12.0":
            filtered_source_model.setFilterRegExp("|".join(TransferExtensions))
        else:
            filtered_source_model.setFilterRegularExpression(
                "|".join(TransferExtensions)
            )
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
                            model["name"],
                            Qt.CheckState.Checked
                            if enabled
                            and self._LV95_equivalent_name(model["name"])
                            not in self.checked_models()
                            else Qt.CheckState.Unchecked,
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
        item, new = self._get_item_by_name(name)
        self._checked_models[name] = checked
        item.setFlags(
            Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            if enabled
            else Qt.ItemFlag.NoItemFlags
        )

        info_item = {"type": type, "path": path, "origin_info": origin_info}
        if new:
            item.setData(name, int(SourceModel.Roles.NAME))
            item.setData([info_item], int(SourceModel.Roles.INFO))
            self.appendRow(item)
        else:
            info_list = item.data(int(SourceModel.Roles.INFO))
            info_list.append(info_item)
            item.setData(info_list, int(SourceModel.Roles.INFO))
        return True

    def _get_item_by_name(self, name):
        for row in range(self.rowCount()):
            index = self.index(row, 0)
            if name == index.data(int(SourceModel.Roles.NAME)):
                return self.itemFromIndex(index), False
        return QStandardItem(), True

    def _title_text(self, info):
        types = [info_item["type"] for info_item in info]

        text_list = []
        if "ili" in types:
            text_list.append(self.tr("in local ili-file"))
        if "xtf" in types or "xml" in types:
            text_list.append(self.tr("in local datafile"))
        if "model" in types:
            text_list.append(self.tr("in the repositories"))
        if len(text_list) == 1:
            return self.tr("Found the model {}.").format(text_list[0])
        if len(text_list) == 2:
            return self.tr("Found the model {} and {}.").format(
                text_list[0], text_list[1]
            )
        if len(text_list) == 3:
            return self.tr("Found the model {}, {} and {}.").format(
                text_list[0], text_list[1], text_list[2]
            )

    def _description_text(self, info):
        source_origin_tuples = [
            (info_item["path"], info_item["origin_info"]) for info_item in info
        ]

        if len(source_origin_tuples) == 1:
            source, origin = source_origin_tuples[0]
            description_text = " from <i>{}</i> ({})".format(
                source or "the repositories", origin
            )
        else:
            description_text = self.tr(" from:<ul>")
            for source, origin in source_origin_tuples:
                description_text += "<li><i>{}</i> ({})</li>".format(
                    source or "the repositories", origin
                )
            description_text += "</ul>"
        return description_text

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return "<p><b>{}{}</b><br/><span style='color:gray;'>{}</span></p>".format(
                ""
                if index.flags() & Qt.ItemFlag.ItemIsEnabled
                else self.tr("Already in the database: "),
                self.data(index, int(SourceModel.Roles.NAME)),
                self._title_text(self.data(index, int(SourceModel.Roles.INFO))),
            )
        if role == Qt.ItemDataRole.ToolTipRole:
            return "<p><b>{}</b>{}</p>".format(
                self.data(index, int(SourceModel.Roles.NAME)),
                self._description_text(self.data(index, int(SourceModel.Roles.INFO))),
            )
        if role == Qt.ItemDataRole.CheckStateRole:
            return self._checked_models[self.data(index, int(SourceModel.Roles.NAME))]
        if role == Qt.ItemDataRole.DecorationRole:
            return QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "../images/file_types/model.png",
                )
            )
        return SourceModel.data(self, index, role)

    # this is unusual that it's not first data and then role (could be changed)
    def setData(self, index, role, data):
        if role == Qt.ItemDataRole.CheckStateRole:
            self.beginResetModel()
            self._checked_models[self.data(index, int(SourceModel.Roles.NAME))] = data
            self.endResetModel()

    def flags(self, index):
        item = self.item(index.row(), index.column())
        if item:
            return item.flags()
        return Qt.ItemFlag.NoItemFlags

    def check(self, index):
        if index.flags() & Qt.ItemFlag.ItemIsEnabled:
            if (
                self.data(index, Qt.ItemDataRole.CheckStateRole)
                == Qt.CheckState.Checked
            ):
                self.setData(
                    index, Qt.ItemDataRole.CheckStateRole, Qt.CheckState.Unchecked
                )
            else:
                self.setData(
                    index, Qt.ItemDataRole.CheckStateRole, Qt.CheckState.Checked
                )

    def import_sessions(self):
        sessions = {}
        for r in range(0, self.rowCount()):
            item = self.index(r, 0)
            model = item.data(int(SourceModel.Roles.NAME))
            if self._checked_models[model] == Qt.CheckState.Checked:
                info = item.data(int(SourceModel.Roles.INFO))
                type_path_tuples = [
                    (info_item["type"], info_item["path"]) for info_item in info
                ]

                # when one type is ili, we take this path (because user selected file on purpose) otherwise repository
                source = "repository"
                for type, path in type_path_tuples:
                    if type == "ili":
                        source = path
                        break
                models = []
                if source in sessions:
                    models = sessions[source]["models"]
                else:
                    sessions[source] = {}
                if model not in models:
                    models.append(model)
                sessions[source]["models"] = models
        return sessions

    def checked_models(self):
        # return a list of the model names
        return [
            key
            for key in self._checked_models.keys()
            if self._checked_models[key] == Qt.CheckState.Checked
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
            return Qt.ItemFlag.ItemIsEnabled
        if index.column() == SourceModel.Columns.DELETE_DATA:
            return Qt.ItemFlag.ItemIsEnabled
        if index.column() == SourceModel.Columns.DATASET:
            if self.index(index.row(), SourceModel.Columns.IS_CATALOGUE).data(
                int(SourceModel.Roles.IS_CATALOGUE)
            ):
                return Qt.ItemFlag.ItemIsEnabled
            return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def import_sessions(self, order_list) -> dict():
        sessions = {}
        i = 0
        for r in order_list:
            source = self.index(r, SourceModel.Columns.SOURCE).data(
                int(SourceModel.Roles.PATH)
            )
            delete_data = self.index(r, SourceModel.Columns.DELETE_DATA).data(
                int(SourceModel.Roles.DELETE_DATA)
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
            sessions[source]["datasets"] = [dataset] if dataset else []
            sessions[source]["delete_data"] = delete_data
            i += 1
        return sessions

    def sources(self):
        sources = []
        for r in range(self.rowCount()):
            sources.append(
                self.index(r, SourceModel.Columns.SOURCE).data(
                    int(SourceModel.Roles.PATH)
                )
            )
        return sources


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
        if e.key() == Qt.Key.Key_Space:
            _selected_indexes = self.selectedIndexes()
            self.space_pressed.emit(_selected_indexes[0])
        super().keyPressEvent(e)


class CheckEntriesModel(QStringListModel):
    """
    A checkable string list model
    """

    def __init__(self):
        super().__init__()
        self._checked_entries = {}

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.ItemDataRole.CheckStateRole:
            if self.data(index, Qt.ItemDataRole.DisplayRole) in self._checked_entries:
                return self._checked_entries[
                    self.data(index, Qt.ItemDataRole.DisplayRole)
                ]
            else:
                return Qt.CheckState.Unchecked
        else:
            return QStringListModel.data(self, index, role)

    # this is unusual that it's not first data and then role (could be changed)
    def setData(self, index, role, data):
        if role == Qt.ItemDataRole.CheckStateRole:
            self._checked_entries[self.data(index, Qt.ItemDataRole.DisplayRole)] = data
        else:
            QStringListModel.setData(self, index, data, role)

    def check(self, index):
        if self.data(index, Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked:
            self.setData(index, Qt.ItemDataRole.CheckStateRole, Qt.CheckState.Unchecked)
        else:
            self.setData(index, Qt.ItemDataRole.CheckStateRole, Qt.CheckState.Checked)
        self._emit_data_changed()

    def check_all(self, state):
        for name in self.stringList():
            self._checked_entries[name] = state
        self._emit_data_changed()

    def _emit_data_changed(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0))

    def checked_entries(self):
        """
        Provides the selected entries as list
        """
        return [
            name
            for name in self.stringList()
            if self._checked_entries.get(name, Qt.CheckState.Unchecked)
            == Qt.CheckState.Checked
        ]

    def check_entries(self, entries: list = []):
        """
        Checks the passed entries and unchecks all others.
        """
        for name in self.stringList():
            if name in entries:
                self._checked_entries[name] == Qt.CheckState.Checked
            else:
                self._checked_entries[name] == Qt.CheckState.Unchecked

    def refresh_stringlist(self, values):
        """
        This sets the values to the string list, keeps thes status (checked_entries) when they still exist, and sets the new ones to Checked
        """

        self.setStringList(values)

        # if there where already entries with a status we take it and otherwise we set checked per default
        new_checked_entries = {}
        for value in values:
            if value in self._checked_entries:
                new_checked_entries[value] = self._checked_entries[value]
            else:
                new_checked_entries[value] = Qt.CheckState.Checked
        self._checked_entries = new_checked_entries

        self._emit_data_changed()
        return self.rowCount()


class SchemaModelsModel(CheckEntriesModel):
    """
    Model providing all the models from the database (except the blacklisted ones) and it's checked state used to filter data according to models
    Multiple db_connectors can be passed to scan multiple sources.
    """

    class Roles(Enum):
        PARENT_MODELS = Qt.ItemDataRole.UserRole + 1

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self._parent_models = {}

    def data(self, index, role):
        if role == Qt.ItemDataRole.ToolTipRole:
            model_name = self.data(index, Qt.ItemDataRole.DisplayRole)
            if self._parent_models[model_name]:
                return self.tr(
                    """
                    <html><head/><body>
                    <p><b>{}</b> is an extension of <b>{}</b></p>
                    </body></html>
                    """
                ).format(model_name, ", ".join(self._parent_models[model_name]))
        if role == int(SchemaModelsModel.Roles.PARENT_MODELS):
            return self._parent_models[self.data(index, Qt.ItemDataRole.DisplayRole)]
        else:
            return CheckEntriesModel.data(self, index, role)

    # this is unusual that it's not first data and then role (could be changed)
    def setData(self, index, role, data):
        if role == int(SchemaModelsModel.Roles.PARENT_MODELS):
            self._parent_models[self.data(index, Qt.ItemDataRole.DisplayRole)] = data
        else:
            CheckEntriesModel.setData(self, index, role, data)

    def refresh_model(self, db_connectors=[]):
        modelnames = []

        for db_connector in db_connectors:
            if (
                db_connector
                and db_connector.db_or_schema_exists()
                and db_connector.metadata_exists()
            ):
                db_models = db_connector.get_models()
                regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                for db_model in db_models:
                    for modelname in regex.split(db_model["modelname"]):
                        name = modelname.strip()
                        if (
                            name
                            and name not in MODELS_BLACKLIST
                            and name not in modelnames
                        ):
                            modelnames.append(name)
                            self._parent_models[name] = db_model["parents"]

        return self.refresh_stringlist(modelnames)


class SchemaDatasetsModel(CheckEntriesModel):
    """
    Model providing all the datasets from the database and it's checked state used to filter data according to datasets
    """

    def __init__(self):
        super().__init__()

    def refresh_model(self, db_connector=None):
        datasetnames = []

        if (
            db_connector
            and db_connector.db_or_schema_exists()
            and db_connector.metadata_exists()
        ):
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                if record["datasetname"] == CATALOGUE_DATASETNAME:
                    continue
                datasetnames.append(record["datasetname"])
        self.setStringList(datasetnames)

        self._checked_entries = {
            datasetname: Qt.CheckState.Checked for datasetname in datasetnames
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

        if (
            db_connector
            and db_connector.db_or_schema_exists()
            and db_connector.metadata_exists()
        ):
            baskets_info = db_connector.get_baskets_info()
            for record in baskets_info:
                basketname = f"{record['datasetname']}-{record['topic']} ({record['basket_t_ili_tid']}) {record['attachmentkey']}"
                basketnames.append(basketname)
                self._basket_ids[basketname] = record["basket_t_ili_tid"]
        self.setStringList(basketnames)

        self._checked_entries = {
            basketname: Qt.CheckState.Checked for basketname in basketnames
        }

        return self.rowCount()

    def checked_entries(self):
        return [
            self._basket_ids[name]
            for name in self.stringList()
            if self._checked_entries[name] == Qt.CheckState.Checked
            and name in self._basket_ids
        ]


class DatasetModel(QStandardItemModel):
    """
    ItemModel providing all the datasets from the database.
    """

    class Roles(Enum):
        TID = Qt.ItemDataRole.UserRole + 1
        DATASETNAME = Qt.ItemDataRole.UserRole + 2

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def refresh_model(self, db_connector=None):
        self.beginResetModel()
        self.clear()
        if db_connector:
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                if record["datasetname"] == CATALOGUE_DATASETNAME:
                    continue
                item = QStandardItem()
                item.setData(record["datasetname"], int(Qt.ItemDataRole.DisplayRole))
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
        DATASETNAME = Qt.ItemDataRole.UserRole + 1
        MODEL_TOPIC = Qt.ItemDataRole.UserRole + 2
        BASKET_TID = Qt.ItemDataRole.UserRole + 3
        # The SCHEMA_TOPIC_IDENTIFICATOR is a combination of db parameters and the topic
        # This because a dataset is usually valid per topic and db schema
        SCHEMA_TOPIC_IDENTIFICATOR = Qt.ItemDataRole.UserRole + 4

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
                item.setData(basket["datasetname"], int(Qt.ItemDataRole.DisplayRole))
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
        if role == Qt.ItemDataRole.DisplayRole:
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


class CheckDelegate(QStyledItemDelegate):
    def __init__(self, parent, role, disable_role=None):
        super().__init__(parent)
        self.role = role
        # according to this role it can be disabled or enabled
        self.disable_role = disable_role

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonPress:
            value = index.data(int(self.role)) or False
            model.setData(index, not value, int(self.role))
            return True
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        # don't show option when disabled
        if index.data(int(self.disable_role)) if self.disable_role else False:
            return

        opt = QStyleOptionButton()
        opt.rect = option.rect
        center_x = opt.rect.x() + opt.rect.width() / 2
        center_y = opt.rect.y() + opt.rect.height() / 2
        checkbox_width = QApplication.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth
        )
        checkbox_height = QApplication.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorHeight
        )
        checkbox_rect = QRect(
            int(center_x - checkbox_width / 2),
            int(center_y - checkbox_height / 2),
            checkbox_width,
            checkbox_height,
        )
        opt.rect = checkbox_rect

        value = index.data(int(self.role)) or False
        opt.state |= QStyle.StateFlag.State_On if value else QStyle.StateFlag.State_Off
        QApplication.style().drawControl(
            QStyle.ControlElement.CE_CheckBox, opt, painter
        )


class Validators(QObject):
    def validate_line_edits(self, *args, **kwargs):
        """
        Validate line edits and set their color to indicate validation state.
        """
        senderObj = self.sender()
        validator = senderObj.validator()
        if validator is None:
            color = (
                QgsApplication.palette()
                .color(QPalette.ColorRole.Base)
                .name(QColor.NameFormat.HexRgb)
            )
        else:
            state = validator.validate(senderObj.text().strip(), 0)[0]
            if state == QValidator.State.Acceptable:
                color = (
                    QgsApplication.palette()
                    .color(QPalette.ColorRole.Base)
                    .name(QColor.NameFormat.HexRgb)
                )
            elif state == QValidator.State.Intermediate:
                color = "#ffd356"  # Light orange
            else:
                color = "#f6989d"  # Red
        senderObj.setStyleSheet("QLineEdit {{ background-color: {} }}".format(color))


class FileValidator(QValidator):
    def __init__(
        self,
        pattern="*",
        is_executable=False,
        parent=None,
        allow_empty=False,
        allow_non_existing=False,
    ):
        """
        Validates if a string is a valid filename, based on the provided parameters.

        :param pattern: A file glob pattern as recognized by ``fnmatch``, if a list if provided, the validator will try
                        to match every pattern in the list.
        :param is_executable: Only match executable files
        :param parent: The parent QObject
        :param allow_empty: Empty strings are valid
        :param allow_non_existing: Non existing files are valid
        """
        QValidator.__init__(self, parent)
        self.pattern = pattern
        self.is_executable = is_executable
        self.allow_empty = allow_empty
        self.allow_non_existing = allow_non_existing
        self.error = ""

    """
    Validator for file line edits
    """

    def validate(self, text, pos):
        self.error = ""

        if self.allow_empty and not text.strip():
            return QValidator.State.Acceptable, text, pos

        pattern_matches = False
        if type(self.pattern) is str:
            pattern_matches = fnmatch.fnmatch(text, self.pattern)
        elif type(self.pattern) is list:
            pattern_matches = True in (
                fnmatch.fnmatch(text, pattern) for pattern in self.pattern
            )
        else:
            raise TypeError(
                "pattern must be str or list, not {}".format(type(self.pattern))
            )

        if not text:
            self.error = self.tr("Text field value is empty.")
        elif not self.allow_non_existing and not os.path.isfile(text):
            self.error = self.tr("The chosen file does not exist.")
        elif not pattern_matches:
            self.error = self.tr(
                "The chosen file has a wrong extension (has to be {}).".format(
                    self.pattern
                    if type(self.pattern) is str
                    else ",".join(self.pattern)
                )
            )
        elif self.is_executable and not os.access(text, os.X_OK):
            self.error = self.tr("The chosen file is not executable.")
        if self.error:
            return QValidator.State.Intermediate, text, pos
        else:
            return QValidator.State.Acceptable, text, pos


class NonEmptyStringValidator(QValidator):
    def __init__(self, parent=None):
        QValidator.__init__(self, parent)

    def validate(self, text, pos):
        if not text.strip():
            return QValidator.State.Intermediate, text, pos

        return QValidator.State.Acceptable, text, pos
