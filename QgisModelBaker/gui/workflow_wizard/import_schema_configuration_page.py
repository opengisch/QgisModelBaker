"""
/***************************************************************************
                              -------------------
        begin                : 06.07.2021
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

import configparser
import os
import pathlib
import re

from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QCompleter, QWizardPage

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import (
    IliDataCache,
    IliDataFileCompleterDelegate,
    IliDataItemModel,
)
from QgisModelBaker.libs.modelbaker.utils.globals import LogLevel
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.globals import CRS_PATTERNS
from QgisModelBaker.utils.gui_utils import get_text_color

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/import_schema_configuration.ui")


class ImportSchemaConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.workflow_wizard = parent
        self.is_complete = True

        self.model_list_view.setModel(self.workflow_wizard.import_models_model)
        self.model_list_view.clicked.connect(
            self.workflow_wizard.import_models_model.check
        )
        self.model_list_view.space_pressed.connect(
            self.workflow_wizard.import_models_model.check
        )
        self.model_list_view.model().modelReset.connect(
            self._update_models_dependent_info
        )

        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog(self)
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self._fill_toml_file_info_label)

        self.crsSelector.crsChanged.connect(self._crs_changed)

        self.ilimetaconfigcache = IliDataCache(
            self.workflow_wizard.import_schema_configuration.base_configuration
        )
        self.metaconfig_delegate = IliDataFileCompleterDelegate()
        self.metaconfig = configparser.ConfigParser()
        self.current_models = []
        self.current_metaconfig_id = None
        self.ili_metaconfig_line_edit.setPlaceholderText(
            self.tr("[Search metaconfiguration from repositories]")
        )
        self.ili_metaconfig_line_edit.setEnabled(False)
        self.ili_metaconfig_line_edit.textChanged.emit(
            self.ili_metaconfig_line_edit.text()
        )
        self.ili_metaconfig_line_edit.textChanged.connect(
            self._complete_metaconfig_completer
        )
        self.ili_metaconfig_line_edit.punched.connect(
            self._complete_metaconfig_completer
        )
        self.ili_metaconfig_line_edit.textChanged.connect(
            self._on_metaconfig_completer_activated
        )
        self.workflow_wizard.ilireferencedatacache.model_refreshed.connect(
            self._update_linked_models
        )

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.completeChanged.emit()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def restore_configuration(self):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        settings = QSettings()
        srs_auth = settings.value("QgisModelBaker/ili2db/srs_auth", "EPSG")
        srs_code = settings.value("QgisModelBaker/ili2db/srs_code", 2056, int)
        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self._update_crs_info()
        self._crs_changed()
        self._fill_toml_file_info_label()
        self._update_models_dependent_info()

    def update_configuration(self, configuration):
        # metaconfig settings
        configuration.metaconfig = self.metaconfig
        if self.current_metaconfig_id:
            configuration.metaconfig_id = f"ilidata:{self.current_metaconfig_id}"
        if "CONFIGURATION" in self.metaconfig.sections():
            configuration.metaconfig_params_only = self.metaconfig[
                "CONFIGURATION"
            ].getboolean("qgis.modelbaker.metaConfigParamsOnly")
        # takes settings from the GUI and provides it to the configuration
        configuration.srs_auth = self.srs_auth
        configuration.srs_code = self.srs_code
        # ili2db_options
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.create_gpkg_multigeom = (
            self.ili2db_options.create_gpkg_multigeom()
        )
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()
        configuration.tomlfile = self.ili2db_options.toml_file()

    def save_configuration(self, updated_configuration):
        # puts it to QSettings
        settings = QSettings()
        settings.setValue(
            "QgisModelBaker/ili2db/srs_auth", updated_configuration.srs_auth
        )
        settings.setValue(
            "QgisModelBaker/ili2db/srs_code", updated_configuration.srs_code
        )

    def _update_models_dependent_info(self):
        """
        When something in the models model change:
        - Checks all checked models for CRS_PATTERNS (takes first match)
        - Calls update of ilimetaconfig cache to provide metaconfigurations
        - Calls update of ilireferencedata cache to load referenced
        """
        model_list = self.model_list_view.model().checked_models()
        self.current_models = model_list
        for pattern, crs in CRS_PATTERNS.items():
            if re.search(pattern, ", ".join(model_list)):
                self.crs = QgsCoordinateReferenceSystem.fromEpsgId(int(crs))
                self._update_crs_info()
                break
        self._update_ilimetaconfigcache()
        self._update_ilireferencedatacache()

    def _update_ilimetaconfigcache(self):
        self.ilimetaconfigcache = IliDataCache(
            self.workflow_wizard.import_schema_configuration.base_configuration,
            models=";".join(self.model_list_view.model().checked_models()),
            datasources=["pg"]
            if (self.workflow_wizard.import_schema_configuration.tool & DbIliMode.pg)
            else ["gpkg"]
            if (self.workflow_wizard.import_schema_configuration.tool & DbIliMode.gpkg)
            else None,
        )
        self.ilimetaconfigcache.file_download_succeeded.connect(
            lambda dataset_id, path: self._on_metaconfig_received(path)
        )
        self.ilimetaconfigcache.file_download_failed.connect(self._on_metaconfig_failed)
        self.ilimetaconfigcache.model_refreshed.connect(
            self._update_metaconfig_completer
        )
        self.workflow_wizard.busy(self, True, self.tr("Refresh repository data..."))
        self._refresh_ili_metaconfig_cache()

    def _update_ilireferencedatacache(self):
        self.workflow_wizard.refresh_referencedata_cache(
            self.model_list_view.model().checked_models(), "referenceData"
        )

    def _fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr("Extra Meta Attribute File: {}").format(
                (
                    "…"
                    + self.ili2db_options.toml_file()[
                        len(self.ili2db_options.toml_file()) - 40 :
                    ]
                )
                if len(self.ili2db_options.toml_file()) > 40
                else self.ili2db_options.toml_file()
            )
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def _update_crs_info(self):
        self.crsSelector.setCrs(self.crs)

    def _crs_changed(self):
        self.srs_auth = "EPSG"  # Default
        self.srs_code = 2056  # Default
        srs_auth, srs_code = self.crsSelector.crs().authid().split(":")
        if srs_auth == "USER":
            self.crs_label.setStyleSheet("color: orange")
            self.crs_label.setToolTip(
                self.tr(
                    "Please select a valid Coordinate Reference System.\nCRSs from USER are valid for a single computer and therefore, a default EPSG:2056 will be used instead."
                )
            )
        else:
            self.crs_label.setStyleSheet("")
            self.crs_label.setToolTip(self.tr("Coordinate Reference System"))
            try:
                self.srs_code = int(srs_code)
                self.srs_auth = srs_auth
            except ValueError:
                # Preserve defaults if srs_code is not an integer
                self.crs_label.setStyleSheet("color: orange")
                self.crs_label.setToolTip(
                    self.tr(
                        "The srs code ('{}') should be an integer.\nA default EPSG:2056 will be used.".format(
                            srs_code
                        )
                    )
                )

    def _disable_settings(self, disable):
        self.crsSelector.setDisabled(disable)
        self.crs_label.setDisabled(disable)
        self.ili2db_options_button.setDisabled(disable)

    def _refresh_ili_metaconfig_cache(self):
        self.ilimetaconfigcache.new_message.connect(
            self.workflow_wizard.log_panel.show_message
        )
        self.ilimetaconfigcache.refresh()

    def _complete_metaconfig_completer(self):
        if not self.ili_metaconfig_line_edit.text():
            self._clean_metaconfig()
            self.ili_metaconfig_line_edit.completer().setCompletionMode(
                QCompleter.UnfilteredPopupCompletion
            )
            self.ili_metaconfig_line_edit.completer().complete()
        else:
            match_contains = (
                self.ili_metaconfig_line_edit.completer()
                .completionModel()
                .match(
                    self.ili_metaconfig_line_edit.completer()
                    .completionModel()
                    .index(0, 0),
                    Qt.DisplayRole,
                    self.ili_metaconfig_line_edit.text(),
                    -1,
                    Qt.MatchContains,
                )
            )
            if len(match_contains) > 1:
                self.ili_metaconfig_line_edit.completer().setCompletionMode(
                    QCompleter.PopupCompletion
                )
                self.ili_metaconfig_line_edit.completer().complete()

            self.ili_metaconfig_line_edit.completer().popup().scrollToTop()

    def _update_metaconfig_completer(self, rows):
        completer = QCompleter(
            self.ilimetaconfigcache.sorted_model, self.ili_metaconfig_line_edit
        )
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setModelSorting(QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setItemDelegate(self.metaconfig_delegate)
        self.ili_metaconfig_line_edit.setCompleter(completer)
        self.ili_metaconfig_line_edit.setEnabled(bool(rows))
        self.workflow_wizard.busy(self, False)

    def _on_metaconfig_completer_activated(self, text=None):
        self._clean_metaconfig()
        matches = self.ilimetaconfigcache.model.match(
            self.ilimetaconfigcache.model.index(0, 0),
            Qt.DisplayRole,
            self.ili_metaconfig_line_edit.text(),
            1,
            Qt.MatchExactly,
        )
        if matches:
            model_index = matches[0]
            metaconfig_id = self.ilimetaconfigcache.model.data(
                model_index, int(IliDataItemModel.Roles.ID)
            )

            if self.current_metaconfig_id == metaconfig_id:
                return
            self.current_metaconfig_id = metaconfig_id
            self.metaconfig_file_info_label.setText(
                self.tr(
                    "<html><head/><body><p><b>Current Metaconfig File: {} ({})</b><br><i>{}</i></p></body></html>"
                ).format(
                    self.ilimetaconfigcache.model.data(model_index, Qt.DisplayRole),
                    metaconfig_id,
                    self.ilimetaconfigcache.model.data(
                        model_index, int(IliDataItemModel.Roles.SHORT_DESCRIPTION)
                    )
                    or "",
                )
            )
            self.metaconfig_file_info_label.setStyleSheet(
                "color: {}".format(get_text_color(LogLevel.TOPPING))
            )
            repository = self.ilimetaconfigcache.model.data(
                model_index, int(IliDataItemModel.Roles.ILIREPO)
            )
            url = self.ilimetaconfigcache.model.data(
                model_index, int(IliDataItemModel.Roles.URL)
            )
            path = self.ilimetaconfigcache.model.data(
                model_index, int(IliDataItemModel.Roles.RELATIVEFILEPATH)
            )
            dataset_id = self.ilimetaconfigcache.model.data(
                model_index, int(IliDataItemModel.Roles.ID)
            )
            # disable the next buttton
            self.setComplete(False)
            if path:
                self.ilimetaconfigcache.download_file(repository, url, path, dataset_id)
            else:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("File not specified for metaconfig with id {}.").format(
                        dataset_id
                    ),
                    LogLevel.TOPPING,
                )

            self._set_metaconfig_line_edit_state(True)
        else:
            self._set_metaconfig_line_edit_state(
                not self.ili_metaconfig_line_edit.text()
            )
            self._clean_metaconfig()

    def _clean_metaconfig(self):
        self.current_metaconfig_id = None
        self.metaconfig.clear()
        self.metaconfig_file_info_label.setText("")
        self._disable_settings(False)
        self.ili2db_options.load_metaconfig(None)

    def _set_metaconfig_line_edit_state(self, valid):
        self.ili_metaconfig_line_edit.setStyleSheet(
            "QLineEdit {{ background-color: {} }}".format(
                "#ffffff" if valid else "#ffd356"
            )
        )

    def _on_metaconfig_received(self, path):
        self.workflow_wizard.log_panel.print_info(
            self.tr("Metaconfig file successfully downloaded: {}").format(path),
            LogLevel.TOPPING,
        )
        # parse metaconfig
        self.metaconfig.clear()
        with open(path) as metaconfig_file:
            self.metaconfig.read_file(metaconfig_file)
            self._load_metaconfig()
            # enable the next buttton
            self._fill_toml_file_info_label()
            self.workflow_wizard.log_panel.print_info(
                self.tr("Metaconfig successfully loaded."), LogLevel.TOPPING
            )
            self.setComplete(True)

    def _on_metaconfig_failed(self, dataset_id, error_msg):
        self.workflow_wizard.log_panel.print_info(
            self.tr("Download of metaconfig file failed: {}.").format(error_msg),
            LogLevel.TOPPING,
        )
        # enable the next buttton
        self.setComplete(True)

    def _update_linked_models(self):
        linked_models = []

        for r in range(self.workflow_wizard.ilireferencedatacache.model.rowCount()):
            if self.workflow_wizard.ilireferencedatacache.model.item(r).data(
                int(IliDataItemModel.Roles.MODEL_LINKS)
            ):
                linked_models.extend(
                    [
                        model_link.split(".")[0]
                        for model_link in self.workflow_wizard.ilireferencedatacache.model.item(
                            r
                        ).data(
                            int(IliDataItemModel.Roles.MODEL_LINKS)
                        )
                    ]
                )

        for linked_model in linked_models:
            model_name = linked_model.split(":")[0]
            if self.workflow_wizard.source_model.add_source(
                model_name,
                "model",
                None,
                self.tr("Linked model referenced over ilidata repository."),
            ):
                self.workflow_wizard.refresh_import_models()

    def _load_crs_from_metaconfig(self, ili2db_metaconfig):
        srs_auth = self.srs_auth
        srs_code = self.srs_code
        if "defaultSrsAuth" in ili2db_metaconfig:
            srs_auth = ili2db_metaconfig.get("defaultSrsAuth")
        if "defaultSrsCode" in ili2db_metaconfig:
            srs_code = ili2db_metaconfig.get("defaultSrsCode")

        crs = QgsCoordinateReferenceSystem("{}:{}".format(srs_auth, srs_code))
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem(srs_code)  # Fallback
        self.crs = crs
        self._update_crs_info()
        self._crs_changed()

    def _load_metaconfig(self):
        self.workflow_wizard.busy(self, True, "Load metaconfiguration...")
        # load ili2db parameters to the GUI
        if "ch.ehi.ili2db" in self.metaconfig.sections():
            self.workflow_wizard.log_panel.print_info(
                self.tr("Load the ili2db configurations from the metaconfig…"),
                LogLevel.TOPPING,
            )

            ili2db_metaconfig = self.metaconfig["ch.ehi.ili2db"]

            if (
                "defaultSrsAuth" in ili2db_metaconfig
                or "defaultSrsCode" in ili2db_metaconfig
            ):
                self._load_crs_from_metaconfig(ili2db_metaconfig)
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Loaded CRS"), LogLevel.TOPPING
                )

            if "models" in ili2db_metaconfig:
                for model in ili2db_metaconfig.get("models").strip().split(";"):
                    self.workflow_wizard.source_model.add_source(
                        model,
                        "model",
                        None,
                        self.tr("Model defined in metaconfigurationfile."),
                    )
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Loaded models"), LogLevel.TOPPING
                )

            # get iliMetaAttrs (toml)
            if "iliMetaAttrs" in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Seek for iliMetaAttrs (toml) files:"),
                    LogLevel.TOPPING,
                )
                ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
                ili_meta_attrs_file_path_list = (
                    self.workflow_wizard.get_topping_file_list(ili_meta_attrs_list)
                )
                self.ili2db_options.load_toml_file_path(
                    ";".join(self.model_list_view.model().checked_models()),
                    ";".join(ili_meta_attrs_file_path_list),
                )
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Loaded iliMetaAttrs (toml) files"),
                    LogLevel.TOPPING,
                )

            # get prescript (sql)
            if "preScript" in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Seek for prescript (sql) files:"), LogLevel.TOPPING
                )
                prescript_list = ili2db_metaconfig.get("prescript").split(";")
                prescript_file_path_list = self.workflow_wizard.get_topping_file_list(
                    prescript_list
                )
                self.ili2db_options.load_pre_script_path(
                    ";".join(prescript_file_path_list)
                )
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Loaded prescript (sql) files"), LogLevel.TOPPING
                )

            # get postscript (sql)
            if "postScript" in ili2db_metaconfig:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Seek for postscript (sql) files:"),
                    LogLevel.TOPPING,
                )
                postscript_list = ili2db_metaconfig.get("postscript").split(";")
                postscript_file_path_list = self.workflow_wizard.get_topping_file_list(
                    postscript_list
                )
                self.ili2db_options.load_post_script_path(
                    ";".join(postscript_file_path_list)
                )
                self.workflow_wizard.log_panel.print_info(
                    self.tr("- Loaded postscript (sql) files"), LogLevel.TOPPING
                )

            self.ili2db_options.load_metaconfig(ili2db_metaconfig)
            self.workflow_wizard.log_panel.print_info(
                self.tr("- Loaded ili2db options"), LogLevel.TOPPING
            )

        if "CONFIGURATION" in self.metaconfig.sections():
            configuration_section = self.metaconfig["CONFIGURATION"]

            # check if only ili2db parameters from metaconfig should be considered
            self._disable_settings(
                configuration_section.getboolean(
                    "qgis.modelbaker.metaConfigParamsOnly", fallback=False
                )
            )

            # get referenceData file and update the source model
            if "ch.interlis.referenceData" in configuration_section:
                self.workflow_wizard.log_panel.print_info(
                    self.tr(
                        "Metaconfig contains transfer or catalogue files (referenced data)."
                    ),
                    LogLevel.TOPPING,
                )
                reference_data_list = configuration_section[
                    "ch.interlis.referenceData"
                ].split(";")
                referencedata_file_path_list = (
                    self.workflow_wizard.get_topping_file_list(reference_data_list)
                )
                for referencedata_file_path in referencedata_file_path_list:
                    if os.path.isfile(referencedata_file_path):
                        name = pathlib.Path(referencedata_file_path).name
                        type = pathlib.Path(referencedata_file_path).suffix[1:]
                        self.workflow_wizard.log_panel.print_info(
                            self.tr("Append referenced data file {}…").format(
                                referencedata_file_path
                            ),
                            LogLevel.TOPPING,
                        )
                        self.workflow_wizard.source_model.add_source(
                            name,
                            type,
                            referencedata_file_path,
                            self.tr(
                                "Datafile referenced in the metaconfigurationfile."
                            ),
                        )
                    else:
                        self.workflow_wizard.log_panel.print_info(
                            self.tr("Could not append referenced data file {}…").format(
                                referencedata_file_path
                            ),
                            LogLevel.TOPPING,
                        )
            self.workflow_wizard.refresh_import_models()

        self.workflow_wizard.busy(self, False)

    def help_text(self):
        logline = self.tr(
            "Now the given models are detected. You may not need all of 'em..."
        )
        help_paragraphs = self.tr(
            """
        <p align="justify">There are several ways the Model Baker wizard detects INTERLIS models:
        <ul>
        <li>Read from the selected local ini file.</li>
        <li>Selected from the repositories.</li>
        <li>Parsed from the selected transfer or catalogue files.</li>
        <li>Depending model of a catalogue referenced in the ilidata.xml of the repositories.</li>
        <li>Defined as ili2db attribute in the metaconfiguration received from the repositories.</li>
        </ul></p>
        <p align="justify">You can <b>check or uncheck</b> the models you want to import to a physical schema.</p>
        <p align="justify">As well you can select a <b>Metaconfiguration</b> file from the repositories to load ili2db settings and styling properties into QGIS project.<br />
        More information about those metaconfigurations in the <a href="https://opengisch.github.io/QgisModelBaker/background_info/usabilityhub/modelbaker_integration/">documentation</a>.</p>
        <p align="justify">The <b>Advanced Options</b> allow you to edit the most important <b>ili2db settings</b></p>
        """
        )
        docutext = self.tr(
            'Find more information about this in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/#3-import-of-interlis-model">documentation</a>...'
        )
        return logline, help_paragraphs, docutext
