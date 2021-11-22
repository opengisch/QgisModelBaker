# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 22.11.2021
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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools

from ...utils import ui

WIDGET_UI = ui.get_ui_class("filter_data_panel.ui")


# could be renamed since it's not only model - it's dataset and basket as well
class FilterDataPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.select_all_checkbox.stateChanged.connect(self._select_all_items)
        self.filter_combobox.currentIndexChanged.connect(self._filter_changed)

    def setup_dialog(self, basket_handling):
        if self.parent:
            # disconnect currentIndexChanged signal while refreshing the combobox
            try:
                self.filter_combobox.currentIndexChanged.disconnect()
            except Exception:
                pass

            self._refresh_filter_combobox(basket_handling)

            self.filter_combobox.currentIndexChanged.connect(self._filter_changed)

        if self.parent.current_filter_mode == wizard_tools.ExportFilterMode.NO_FILTER:
            self.items_view.setHidden(True)
            self.select_all_checkbox.setHidden(True)

    def _refresh_filter_combobox(self, basket_handling):
        stored_index = self.filter_combobox.findData(self.parent.current_filter_mode)
        self.filter_combobox.clear()
        self.filter_combobox.addItem(
            self.tr("No filter (all models)"),
            wizard_tools.ExportFilterMode.NO_FILTER,
        )
        self.filter_combobox.addItem(
            self.tr("Models"), wizard_tools.ExportFilterMode.MODEL
        )
        if basket_handling:
            self.filter_combobox.addItem(
                self.tr("Datasets"), wizard_tools.ExportFilterMode.DATASET
            )
            self.filter_combobox.addItem(
                self.tr("Baskets"), wizard_tools.ExportFilterMode.BASKET
            )
        if self.filter_combobox.itemData(stored_index):
            self.filter_combobox.setCurrentIndex(stored_index)
            if (
                self.filter_combobox.itemData(stored_index)
                != wizard_tools.ExportFilterMode.NO_FILTER
            ):
                self._set_select_all_checkbox()
        else:
            self.filter_combobox.setCurrentIndex(0)
            self._filter_changed()

    def _set_export_filter_view_model(self, model):
        try:
            self.items_view.clicked.disconnect()
            self.items_view.space_pressed.disconnect()
            self.items_view.model().dataChanged.disconnect()
        except Exception:
            pass

        self.items_view.setModel(model)
        self.items_view.clicked.connect(self.items_view.model().check)
        self.items_view.space_pressed.connect(self.items_view.model().check)
        self.items_view.model().dataChanged.connect(
            lambda: self._set_select_all_checkbox()
        )

    def _filter_changed(self):
        filter = self.filter_combobox.currentData()
        if filter == wizard_tools.ExportFilterMode.NO_FILTER:
            self.items_view.setHidden(True)
            self.select_all_checkbox.setHidden(True)
        else:
            self.items_view.setVisible(True)
            self.select_all_checkbox.setVisible(True)
            if filter == wizard_tools.ExportFilterMode.MODEL:
                self._set_export_filter_view_model(self.parent.current_models_model)
                self.select_all_checkbox.setText(self.tr("Select all models"))
            if filter == wizard_tools.ExportFilterMode.DATASET:
                self._set_export_filter_view_model(self.parent.current_datasets_model)
                self.select_all_checkbox.setText(self.tr("Select all datasets"))
            if filter == wizard_tools.ExportFilterMode.BASKET:
                self._set_export_filter_view_model(self.parent.current_baskets_model)
                self.select_all_checkbox.setText(self.tr("Select all baskets"))
            self._set_select_all_checkbox()
        self.parent.current_filter_mode = filter

    def _select_all_items(self, state):
        if state != Qt.PartiallyChecked and state != self._evaluated_check_state(
            self.items_view.model()
        ):
            self.items_view.model().check_all(state)

    def _set_select_all_checkbox(self):
        self.select_all_checkbox.setCheckState(
            self._evaluated_check_state(self.items_view.model())
        )

    def _evaluated_check_state(self, model):
        nbr_of_checked = len(model.checked_entries())
        if nbr_of_checked:
            if nbr_of_checked == model.rowCount():
                return Qt.Checked
            return Qt.PartiallyChecked
        return Qt.Unchecked
