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
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsDataSourceUri,
    QgsMapLayer,
    QgsProject,
)
from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils import db_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/ili2dbsettings.ui")


class Ili2dbSettingsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.setTitle(title)

        self.type_combo_box.currentIndexChanged.connect(self._schema_changed)
        # load into a model all the schema names from the layer and the layersource
        # on next or wherever get teh configuration from layersource utils.get_configuration_from_layersource
        # to set the config in toppingmaker

        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog(self)
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        # self.crsSelector.crsChanged.connect(self._crs_changed)

    def initializePage(self) -> None:
        print("now at settings.")
        # - [ ] Ist das der Ort Models etc zu laden? Diese Funktion wird aufgerufen, jedes mal wenn mit "next" auf die Seite kommt.
        self._refresh_combobox()
        return super().initializePage()

    def _refresh_combobox(self):
        """
        Check all the vector layers if the variable "interlis_topic" is set and
        """
        self.schema_combobox.clear()
        self.schema_combobox.addItem(
            self.tr("Not loading ili2db settings from schema"), None
        )
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
                schema_identificator = (
                    db_utils.get_schema_identificator_from_layersource(
                        source_provider, source
                    )
                )
                if (
                    not schema_identificator
                    or self.schema_combobox.findText(schema_identificator) > -1
                ):
                    continue

                configuration = Ili2DbCommandConfiguration()
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, configuration
                )
                if valid and mode:
                    configuration.tool = mode
                    db_connector = db_utils.get_db_connector(configuration)
                    # only load it when it exists and metadata there (contains interlis data)
                    if (
                        db_connector.db_or_schema_exists()
                        or db_connector.metadata_exists()
                    ):
                        self.schema_combobox.addItem(schema_identificator, db_connector)

    def _schema_changed(self):
        db_connector = self.schema_combobox.currentData()
        if db_connector:
            self.toppingmaker_wizard.topping_maker.create_ili2dbsettings(db_connector)
        else:
            # clean it up or similar
            pass

    """
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
    def _set_crs_from_d(self, ili2db_metaconfig):
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
    """
