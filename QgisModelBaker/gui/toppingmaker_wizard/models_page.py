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

from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/models.ui")


class ModelsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setTitle(title)


"""
# on this page we get the current project
# we go through the project and load all the models
# for that we might need to extend the SchemaModelsModel of gui utils
    def load_available_models(self, project: QgsProject):
        root = project.layerTreeRoot()
        checked_identificators = []
        for layer_node in root.findLayers():
            source_provider = layer_node.layer().dataProvider()
            source = QgsDataSourceUri(layer_node.layer().dataProvider().dataSourceUri())
            schema_identificator = db_utils.get_schema_identificator_from_layersource(source_provider, source)
            if schema_identificator in checked_identificators:
                continue
            else:
                checked_identificators.append(schema_identificator)
                current_configuration = Ili2DbCommandConfiguration
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, current_configuration
                )
                if valid and mode:
                     db_connector = db_utils.get_db_connector(self.current_configuration)
                    self.schema_validations[
                        self.current_schema_identificator
                    ].models_model.refresh_model(db_connector)
"""
