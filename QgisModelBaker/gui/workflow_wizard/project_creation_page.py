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
import re

import yaml
from osgeo import gdal
from qgis.core import Qgis, QgsApplication, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QCompleter, QWizardPage

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import (
    IliDataCache,
    IliDataFileCompleterDelegate,
    IliDataItemModel,
    IliToppingFileItemModel,
)
from QgisModelBaker.libs.modelbaker.utils.globals import OptimizeStrategy
from QgisModelBaker.libs.modelbaker.utils.qt_utils import make_file_selector
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.globals import CATALOGUE_DATASETNAME, displayLanguages
from QgisModelBaker.utils.gui_utils import MODELS_BLACKLIST, LogLevel

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/project_creation.ui")


class ProjectCreationPage(QWizardPage, PAGE_UI):

    ValidExtensions = ["YAML", "yaml"]

    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.db_simple_factory = DbSimpleFactory()
        self.configuration = None

        self.existing_projecttopping_id = None
        self.projecttopping_id = None
        self.db_connector = None

        self._update_optimize_combo()
        self._update_translation_combo()

        self.create_project_button.clicked.connect(self._create_project)
        self.is_complete = False

        self.existing_topping_checkbox.setVisible(False)
        self.existing_topping_checkbox.stateChanged.connect(self._use_existing)

        self.ilitoppingcache = IliDataCache(None)
        self.ilitopping_delegate = IliDataFileCompleterDelegate()
        self.topping_line_edit.setPlaceholderText(
            self.tr("[Search project toppings on the repositories or the local system]")
        )
        self.topping_line_edit.textChanged.connect(self._complete_completer)
        self.topping_line_edit.punched.connect(self._complete_completer)
        self.topping_line_edit.textChanged.emit(self.topping_line_edit.text())
        self.topping_line_edit.textChanged.connect(self._on_completer_activated)
        self.topping_file_browse_button.clicked.connect(
            make_file_selector(
                self.topping_line_edit,
                title=self.tr("Project Topping"),
                file_filter=self.tr("Project Topping File (*.yaml *.YAML)"),
            )
        )
        self.fileValidator = gui_utils.FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions], allow_empty=False
        )
        self.gpkg_multigeometry_frame.setVisible(False)

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.create_project_button.setDisabled(complete)
        self.completeChanged.emit()

    def restore_configuration(self, configuration):
        self.workflow_wizard.busy(
            self,
            True,
            self.tr("Restoring configuration and check existing metaconfigfile..."),
        )
        self.configuration = configuration
        self.db_connector = db_utils.get_db_connector(self.configuration)

        # get inheritance
        self.configuration.inheritance = self._inheritance()
        self._update_optimize_combo()

        # get translation languages
        self._update_translation_combo()

        # get existing topping
        self.existing_topping_checkbox.setVisible(False)
        self.existing_projecttopping_id = self._existing_projecttopping_id()
        if self.existing_projecttopping_id:
            self.existing_topping_checkbox.setVisible(True)
            # with setting it checked _use_existing is called
            self.existing_topping_checkbox.setChecked(True)
        else:
            self._use_existing(False)

        self.gpkg_multigeometry_frame.setVisible(self._multigeom_gpkg())

        self.workflow_wizard.busy(self, False)

    def _use_existing(self, state):
        # triggered by checked state.
        if state:
            self._clean_topping()
            self.projecttopping_id = self.existing_projecttopping_id
            self._set_topping_info(True)
            # disable other widgets
            self._enable_topping_selection(False)
            self._enable_optimize_combo(False)
            self.topping_line_edit.setText("")
        else:
            self._clean_topping()
            self.ilitoppingcache = IliDataCache(
                self.configuration.base_configuration,
                type="projecttopping",
                models=";".join(self._modelnames()),
                datasources=["pg"]
                if (
                    self.workflow_wizard.import_schema_configuration.tool & DbIliMode.pg
                )
                else ["gpkg"]
                if (
                    self.workflow_wizard.import_schema_configuration.tool
                    & DbIliMode.gpkg
                )
                else None,
            )
            self.ilitoppingcache.new_message.connect(
                self.workflow_wizard.log_panel.show_message
            )
            # wait before activating until end of refreshment
            self.workflow_wizard.busy(self, True, self.tr("Refresh repository data..."))
            self.ilitoppingcache.model_refreshed.connect(self._enable_topping_selection)
            self._enable_optimize_combo(True)
            self.ilitoppingcache.refresh()

            completer = QCompleter(
                self.ilitoppingcache.sorted_model,
                self.topping_line_edit,
            )
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setModelSorting(
                QCompleter.ModelSorting.CaseInsensitivelySortedModel
            )
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.popup().setItemDelegate(self.ilitopping_delegate)
            self.topping_line_edit.setCompleter(completer)

    def _enable_topping_selection(self, state):
        # doublecheck if meanwhile user checked box again
        if state:
            state = state and not self.existing_topping_checkbox.isChecked()
        self.topping_file_browse_button.setEnabled(state)
        self.topping_line_edit.setEnabled(state)
        self.topping_line_label.setEnabled(state)
        self.topping_info.setEnabled(state)

        self.workflow_wizard.busy(self, False)

    def _enable_optimize_combo(self, state):
        self.optimize_combo.setEnabled(state)
        self.optimize_label.setEnabled(state)

    def _update_optimize_combo(self):
        index = self.optimize_combo.currentIndex()
        self.optimize_combo.clear()
        if self.configuration and self.configuration.inheritance == "smart2":
            self.optimize_combo.addItem(
                self.tr("Hide unused base class layers"), OptimizeStrategy.HIDE
            )
            self.optimize_combo.addItem(
                self.tr("Group unused base class layers"), OptimizeStrategy.GROUP
            )
            self.optimize_combo.setToolTip(
                self.tr(
                    """
                <html><head/><body>
                    <p><b>Hide unused base class layers:</b></p>
                    <p>- Base class layers with same named extensions will be <i>hidden</i> and and base class layers with multiple extensions as well. Except if the extension is in the same model, then it's will <i>not</i> be <i>hidden</i> but <i>renamed</i>.</p>
                    <p>- Relations of hidden layers will <i>not</i> be <i>created</i> and with them <i>no</i> widgets<br/></p>
                    <p><b>Group unused base class layers:</b></p>
                    <p>- Base class layers with same named extensions will be <i>collected in a group</i> and base class layers with multiple extensions as well. Except if the extension is in the same model, then it will <i>not</i> be <i>grouped</i> but <i>renamed</i>.</p>
                    <p>- Relations of grouped layers will be <i>created</i> but the widgets <i>not applied</i> to the form.</p>
                </body></html>
            """
                )
            )
        else:
            self.optimize_combo.addItem(
                self.tr("Hide unused base class types"), OptimizeStrategy.HIDE
            )
            self.optimize_combo.setToolTip(
                self.tr(
                    """
                <html><head/><body>
                    <p><b>Hide unused base class types:</b></p>
                    <p>- Base class tables with same named extensions will be <i>hidden</i> in the <code>t_type</code> dropdown and and base class tables with multiple extensions as well. Except if the extension is in the same model, then it will <i>not</i> be <i>hidden</i>.</p>
                </body></html>
            """
                )
            )
        self.optimize_combo.addItem(self.tr("No optimization"), OptimizeStrategy.NONE)
        self.optimize_combo.setCurrentIndex(index)

    def _update_translation_combo(self):
        self.translation_combo.clear()

        if self.db_connector:
            available_languages = self.db_connector.get_available_languages(
                MODELS_BLACKLIST
            )
            if len(available_languages) > 1:
                for lang in available_languages:
                    self.translation_combo.addItem(
                        displayLanguages.get(lang, lang), lang
                    )
                translation_lang = self.db_connector.get_available_languages(
                    MODELS_BLACKLIST, self.db_connector.get_translation_models()
                )
                if len(translation_lang) > 0:
                    self.translation_combo.setCurrentText(
                        displayLanguages.get(translation_lang[0], translation_lang[0])
                    )
                self.translation_combo.setEnabled(True)
            else:
                self.translation_combo.setEnabled(False)

        self.translation_combo.addItem(self.tr("Original model language"), "__")

        # Synchronize length of both comboboxes
        self.translation_combo.setMinimumSize(self.optimize_combo.minimumSizeHint())

    def _complete_completer(self):
        if self.topping_line_edit.hasFocus() and self.topping_line_edit.completer():
            if not self.topping_line_edit.text():
                self.topping_line_edit.completer().setCompletionMode(
                    QCompleter.CompletionMode.UnfilteredPopupCompletion
                )
                self.topping_line_edit.completer().complete()
            else:
                match_contains = (
                    self.topping_line_edit.completer()
                    .completionModel()
                    .match(
                        self.topping_line_edit.completer()
                        .completionModel()
                        .index(0, 0),
                        Qt.ItemDataRole.DisplayRole,
                        self.topping_line_edit.text(),
                        -1,
                        Qt.MatchFlag.MatchContains,
                    )
                )
                if len(match_contains) > 1:
                    self.topping_line_edit.completer().setCompletionMode(
                        QCompleter.CompletionMode.PopupCompletion
                    )
                    self.topping_line_edit.completer().complete()
            self.topping_line_edit.completer().popup().scrollToTop()

    def _on_completer_activated(self, text=None):
        self._clean_topping()
        if os.path.isfile(self.topping_line_edit.text()):
            self.projecttopping_id = self.topping_line_edit.text()
            self._set_topping_info(True)
            self._enable_optimize_combo(False)
            return

        matches = self.ilitoppingcache.model.match(
            self.ilitoppingcache.model.index(0, 0),
            Qt.ItemDataRole.DisplayRole,
            self.topping_line_edit.text(),
            1,
            Qt.MatchFlag.MatchExactly,
        )
        if matches:
            model_index = matches[0]
            self.projecttopping_id = f"ilidata:{self.ilitoppingcache.model.data(model_index, int(IliDataItemModel.Roles.ID))}"
            self._set_topping_info(True, model_index)
            self._enable_optimize_combo(False)
            return

        self._set_topping_info(not self.topping_line_edit.text())
        self._enable_optimize_combo(True)

    def _clean_topping(self):
        self.projecttopping_id = None
        self.topping_info.setText("")

    def _set_topping_info(self, valid, index=None):
        if self.projecttopping_id:
            if index:
                if self.existing_topping_checkbox.isChecked():
                    info = self.tr(
                        "Project topping received according to the id found in the database or selected previously"
                    )
                else:
                    info = self.tr("Project topping received according selection")
                self.topping_info.setText(
                    "<html><head/><body><p><b>{} ({})</b><br><i><b>{}</b></i></p></body></html>".format(
                        info,
                        self.projecttopping_id,
                        self.ilitoppingcache.model.data(
                            index, int(IliDataItemModel.Roles.SHORT_DESCRIPTION)
                        )
                        or "",
                    )
                )
            else:
                self.topping_info.setText(
                    self.tr(
                        "<html><head/><body><p><b>Project topping from file {}</b></p></body></html>"
                    ).format(self.projecttopping_id)
                )

            self.topping_info.setStyleSheet(f"color: {LogLevel.TOPPING}")

        self.topping_line_edit.setStyleSheet(
            "QLineEdit {{ background-color: {} }}".format(
                "#ffffff" if valid else "#ffd356"
            )
        )

    def _create_project(self):
        self.progress_bar.setValue(0)

        if not self.db_connector:
            self.workflow_wizard.log_panel.print_info(
                self.tr("Cannot connect to the database…"), LogLevel.FAIL
            )
            return

        db_factory = self.db_simple_factory.create_factory(self.configuration.tool)

        try:
            config_manager = db_factory.get_db_command_config_manager(
                self.configuration
            )
            uri = config_manager.get_uri(qgis=True)
            mgmt_uri = config_manager.get_uri(
                su=self.configuration.db_use_super_login,
                fallback_user=QgsApplication.userLoginName(),
            )
            generator = Generator(
                self.configuration.tool,
                uri,
                self.configuration.inheritance,
                self.configuration.dbschema,
                mgmt_uri=mgmt_uri,
                consider_basket_handling=True,
                optimize_strategy=self.optimize_combo.currentData(),
                preferred_language=self.translation_combo.currentData(),
            )
            generator.stdout.connect(self.workflow_wizard.log_panel.print_info)
            generator.new_message.connect(self.workflow_wizard.log_panel.show_message)
            self.progress_bar.setValue(30)
        except DBConnectorError as db_connector_error:
            self.workflow_wizard.log_panel.txtStdout.setText(
                self.tr(
                    "There was an error connecting to the database. Check connection parameters. Error details: {}".format(
                        db_connector_error
                    )
                )
            )
            self.progress_bar.setValue(0)
            return
        except FileNotFoundError as file_not_found_error:
            self.workflow_wizard.log_panel.txtStdout.setText(
                self.tr(
                    "There was an error connecting to the database. Check connection parameters. Error details: {}".format(
                        file_not_found_error
                    )
                )
            )
            self.progress_bar.setValue(0)
            return

        if not generator.db_or_schema_exists():
            self.workflow_wizard.log_panel.txtStdout.setText(
                self.tr(
                    "Source {} does not exist. Check connection parameters."
                ).format(db_factory.get_specific_messages()["db_or_schema"])
            )
            self.progress_bar.setValue(0)
            return

        res, message = db_factory.post_generate_project_validations(
            self.configuration, QgsApplication.userLoginName()
        )

        if not res:
            self.workflow_wizard.log_panel.txtStdout.setText(message)
            self.progress_bar.setValue(0)
            return

        self.workflow_wizard.log_panel.print_info(
            f'\n{self.tr("Obtaining available layers from the database…")}'
        )

        available_layers = generator.layers()

        if not available_layers:
            text = self.tr("The {} has no layers to load into QGIS.").format(
                db_factory.get_specific_messages()["layers_source"]
            )

            self.workflow_wizard.log_panel.txtStdout.setText(text)
            self.progress_bar.setValue(0)
            return

        self.progress_bar.setValue(40)
        self.workflow_wizard.log_panel.print_info(
            self.tr("Obtaining relations from the database…")
        )
        relations, bags_of_enum = generator.relations(available_layers)
        self.progress_bar.setValue(45)

        # If coalesceCatalogueRef was used, suppress any catalogue
        # ref layer that doesn't have a BAG OF attribute. Those
        # ref layers are not needed to create data.
        coalesce_catalogue_used = False
        setting_records = self.db_connector.get_ili2db_settings()

        for setting_record in setting_records:
            if (
                setting_record["tag"] == "ch.ehi.ili2db.catalogueRefTrafo"
                and setting_record["setting"] == "coalesce"
            ):
                coalesce_catalogue_used = True
                break

        if coalesce_catalogue_used:
            layer_count_before = len(available_layers)
            relation_count_before = len(relations)
            available_layers, relations = generator.suppress_catalogue_reference_layers(
                available_layers, relations, bags_of_enum
            )
            if layer_count_before - len(available_layers) > 0:
                self.workflow_wizard.log_panel.print_info(
                    self.tr(
                        "Filtering out {} catalogue reference layer(s) (not BAG OF) and {} relation(s)…".format(
                            layer_count_before - len(available_layers),
                            relation_count_before - len(relations),
                        )
                    )
                )

        self.workflow_wizard.log_panel.print_info(
            self.tr("Arranging layers into groups…")
        )
        legend = generator.legend(available_layers, hide_systemlayers=True)

        self.progress_bar.setValue(50)

        custom_layer_order_structure = list()
        custom_project_properties = {}
        mapthemes = {}
        resolved_layouts = {}
        custom_variables = {}

        if self.projecttopping_id:
            # Project topping file for legend and layers: collect and download
            projecttopping_file_path = self.ilidata_path_resolver(
                "", self.projecttopping_id
            )

            if projecttopping_file_path:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("Parse project topping file {}…").format(
                        projecttopping_file_path
                    ),
                    LogLevel.TOPPING,
                )
                with open(projecttopping_file_path) as stream:
                    try:
                        projecttopping_data = yaml.safe_load(stream)

                        # layertree / legend
                        layertree_key = "layertree"
                        if layertree_key not in projecttopping_data:
                            layertree_key = "legend"
                            self.workflow_wizard.log_panel.print_info(
                                self.tr(
                                    'Keyword "legend" is deprecated (but still working).. Use "layertree" instead.'
                                ),
                                LogLevel.TOPPING,
                            )
                        if layertree_key in projecttopping_data:
                            legend = generator.legend(
                                available_layers,
                                layertree_structure=projecttopping_data[layertree_key],
                                path_resolver=lambda path: self.ilidata_path_resolver(
                                    os.path.dirname(projecttopping_file_path), path
                                )
                                if path
                                else None,
                            )

                        # layer order
                        layerorder_key = "layerorder"
                        if layerorder_key not in projecttopping_data:
                            layerorder_key = "layer-order"

                        if layerorder_key in projecttopping_data:
                            custom_layer_order_structure = projecttopping_data[
                                layerorder_key
                            ]

                        # map themes
                        if "mapthemes" in projecttopping_data:
                            mapthemes = projecttopping_data["mapthemes"]

                        # layouts
                        if "layouts" in projecttopping_data:
                            resolved_layouts = generator.resolved_layouts(
                                projecttopping_data["layouts"],
                                path_resolver=lambda path: self.ilidata_path_resolver(
                                    os.path.dirname(projecttopping_file_path), path
                                )
                                if path
                                else None,
                            )

                        # variables
                        if "variables" in projecttopping_data:
                            custom_variables = projecttopping_data["variables"]

                        # properties
                        if "properties" in projecttopping_data:
                            custom_project_properties = projecttopping_data[
                                "properties"
                            ]

                    except yaml.YAMLError as exc:
                        self.workflow_wizard.log_panel.print_info(
                            self.tr("Unable to parse project topping: {}").format(exc),
                            LogLevel.TOPPING,
                        )

        self.progress_bar.setValue(55)

        self.workflow_wizard.log_panel.print_info(self.tr("Set transaction mode…"))
        # override transaction mode if given by topping
        transaction_mode = custom_project_properties.get("transaction_mode", None)

        if Qgis.QGIS_VERSION_INT < 32600:
            # For backwards compatibility, we support booleans,
            # but convert them to strings to match the new API
            if transaction_mode is None:
                # on geopackages we don't use the transaction mode on default otherwise we do
                transaction_mode = str(
                    not bool(self.configuration.tool & DbIliMode.gpkg)
                )
            else:
                transaction_mode = str(transaction_mode)
        else:
            # pass transaction_mode as string
            if transaction_mode is None:
                # on both PG and GPKG we use the transaction mode by default
                transaction_mode = Qgis.TransactionMode.AutomaticGroups.name
            else:
                # in case the topping used True/False value we need to convert
                if transaction_mode is True:
                    transaction_mode = Qgis.TransactionMode.AutomaticGroups.name
                if transaction_mode is False:
                    transaction_mode = Qgis.TransactionMode.Disabled.name
                # otherwise it's already a string and could be everything

        self.progress_bar.setValue(60)

        self.workflow_wizard.log_panel.print_info(
            self.tr("Optimize according the strategy...")
        )

        # override optimize strategy if give n by topic
        optimize_strategy = custom_project_properties.get("ili_optimize_strategy", None)

        if optimize_strategy == "HIDE":
            optimize_strategy = OptimizeStrategy.HIDE
        elif optimize_strategy == "GROUP":
            optimize_strategy = OptimizeStrategy.GROUP
        elif optimize_strategy == "NONE":
            optimize_strategy = OptimizeStrategy.NONE
        else:
            optimize_strategy = self.optimize_combo.currentData()

        project = Project(
            auto_transaction=transaction_mode,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
            optimize_strategy=optimize_strategy,
            log_function=self.workflow_wizard.log_panel.print_info,
        )
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.mapthemes = mapthemes
        project.layouts = resolved_layouts
        project.custom_variables = custom_variables

        self.workflow_wizard.log_panel.print_info(
            self.tr("Configure forms and widgets…")
        )
        project.post_generate()

        self.progress_bar.setValue(70)

        qgis_project = QgsProject.instance()

        self.workflow_wizard.log_panel.print_info(self.tr("Generate QGIS project…"))
        project.create(None, qgis_project)

        self.progress_bar.setValue(75)

        self.workflow_wizard.log_panel.print_info(self.tr("Set map canvas extent..."))

        # Set the extent of the mapCanvas from the first layer extent found
        for layer in project.layers:
            if layer.extent is not None:
                self.workflow_wizard.iface.mapCanvas().setExtent(layer.extent)
                self.workflow_wizard.iface.mapCanvas().refresh()
                break

        self.progress_bar.setValue(80)

        # QML Toppings in the metadata: collect, download and apply
        # This configuration is legacy (should be in project topping instead), but it's still supported
        if (
            self.configuration.metaconfig
            and "qgis.modelbaker.qml" in self.configuration.metaconfig.sections()
        ):
            self.workflow_wizard.log_panel.print_info(
                self.tr(
                    "Metaconfig contains QML toppings. Better practice would be to define QML toppings in the project topping file."
                ),
                LogLevel.TOPPING,
            )
            qml_section = dict(self.configuration.metaconfig["qgis.modelbaker.qml"])
            qml_file_model = self.workflow_wizard.get_topping_file_model(
                list(qml_section.values())
            )
            for layer in project.layers:
                if layer.alias:
                    if any(layer.alias.lower() == s for s in qml_section):
                        layer_qml = layer.alias.lower()
                    elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                        layer_qml = f'"{layer.alias.lower()}"'
                    else:
                        continue
                    matches = qml_file_model.match(
                        qml_file_model.index(0, 0),
                        Qt.ItemDataRole.DisplayRole,
                        qml_section[layer_qml],
                        1,
                    )
                    if matches:
                        style_file_path = matches[0].data(
                            int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                        )
                        self.workflow_wizard.log_panel.print_info(
                            self.tr("Apply QML topping on layer {}:{}…").format(
                                layer.alias, style_file_path
                            ),
                            LogLevel.TOPPING,
                        )
                        layer.layer.loadNamedStyle(style_file_path)

        self.progress_bar.setValue(100)
        self.setStyleSheet(gui_utils.SUCCESS_STYLE)
        self.workflow_wizard.log_panel.print_info(self.tr("It's served!"))
        self.setComplete(True)

    def ilidata_path_resolver(self, base_path, path):
        if "ilidata:" in path or "file:" in path:
            data_file_path_list = self.workflow_wizard.get_topping_file_list([path])
            return data_file_path_list[0] if data_file_path_list else None
        return os.path.join(base_path, path)

    def _datasource_metaconfig(self):
        metaconfig_id = None
        if not self.db_connector:
            return None
        setting_records = self.db_connector.get_ili2db_settings()
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.metaConfigFileName":
                metaconfig_id = setting_record["setting"]
                break
        if metaconfig_id:
            metaconfig_file_path_list = self.workflow_wizard.get_topping_file_list(
                [metaconfig_id]
            )

            if not metaconfig_file_path_list:
                self.workflow_wizard.log_panel.print_info(
                    self.tr(
                        "Found a metaconfig-id ({}) in the data source, but no corresponding metaconfig in the repositories."
                    ).format(metaconfig_id),
                    LogLevel.TOPPING,
                )
                return None

            metaconfig = configparser.ConfigParser()
            with open(metaconfig_file_path_list[0]) as metaconfig_file:
                metaconfig.read_file(metaconfig_file)
                return metaconfig

        return None

    def _existing_projecttopping_id(self):
        metaconfig = self.configuration.metaconfig

        if not metaconfig:
            metaconfig = self._datasource_metaconfig()

        if not metaconfig:
            # no existing metaconfig available
            return None

        # get projecttopping_id from metaconfig
        if "CONFIGURATION" in metaconfig.sections():
            configuration_section = metaconfig["CONFIGURATION"]
            # get topping referenced in qgis.modelbaker.projecttopping
            key = "qgis.modelbaker.projecttopping"
            if key not in configuration_section:
                key = "qgis.modelbaker.layertree"
                self.workflow_wizard.log_panel.print_info(
                    self.tr(
                        'Keyword "qgis.modelbaker.layertree" is deprecated (but still working). Use "qgis.modelbaker.projecttopping" instead.'
                    ),
                    LogLevel.TOPPING,
                )

            if key in configuration_section:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("Metaconfig contains a project topping."),
                    LogLevel.TOPPING,
                )
                projecttopping_id_list = configuration_section[key].split(";")
                if len(projecttopping_id_list) > 1:
                    self.workflow_wizard.log_panel.print_info(
                        self.tr(
                            "Only one projec topping allowed. Taking first one of the list."
                        ),
                        LogLevel.TOPPING,
                    )
                return projecttopping_id_list[0]
        return None

    def _modelnames(self):
        modelnames = []
        if self.db_connector:
            db_models = self.db_connector.get_models()
            regex = re.compile(r"(?:\{[^\}]*\}|\s)")
            for db_model in db_models:
                for modelname in regex.split(db_model["modelname"]):
                    name = modelname.strip()
                    if name and name not in MODELS_BLACKLIST and name not in modelnames:
                        modelnames.append(name)
        return modelnames

    def _inheritance(self):
        if self.db_connector:
            setting_records = self.db_connector.get_ili2db_settings()
            for setting_record in setting_records:
                if setting_record["tag"] == "ch.ehi.ili2db.inheritanceTrafo":
                    return setting_record["setting"]

    def _multigeom_gpkg(self):
        # this concerns only geopackage
        if not (self.workflow_wizard.import_schema_configuration.tool & DbIliMode.gpkg):
            return False

        # and when this geopackage has multiple geometry columns in a table
        if len(self.db_connector.multiple_geometry_tables()) == 0:
            return False

        if int(gdal.VersionInfo("VERSION_NUM")) < 3080000:
            self.gpkg_multigeometry_label.setText(
                """
                <html><head/><body style="background-color:powderblue;">
                     <p><b>This GeoPackage contains at least one table with multiple geometries</b></p>
                    <p>These tables require <span style=" font-weight:600;">GDAL version &gt;= 3.8</span> to run in QGIS, yours is <span style=" font-weight:600;">{gdal_version}</span>.</p>
                    <p>Means this won't work.</p>
                </body></html>
                """.format(
                    qgis_version=Qgis.QGIS_VERSION,
                    gdal_version=gdal.VersionInfo("RELEASE_NAME"),
                )
            )
            self.create_project_button.setDisabled(True)
        else:
            self.gpkg_multigeometry_label.setText(
                """
                <html><head/><body style="background-color:powderblue;">
                    <p><b>This GeoPackage contains at least one table with multiple geometries</b></p>
                    <p>These tables require <span style=" font-weight:600;">GDAL version &gt;= 3.8</span> to run in QGIS, yours is <span style=" font-weight:600;">{gdal_version}</span>.</p>
                    <p>But note that others with lower 3.8 version <span style=" font-weight:600;">will not be able</span> to read such tables in the created QGIS project.</p>
                </body></html>
                """.format(
                    qgis_version=Qgis.QGIS_VERSION,
                    gdal_version=gdal.VersionInfo("RELEASE_NAME"),
                )
            )
        return True

    def help_text(self):
        logline = self.tr(
            "Most of the time you won't need to change anything here.<br />Just press Generate :-)"
        )
        help_paragraphs = self.tr(
            """
        <h4>Project Topping</h4>
        <p align="justify">If your database was created using a <b>metaconfiguration</b> (you'd know this), it will now be recognised.</p>
        <p align="justify">If not, you may still be able to choose a <b>project topping</b> from the repositories.</p>
        <h4>Project Optimization</h4>
        <p align="justify">The project is optimized depending on the inheritance structure of the INTERLIS model on which it is based.<br />
        Means it hides unused layers etc. Read more about optimization strategies <a href="https://opengisch.github.io/QgisModelBaker/background_info/extended_models_optimization/">here</a>.</p>
        """
        )
        docutext = self.tr(
            'Find more information about this page in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/#7-generate-the-qgis-project">documentation</a>...'
        )
        return logline, help_paragraphs, docutext
