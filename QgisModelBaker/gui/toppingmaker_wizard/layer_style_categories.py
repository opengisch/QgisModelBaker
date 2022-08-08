# -*- coding: utf-8 -*-
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

from qgis.PyQt.QtWidgets import QDialog

from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("toppingmaker_wizard/layer_style_categories.ui")


class LayerStyleCategories(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
