# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 11/11/21
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

from qgis.core import QgsDataSourceUri, QgsExpressionContextUtils
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QStandardPaths, Qt
from qgis.PyQt.QtWidgets import QDockWidget

from QgisModelBaker.libili2db.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.libili2db.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils.db_utils import (
    get_configuration_from_layersource,
    get_schema_identificator_from_layersource,
)
from QgisModelBaker.utils.qt_utils import OverrideCursor, slugify

from ..libili2db import ilivalidator
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..utils import ui

DIALOG_UI = ui.get_ui_class("validator.ui")


class ValidateDock(QDockWidget, DIALOG_UI):
    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.info_label.setText("")
        self.setDisabled(True)
        self.run_button.clicked.connect(self.run)
        self.configuration = ValidateConfiguration()

    def set_current_layer(self, layer):
        self.info_label.setText("")
        self.setDisabled(True)

        if not layer or not layer.dataProvider().isValid():
            return

        source_name = layer.dataProvider().name()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        schema_identificator = get_schema_identificator_from_layersource(
            source_name, source
        )
        layer_model_topic_name = (
            QgsExpressionContextUtils.layerScope(layer).variable("interlis_topic") or ""
        )

        # set the filter of the model according the current uri_identificator
        current_schema_topic_identificator = slugify(
            f"{schema_identificator}_{layer_model_topic_name}"
        )

        valid, mode, self.configuration = get_configuration_from_layersource(
            source_name, source, self.configuration
        )

        if valid and mode:
            output_file_name = "{}.xtf".format(current_schema_topic_identificator)
            self.configuration.xtflog = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                output_file_name,
            )
            self.configuration.tool = mode
            self.info_label.setText(
                f"{current_schema_topic_identificator}\n{layer.name()}\n{self.configuration.database} / {self.configuration.dbschema or self.configuration.dbfile}"
            )
            self.setDisabled(False)

    def run(self, edited_command=None):
        validator = ilivalidator.Validator()
        if validator:
            validator.tool = self.configuration.tool
            validator.configuration = self.configuration

        with OverrideCursor(Qt.WaitCursor):
            self.setDisabled(True)
            try:
                if validator.run(edited_command) != ilivalidator.Validator.SUCCESS:
                    self.setDisabled(False)
            except JavaNotFoundError:
                self.setDisabled(False)
            print(f"Result here {self.configuration.xtflog}")

        return True
