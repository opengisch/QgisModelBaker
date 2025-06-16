"""
/***************************************************************************
                              -------------------
        begin                : 26.08.2024
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

from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsProject
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from QgisModelBaker.gui.create_baskets import CreateBasketDialog
from QgisModelBaker.gui.edit_basket import EditBasketDialog
from QgisModelBaker.gui.panel.summary_basket_panel import SummaryBasketPanel
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.ili2db_utils import Ili2DbUtils
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("basket_manager.ui")


class BasketManagerDialog(QDialog, DIALOG_UI):
    def __init__(
        self,
        iface,
        parent=None,
        db_connector=None,
        datasetname=None,
        configuration: Ili2DbCommandConfiguration = None,
    ):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.iface = iface
        self.datasetname = datasetname
        self.db_connector = db_connector
        self.configuration = configuration

        self.buttonBox.accepted.connect(self.accept)

        # baskets part
        self.baskets_panel = SummaryBasketPanel(self)
        self.baskets_layout.addWidget(self.baskets_panel)
        self.baskets_panel.basket_view.doubleClicked.connect(self._edit_basket)

        self.baskets_panel.load_basket_config(self.db_connector, self.datasetname)

        self.add_button.clicked.connect(self._add_basket)
        self.edit_button.clicked.connect(self._edit_basket)
        self.delete_button.clicked.connect(self._delete_basket)
        self.baskets_panel.basket_view.selectionModel().selectionChanged.connect(
            lambda: self._enable_basket_handling(True)
        )

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.edit_button.setIcon(QgsApplication.getThemeIcon("/symbologyEdit.svg"))
        self.delete_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

        self._enable_basket_handling(True)  # Initial widget status

    def _enable_basket_handling(self, enable):
        self.add_button.setEnabled(enable)
        self.edit_button.setEnabled(self._valid_selection())
        self.delete_button.setEnabled(self._valid_selection())

    def _valid_selection(self):
        """
        Returns if at least one dataset is selected
        """
        return bool(self.baskets_panel.basket_view.selectedIndexes())

    def _refresh_baskets(self):
        self.baskets_panel.bid_model.load_basket_config(
            self.db_connector, self.datasetname
        )
        self._enable_basket_handling(True)

    def _add_basket(self):
        create_basket_dialog = CreateBasketDialog(
            self, self.db_connector, self.datasetname
        )
        if create_basket_dialog.baskets_can_be_created():
            create_basket_dialog.exec()

            # Refresh existing baskets in basket manager after creation
            self._refresh_baskets()
        else:
            QMessageBox.information(
                self,
                self.tr("Create Baskets"),
                self.tr(
                    f"The dataset '{self.datasetname}' already contains one basket for each topic.\n\n"
                    f"No additional baskets can be created."
                ),
                QMessageBox.StandardButton.Close,
            )

    def _edit_basket(self) -> None:
        if self._valid_selection():
            selected_basket_settings = self.baskets_panel.selected_basket_settings()
            edit_basket_dialog = EditBasketDialog(
                self, self.db_connector, selected_basket_settings
            )
            edit_basket_dialog.exec()

            # Refresh existing baskets in basket manager after edition
            self._refresh_baskets()

    def _delete_basket(self) -> None:
        if self._valid_selection():
            if not self.db_connector.get_basket_handling():
                QMessageBox.warning(
                    self,
                    self.tr("Delete Basket"),
                    self.tr(
                        "Delete baskets is only available for database schemas created with --createBasketCol parameter."
                    ),
                    QMessageBox.StandardButton.Close,
                )
                return

            if (
                QMessageBox.warning(
                    self,
                    self.tr("Delete Basket"),
                    self.tr(
                        "Deleting a Basket will also delete all the data it contains. This operation cannot be reverted.\n\nAre you sure you want to proceed?"
                    ),
                    QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
                )
                == QMessageBox.StandardButton.Yes
            ):
                basket_config = self.baskets_panel.selected_basket_settings()
                res, msg = self._do_delete_basket(basket_config)

                if res:
                    # After deletion, make sure canvas is refreshed
                    self._refresh_map_layers()

                    # Refresh existing baskets in basket manager after deletion
                    self._refresh_baskets()

                warning_box = QMessageBox(self)
                warning_box.setIcon(
                    QMessageBox.Icon.Information if res else QMessageBox.Icon.Warning
                )
                warning_box.setWindowTitle(self.tr("Delete Basket"))
                warning_box.setText(msg)
                warning_box.exec()

    def _refresh_map_layers(self):
        # Refresh layer data sources and also their symbology (including feature count)
        layer_tree_view = self.iface.layerTreeView()
        for tree_layer in QgsProject.instance().layerTreeRoot().findLayers():
            layer = tree_layer.layer()
            layer.dataProvider().reloadData()
            layer_tree_view.refreshLayerSymbology(layer.id())

    def _do_delete_basket(self, basket_config):
        # Keep original values just in case we need to go back to them
        original_dataset_id = basket_config["dataset_t_id"]
        original_dataset_name = basket_config["datasetname"]

        # Create temporary dataset
        tmp_dataset_id, tmp_dataset_name = "", "_tmp_dataset_tmp_"
        res, msg = self.db_connector.create_dataset(tmp_dataset_name)
        for _dataset in self.db_connector.get_datasets_info():
            if _dataset["datasetname"] == tmp_dataset_name:
                tmp_dataset_id = _dataset["t_id"]
                break

        if tmp_dataset_id == "":
            return False, self.tr(
                "Delete basket failed! Internal error modifying dataset/basket tables."
            )

        # Move basket to temporary dataset
        basket_config["dataset_t_id"] = tmp_dataset_id
        basket_config["datasetname"] = tmp_dataset_name

        res, msg = self.db_connector.edit_basket(basket_config)
        if not res:
            return False, self.tr(
                "Delete basket failed! Internal error modifying basket."
            )

        # Remove temporary dataset
        ili2db_utils = Ili2DbUtils()
        ili2db_utils.log_on_error.connect(self._log_on_delete_dataset_error)
        res, msg = ili2db_utils.delete_dataset(tmp_dataset_name, self.configuration)

        # If anything went bad, leave everything as the original status,
        # i.e., move the basket to its original dataset
        if not res:
            msg = self.tr(
                "Delete basket failed! Internal error deleting dataset/basket records."
            )
            basket_config["dataset_t_id"] = original_dataset_id
            basket_config["datasetname"] = original_dataset_name
            _res, _msg = self.db_connector.edit_basket(basket_config)
            if not _res:
                # We shouldn't reach this, the basket is in another dataset!
                msg = self.tr("The basket (t_id: {}) couldn't be deleted!").format(
                    basket_config["basket_t_id"]
                )
        else:
            msg = self.tr("Basket (t_id: {}) successfully deleted!").format(
                basket_config["basket_t_id"]
            )

        return res, msg

    def _log_on_delete_dataset_error(self, log):
        QgsMessageLog.logMessage(
            log, self.tr("Delete dataset from DB"), Qgis.MessageLevel.Critical
        )
