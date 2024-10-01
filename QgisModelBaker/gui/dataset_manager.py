"""
/***************************************************************************
        begin                : 10.08.2021
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

from qgis.core import Qgis, QgsApplication, QgsMapLayer, QgsMessageLog, QgsProject
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHeaderView,
    QMessageBox,
    QSizePolicy,
    QTableView,
)

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.basket_manager import BasketManagerDialog
from QgisModelBaker.gui.edit_dataset_name import EditDatasetDialog
from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.ili2db_utils import Ili2DbUtils
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import DatasetModel

DIALOG_UI = gui_utils.get_ui_class("dataset_manager.ui")


class DatasetManagerDialog(QDialog, DIALOG_UI):
    def __init__(self, iface, parent=None, wizard_embedded=False):

        QDialog.__init__(self, parent)
        self.iface = iface
        self.embedded = wizard_embedded
        self._close_editing()

        self.setupUi(self)
        self.buttonBox.accepted.connect(self._accepted)
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.info_layout.addWidget(self.bar, 0, Qt.AlignTop)

        self.db_simple_factory = DbSimpleFactory()

        self.dataset_model = DatasetModel()
        self.dataset_tableview.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.dataset_tableview.horizontalHeader().hide()
        self.dataset_tableview.verticalHeader().hide()
        self.dataset_tableview.setSelectionMode(QTableView.SingleSelection)
        self.dataset_tableview.setModel(self.dataset_model)

        self.add_button.clicked.connect(self._add_dataset)
        self.edit_button.clicked.connect(self._edit_dataset)
        self.delete_button.clicked.connect(self._delete_dataset)
        self.dataset_tableview.selectionModel().selectionChanged.connect(
            lambda: self._enable_dataset_handling(True)
        )

        if self.embedded:
            # While performing an Import Data operation,
            # baskets should not be shown, since the operation
            # will create a new basket for the chosen dataset.
            self.basket_manager_button.setVisible(False)
        else:
            self.basket_manager_button.clicked.connect(self._open_basket_manager)

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.edit_button.setIcon(QgsApplication.getThemeIcon("/symbologyEdit.svg"))
        self.delete_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

        self.configuration = self._evaluated_configuration()
        self._refresh_datasets()

    def _close_editing(self):
        editable_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.iface.vectorLayerTools().stopEditing(layer)
                if layer.isEditable():
                    editable_layers.append(layer)
        if editable_layers:
            # in case it could not close it automatically
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Warning)
            warning_title = self.tr("Layers still editable")
            warning_box.setWindowTitle(warning_title)
            warning_box.setText(
                self.tr(
                    "You still have layers in edit mode.\nIn case you modify datasets on the database of those layers, it could lead to database locks.\nEditable layers are:\n - {}"
                ).format("\n - ".join([layer.name() for layer in editable_layers]))
            )
            warning_box.exec_()

    def _valid_selection(self):
        """
        Returns if at least one dataset is selected
        """
        return bool(self.dataset_tableview.selectedIndexes())

    def _enable_dataset_handling(self, enable):
        self.dataset_tableview.setEnabled(enable)
        self.add_button.setEnabled(enable)
        self.edit_button.setEnabled(self._valid_selection())
        self.delete_button.setEnabled(self._valid_selection())
        self.basket_manager_button.setEnabled(self._valid_selection())

    def _refresh_datasets(self):
        db_connector = db_utils.get_db_connector(self.configuration)
        if db_connector and db_connector.get_basket_handling():
            self._enable_dataset_handling(True)
            return self.dataset_model.refresh_model(db_connector)
        else:
            self._enable_dataset_handling(False)
            self.bar.pushWarning(
                self.tr("Warning"),
                self.tr(
                    "This source does not support datasets and baskets (recreate it with basket columns)."
                ),
            )
            return self.dataset_model.clear()

    def _add_dataset(self):
        db_connector = db_utils.get_db_connector(self.configuration)
        if db_connector and db_connector.get_basket_handling():
            edit_dataset_dialog = EditDatasetDialog(self, db_connector)
            edit_dataset_dialog.exec_()
            self._refresh_datasets()
            self._jump_to_entry(edit_dataset_dialog.dataset_line_edit.text())

    def _edit_dataset(self):
        if self._valid_selection():
            db_connector = db_utils.get_db_connector(self.configuration)
            if db_connector and db_connector.get_basket_handling():
                dataset = (
                    self.dataset_tableview.selectedIndexes()[0].data(
                        int(DatasetModel.Roles.TID)
                    ),
                    self.dataset_tableview.selectedIndexes()[0].data(
                        int(DatasetModel.Roles.DATASETNAME)
                    ),
                )
                edit_dataset_dialog = EditDatasetDialog(self, db_connector, dataset)
                edit_dataset_dialog.exec_()
                self._refresh_datasets()
                self._jump_to_entry(edit_dataset_dialog.dataset_line_edit.text())

    def _delete_dataset(self):
        if self._valid_selection():
            db_connector = db_utils.get_db_connector(self.configuration)
            if not db_connector.get_basket_handling():
                QMessageBox.warning(
                    self,
                    self.tr("Delete Dataset"),
                    self.tr(
                        "Delete datasets is only available for database schemas created with --createBasketCol parameter."
                    ),
                    QMessageBox.Close,
                )
                return

            if (
                QMessageBox.warning(
                    self,
                    self.tr("Delete Dataset"),
                    self.tr(
                        "Deleting a Dataset will also delete children baskets and all the data they contain. This operation cannot be reverted.\n\nAre you sure you want to proceed?"
                    ),
                    QMessageBox.No | QMessageBox.Yes,
                )
                == QMessageBox.Yes
            ):
                dataset = self.dataset_tableview.selectedIndexes()[0].data(
                    int(DatasetModel.Roles.DATASETNAME)
                )
                ili2db_utils = Ili2DbUtils()
                ili2db_utils.log_on_error.connect(self._log_on_delete_dataset_error)
                res, msg = ili2db_utils.delete_dataset(dataset, self.configuration)
                if res:
                    # After deletion, make sure canvas is refreshed
                    self._refresh_map_layers()

                    # Refresh dataset table view
                    self._refresh_datasets()

                warning_box = QMessageBox(self)
                warning_box.setIcon(
                    QMessageBox.Information if res else QMessageBox.Warning
                )
                warning_box.setWindowTitle(self.tr("Delete Dataset"))
                warning_box.setText(msg)
                warning_box.exec_()

    def _log_on_delete_dataset_error(self, log):
        QgsMessageLog.logMessage(log, self.tr("Delete dataset from DB"), Qgis.Critical)

    def _refresh_map_layers(self):
        # Refresh layer data sources and also their symbology (including feature count)
        layer_tree_view = self.iface.layerTreeView()
        for tree_layer in QgsProject.instance().layerTreeRoot().findLayers():
            layer = tree_layer.layer()
            layer.dataProvider().reloadData()
            layer_tree_view.refreshLayerSymbology(layer.id())

    def _open_basket_manager(self):
        if self._valid_selection():
            db_connector = db_utils.get_db_connector(self.configuration)
            if db_connector and db_connector.get_basket_handling():
                datasetname = self.dataset_tableview.selectedIndexes()[0].data(
                    int(DatasetModel.Roles.DATASETNAME)
                )
                basket_manager_dialog = BasketManagerDialog(
                    self.iface, self, db_connector, datasetname, self.configuration
                )
                basket_manager_dialog.exec_()

    def _jump_to_entry(self, datasetname):
        matches = self.dataset_model.match(
            self.dataset_model.index(0, 0),
            Qt.DisplayRole,
            datasetname,
            1,
            Qt.MatchExactly,
        )
        if matches:
            self.dataset_tableview.setCurrentIndex(matches[0])
            self.dataset_tableview.scrollTo(matches[0])

    def _evaluated_configuration(self):
        configuration = Ili2DbCommandConfiguration()

        if self.embedded:
            # when embedded, just use the current configuration
            configuration = self._restored_configuration()
        else:
            valid = False
            mode = None

            layer = self._relevant_layer()
            if layer:
                source_provider = layer.dataProvider()
                valid, mode = db_utils.get_configuration_from_sourceprovider(
                    source_provider, configuration
                )
                configuration.tool = mode
                source_info_text = self.tr(
                    "<body><p>It's the datasource of the current project, evaluated by layer <b>{}</b>.</p>"
                ).format(layer.name())

            # when no valid configuration has been read from layer(s), take the last stored
            if not valid or not mode:
                configuration = self._restored_configuration()
                source_info_text = self.tr(
                    "<p>It's the last time used datasource, since no valid layer in the current project (probably empty project).</p>"
                )

            if configuration.tool == DbIliMode.gpkg:
                self.info_label.setText(
                    self.tr(
                        """<html><head/><body><p><b>Modify datasets and baskets in the GeoPackage databasefile <span style=" font-family:'monospace'; color:'#9BCADE';">{}</span></b></p>{}</body></html>"""
                    ).format(configuration.dbfile, source_info_text)
                )
            elif (
                configuration.tool == DbIliMode.pg
                or configuration.tool == DbIliMode.mssql
            ):
                self.info_label.setText(
                    self.tr(
                        """<html><head/><body><p><b>Modify datasets and baskets in the schema <span style=" font-family:'monospace'; color:'#9BCADE';">{}</span> at the PostgreSQL database <span style=" font-family:'monospace'; color:'#9BCADE';">{}</span></b></p>{}</body></html>"""
                    ).format(
                        configuration.dbschema, configuration.database, source_info_text
                    )
                )
            else:
                self.info_label.setText(
                    self.tr(
                        """<html><head/><body><p><b>No valid datasource found. Open or create an INTERLIS based QGIS project first.</b></p></body></html>"""
                    )
                )

        return configuration

    def _relevant_layer(self):
        layer = None

        for layer in [self.iface.activeLayer()] + list(
            QgsProject.instance().mapLayers().values()
        ):
            if layer and layer.dataProvider() and layer.dataProvider().isValid():
                return layer

    def _restored_configuration(self):
        settings = QSettings()
        configuration = Ili2DbCommandConfiguration()
        for db_id in self.db_simple_factory.get_db_list(False):
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()

        mode = settings.value("QgisModelBaker/importtype")
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili
        configuration.tool = mode
        return configuration

    def _save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue("QgisModelBaker/importtype", configuration.tool.name)
        mode = configuration.tool
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()

    def _accepted(self):
        self._save_configuration(self.configuration)
        self.close()
