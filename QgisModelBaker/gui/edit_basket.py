"""
/***************************************************************************
                              -------------------
        begin                : 20.09.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german at opengis ch
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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QWidget

from QgisModelBaker.libs.modelbaker.dbconnector.db_connector import DBConnector
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("edit_basket.ui")


class EditBasketDialog(QDialog, DIALOG_UI):
    def __init__(
        self, parent: QWidget, db_connector: DBConnector, basket_configuration: dict
    ) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.db_connector = db_connector

        self.buttonBox.accepted.connect(self._accept)

        self._basket_info = basket_configuration
        self.txtTopic.setText(self._basket_info["topic"])
        self.txtBidOidType.setText(self._basket_info["bid_domain"])
        self.txtBidValue.setText(self._basket_info["bid_value"])
        self.txtAttachmentKey.setText(self._basket_info["attachment_key"])

        # Fill filtered datasets
        for t_id, dataset_data in self._get_filtered_datasets().items():
            self.cboDatasets.addItem(dataset_data["datasetname"], t_id)

            if not dataset_data["enabled"]:
                model = self.cboDatasets.model()
                item = model.item(self.cboDatasets.count() - 1)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # Disable mirror item

        # Select the current basket's dataset
        self.cboDatasets.setCurrentIndex(
            self.cboDatasets.findData(self._basket_info["dataset_t_id"])
        )

    def _get_filtered_datasets(self) -> dict:
        # Returns datasets info, marking as disabled those that
        # already have a basket for the editing basket's topic.
        filtered_datasets = {}  # {dataset_id1: {'datasetname': name, 'enabled': True}}

        # Obtain DB datasets
        for record in self.db_connector.get_datasets_info():
            filtered_datasets[record["t_id"]] = {
                "datasetname": record["datasetname"],
                "enabled": True,
            }

        # Obtain DB baskets info
        baskets = self.db_connector.get_baskets_info()

        # Filter baskets belonging to the editing basket's topic.
        # Exclude the dataset of the basket being edited (it should
        # be enabled to allow selection in the comboBox).
        for basket in baskets:
            if (
                basket["topic"] == self._basket_info["topic"]
                and basket["basket_t_id"] != self._basket_info["basket_t_id"]
            ):
                # Mark their corresponding datasets as disabled
                filtered_datasets[basket["dataset_t_id"]]["enabled"] = False

        return filtered_datasets

    def _accept(self):
        self._save_edited_basket()
        self.close()

    def _save_edited_basket(self):
        # Save basket attributes
        return
