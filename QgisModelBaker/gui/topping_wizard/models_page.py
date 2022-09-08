# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-08-01
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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

from qgis.core import QgsDataSourceUri, QgsMapLayer, QgsProject
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import SchemaModelsModel

PAGE_UI = gui_utils.get_ui_class("topping_wizard/models.ui")


class ModelsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.models_model = SchemaModelsModel()
        self.items_view.setModel(self.models_model)
        self.items_view.clicked.connect(self.items_view.model().check)
        self.items_view.space_pressed.connect(self.items_view.model().check)

        self.refresh_button.clicked.connect(self._refresh)

    def initializePage(self) -> None:
        self._refresh()
        return super().initializePage()

    def validatePage(self) -> bool:
        self.topping_wizard.topping.models = self.models_model.checked_entries()
        if self.topping_wizard.topping.models:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "Models set: {models}".format(
                        models=", ".join(self.topping_wizard.topping.models)
                    )
                ),
                gui_utils.LogColor.COLOR_SUCCESS,
            )
        else:
            self.topping_wizard.log_panel.print_info(
                self.tr("No models set."),
                gui_utils.LogColor.COLOR_SUCCESS,
            )
        return super().validatePage()

    def _refresh(self):
        self._load_available_models()
        self.models_model.check_entries(self.topping_wizard.topping.models)

    def _load_available_models(self):
        """
        Collects all the available sources in the project and makes the models_model to refresh accordingly.
        """
        checked_identificators = []
        db_connectors = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
                schema_identificator = (
                    db_utils.get_schema_identificator_from_layersource(
                        source_provider, source
                    )
                )
                if schema_identificator in checked_identificators:
                    continue
                else:
                    checked_identificators.append(schema_identificator)
                    current_configuration = Ili2DbCommandConfiguration()
                    valid, mode = db_utils.get_configuration_from_layersource(
                        source_provider, source, current_configuration
                    )
                    if valid and mode:
                        current_configuration.tool = mode
                        db_connector = db_utils.get_db_connector(current_configuration)
                        if db_connector:
                            db_connectors.append(db_connector)
        self.models_model.refresh_model(db_connectors)
