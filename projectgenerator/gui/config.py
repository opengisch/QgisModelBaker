# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 29/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

from projectgenerator.utils import get_ui_class
from projectgenerator.utils import qt_utils
from qgis.PyQt.QtWidgets import QDialog

DIALOG_UI = get_ui_class('config.ui')

class ConfigDialog(QDialog, DIALOG_UI):
    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        qt_utils.make_file_selector(self.java_path, self.tr('Select java application.'), self.tr('java (*)'))
        self.buttonBox.accepted.connect(self.accepted)

    def accepted(self):
        self.configuration.java_path = self.java_path.text()