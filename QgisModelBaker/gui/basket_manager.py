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

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from QgisModelBaker.gui.create_baskets import CreateBasketDialog
from QgisModelBaker.gui.panel.summary_basket_panel import SummaryBasketPanel
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("basket_manager.ui")


class BasketManagerDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None, db_connector=None, datasetname=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.datasetname = datasetname
        self.db_connector = db_connector

        # self.buttonBox.accepted.connect(self._accepted)
        # self.buttonBox.rejected.connect(self._rejected)

        # baskets part
        self.baskets_panel = SummaryBasketPanel(self)
        self.baskets_layout.addWidget(self.baskets_panel)

        self.baskets_panel.load_basket_config(self.db_connector, self.datasetname)

        self.add_button.clicked.connect(self._add_basket)
        self.edit_button.clicked.connect(self._edit_basket)
        self.delete_button.clicked.connect(self._delete_basket)

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.edit_button.setIcon(QgsApplication.getThemeIcon("/symbologyEdit.svg"))
        self.delete_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

    def _valid_selection(self):
        """
        Returns if at least one dataset is selected
        """
        return bool(self.baskets_panel.basket_view.selectedIndexes())

    def _add_basket(self):
        create_basket_dialog = CreateBasketDialog(
            self, self.db_connector, self.datasetname
        )
        create_basket_dialog.exec_()
        self.baskets_panel.bid_model.load_basket_config(
            self.db_connector, self.datasetname
        )

    def _edit_basket(self):
        if self._valid_selection():
            print("EDIT! (TODO)")

    def _delete_basket(self):
        if self._valid_selection():
            if (
                QMessageBox.warning(
                    self,
                    self.tr("Delete basket"),
                    self.tr(
                        "Deleting a Basket will also delete all the data it contains. This operation cannot be reverted.\n\nAre you sure you want to proceed?"
                    ),
                    QMessageBox.No | QMessageBox.Yes,
                )
                == QMessageBox.Yes
            ):
                print("DELETED! (TODO)")

    # def _accepted(self):
    #     feedbacks = self.baskets_panel.save_basket_config(
    #         self.db_connector, self.datasetname
    #     )
    #     negative_feedbacks = [
    #         feedback for feedback in feedbacks if feedback[0] is False
    #     ]
    #     if negative_feedbacks:
    #         warning_box = QMessageBox(self)
    #         warning_box.setIcon(QMessageBox.Critical)
    #         warning_title = self.tr("Creating baskets failed")
    #         warning_box.setWindowTitle(warning_title)
    #         warning_box.setText(
    #             "{}{}".format(
    #                 "\n".join([feedback[1] for feedback in negative_feedbacks]),
    #                 "\n(The problem is often an incorrectly formatted BID)",
    #             )
    #         )
    #         warning_box.exec_()
    #     self.close()
