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

import os

import yaml
from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import IliToppingFileItemModel
from QgisModelBaker.libs.modelbaker.utils.globals import OptimizeStrategy
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.globals import CATALOGUE_DATASETNAME
from QgisModelBaker.utils.gui_utils import LogColor

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/project_creation.ui")


class ProjectCreationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)

        self.optimize_combo.clear()
        self.optimize_combo.addItem(
            self.tr("Hide unused base class layers"), OptimizeStrategy.HIDE
        )
        self.optimize_combo.addItem(
            self.tr("Group unused base class layers"), OptimizeStrategy.GROUP
        )
        self.optimize_combo.addItem(self.tr("No optimization"), OptimizeStrategy.NONE)

        self.db_simple_factory = DbSimpleFactory()
        self.configuration = None

        self.create_project_button.clicked.connect(self._create_project)

        self.is_complete = False

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.create_project_button.setDisabled(complete)
        self.completeChanged.emit()

    def restore_configuration(self, configuration):
        self.configuration = configuration

    def _create_project(self):
        self.progress_bar.setValue(0)

        db_factory = self.db_simple_factory.create_factory(self.configuration.tool)

        try:
            config_manager = db_factory.get_db_command_config_manager(
                self.configuration
            )
            uri = config_manager.get_uri(qgis=True)
            mgmt_uri = config_manager.get_uri(self.configuration.db_use_super_login)
            generator = Generator(
                self.configuration.tool,
                uri,
                self.configuration.inheritance,
                self.configuration.dbschema,
                mgmt_uri=mgmt_uri,
                consider_basket_handling=True,
                optimize_strategy=self.optimize_combo.currentData(),
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

        res, message = db_factory.post_generate_project_validations(self.configuration)

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

        self.workflow_wizard.log_panel.print_info(
            self.tr("Arranging layers into groups…")
        )
        legend = generator.legend(available_layers)

        custom_layer_order_structure = list()
        custom_project_properties = {}
        mapthemes = {}
        resolved_layouts = {}
        custom_variables = {}

        # Project topping file for legend and layers: collect and download
        projecttopping_file_path_list = []
        if (
            self.configuration.metaconfig
            and "CONFIGURATION" in self.configuration.metaconfig.sections()
        ):
            configuration_section = self.configuration.metaconfig["CONFIGURATION"]
            # get topping referenced in qgis.modelbaker.projecttopping
            key = "qgis.modelbaker.projecttopping"
            if key not in configuration_section:
                key = "qgis.modelbaker.layertree"
                self.workflow_wizard.log_panel.print_info(
                    self.tr(
                        'Keyword "qgis.modelbaker.layertree" is deprecated (but still working). Use "qgis.modelbaker.projecttopping" instead.'
                    ),
                    LogColor.COLOR_TOPPING,
                )

            if key in configuration_section:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("Metaconfig contains a project topping."),
                    LogColor.COLOR_TOPPING,
                )
                projecttopping_data_list = configuration_section[key].split(";")
                projecttopping_file_path_list = (
                    self.workflow_wizard.get_topping_file_list(projecttopping_data_list)
                )

        if len(projecttopping_file_path_list) > 1:
            self.workflow_wizard.log_panel.print_info(
                self.tr(
                    "Multiple project toppings can lead to unexpected behavior, when the sections are not clearly separated."
                ),
                LogColor.COLOR_TOPPING,
            )

        for projecttopping_file_path in projecttopping_file_path_list:
            self.workflow_wizard.log_panel.print_info(
                self.tr("Parse project topping file {}…").format(
                    projecttopping_file_path
                ),
                LogColor.COLOR_TOPPING,
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
                            LogColor.COLOR_TOPPING,
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

                    # properties (inoffical)
                    if "properties" in projecttopping_data:
                        custom_project_properties = projecttopping_data["properties"]

                except yaml.YAMLError as exc:
                    self.workflow_wizard.log_panel.print_info(
                        self.tr("Unable to parse project topping: {}").format(exc),
                        LogColor.COLOR_TOPPING,
                    )

        self.progress_bar.setValue(55)

        transaction_mode = custom_project_properties.get("transaction_mode", None)

        if Qgis.QGIS_VERSION_INT < 32600:
            # pass transaction_mode as boolean
            if transaction_mode is None:
                # on geopackages we don't use the transaction mode on default otherwise we do
                transaction_mode = not bool(self.configuration.tool & DbIliMode.gpkg)
            else:
                transaction_mode = custom_transaction_mode == "AutomaticGroups"
        else:
            # pass transaction_mode as string
            if transaction_mode is None:
                # on geopackages we don't use the transaction mode on default otherwise we do
                transaction_mode = (
                    "Disabled"
                    if not bool(self.configuration.tool & DbIliMode.gpkg)
                    else "AutomaticGroups"
                )
            else:
                # in case the topping used True/False value we need to convert
                if transaction_mode is True:
                    transaction_mode = "AutomaticGroups"
                if transaction_mode is False:
                    transaction_mode = "Disabled"
                # otherwise it's already a string and could be everything

        project = Project(
            auto_transaction=transaction_mode,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
            optimize_strategy=self.optimize_combo.currentData(),
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

        qgis_project = QgsProject.instance()

        self.workflow_wizard.log_panel.print_info(self.tr("Generate QGIS project…"))
        project.create(None, qgis_project)

        # Set the extent of the mapCanvas from the first layer extent found
        for layer in project.layers:
            if layer.extent is not None:
                self.workflow_wizard.iface.mapCanvas().setExtent(layer.extent)
                self.workflow_wizard.iface.mapCanvas().refresh()
                break

        self.progress_bar.setValue(60)

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
                LogColor.COLOR_TOPPING,
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
                        Qt.DisplayRole,
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
                            LogColor.COLOR_TOPPING,
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
