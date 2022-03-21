# -*- coding: utf-8 -*-
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

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libili2db.ilicache import IliToppingFileItemModel

from ...libqgsprojectgen.dataobjects.project import Project
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ...libqgsprojectgen.generator.generator import Generator
from ...utils import gui_utils
from ...utils.globals import CATALOGUE_DATASETNAME
from ...utils.gui_utils import LogColor

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/project_creation.ui")


class ProjectCreationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent

        self.setupUi(self)
        self.setFinalPage(True)
        self.setTitle(title)

        self.db_simple_factory = DbSimpleFactory()
        self.configuration = None

        self.create_project_button.clicked.connect(self._create_project)

    def set_configuration(self, configuration):
        self.configuration = configuration

    def _create_project(self):
        self.progress_bar.setValue(0)

        db_factory = self.db_simple_factory.create_factory(self.configuration.tool)

        try:
            config_manager = db_factory.get_db_command_config_manager(
                self.configuration
            )
            uri = config_manager.get_uri()
            mgmt_uri = config_manager.get_uri(self.configuration.db_use_super_login)
            generator = Generator(
                self.configuration.tool,
                uri,
                self.configuration.inheritance,
                self.configuration.dbschema,
                mgmt_uri=mgmt_uri,
                consider_basket_handling=True,
            )
            generator.stdout.connect(self.workflow_wizard.log_panel.print_info)
            generator.new_message.connect(self.workflow_wizard.log_panel.show_message)
            self.progress_bar.setValue(30)
        except (DBConnectorError, FileNotFoundError):
            self.workflow_wizard.log_panel.txtStdout.setText(
                self.tr(
                    "There was an error connecting to the database. Check connection parameters."
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

        # Project topping file for legend and layers: collect and download
        projecttopping_file_path_list = []
        if (
            self.configuration.metaconfig
            and "CONFIGURATION" in self.configuration.metaconfig.sections()
        ):
            configuration_section = self.configuration.metaconfig["CONFIGURATION"]
            # get topping referenced in qgis.modelbaker.projecttopping
            key = None
            if "qgis.modelbaker.projecttopping" in configuration_section:
                key = "qgis.modelbaker.projecttopping"
            if "qgis.modelbaker.layertree" in configuration_section:
                key = "qgis.modelbaker.layertree"

            if key:
                self.workflow_wizard.log_panel.print_info(
                    self.tr("Metaconfig contains a project topping."),
                    LogColor.COLOR_TOPPING,
                )
                projecttopping_data_list = configuration_section[key].split(";")
                projecttopping_file_path_list = (
                    self.workflow_wizard.get_topping_file_list(projecttopping_data_list)
                )

        # override for test - to remove @dave
        projecttopping_file_path_list = [
            "/home/dave/dev/opengisch/QgisModelBaker/QgisModelBaker/tests/testdata/ilirepo/24/layertree/opengis_projecttopping_ilidata_KbS_LV95_V1_4.yaml"
        ]

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
            with open(projecttopping_file_path, "r") as stream:
                try:
                    projecttopping_data = yaml.safe_load(stream)
                    if "legend" in projecttopping_data:
                        legend = generator.legend(
                            available_layers,
                            layertree_structure=projecttopping_data["legend"],
                            path_resolver=lambda path: self.ilidata_path_resolver(
                                os.path.dirname(projecttopping_file_path), path
                            )
                            if path
                            else None,
                        )
                    if "layer-order" in projecttopping_data:
                        custom_layer_order_structure = projecttopping_data[
                            "layer-order"
                        ]
                except yaml.YAMLError as exc:
                    self.workflow_wizard.log_panel.print_info(
                        self.tr("Unable to parse project topping: {}").format(exc),
                        LogColor.COLOR_TOPPING,
                    )

        self.progress_bar.setValue(55)

        # on geopackages we don't use the transaction mode on default, since this leaded to troubles
        project = Project(
            auto_transaction=not bool(self.configuration.tool & DbIliMode.gpkg),
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure

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
                self.tr("Metaconfig contains QML toppings."), LogColor.COLOR_TOPPING
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
        self.workflow_wizard.log_panel.print_info(self.tr("It's served!"))

    def ilidata_path_resolver(self, base_path, path):
        if "ilidata:" in path or "file:" in path:
            data_file_path_list = self.workflow_wizard.get_topping_file_list([path])
            return data_file_path_list[0] if data_file_path_list else None
        return os.path.join(base_path, path)
