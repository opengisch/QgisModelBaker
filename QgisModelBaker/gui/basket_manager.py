"""
/***************************************************************************
                              -------------------
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

from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from QgisModelBaker.gui.panel.basket_panel import BasketPanel
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("basket_manager.ui")


class BasketManagerDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None, db_connector=None, datasetname=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.datasetname = datasetname
        self.db_connector = db_connector

        self.buttonBox.accepted.connect(self._accepted)
        self.buttonBox.rejected.connect(self._rejected)

        # baskets part
        self.baskets_panel = BasketPanel(self)
        self.baskets_layout.addWidget(self.baskets_panel)

        self.baskets_panel.load_basket_config(self.db_connector, self.datasetname)

    def _accepted(self):
        feedbacks = self.baskets_panel.save_basket_config(
            self.db_connector, self.datasetname
        )
        negative_feedbacks = [
            feedback for feedback in feedbacks if feedback[0] is False
        ]
        if negative_feedbacks:
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Critical)
            warning_title = self.tr("Creating baskets failed")
            warning_box.setWindowTitle(warning_title)
            warning_box.setText(
                "{}{}".format(
                    "\n".join([feedback[1] for feedback in negative_feedbacks]),
                    "\n(The problem is often an incorrectly formatted BID)",
                )
            )
            warning_box.exec_()
        self.close()

    def _rejected(self):
        self.close()
