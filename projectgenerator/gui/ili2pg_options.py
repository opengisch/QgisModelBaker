# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 03/04/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo
        email                : gcarrillo@linuxmail.org
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
from qgis.PyQt.QtCore import QSettings
from ..utils import get_ui_class

DIALOG_UI = get_ui_class('ili2pg_options.ui')


class Ili2pgOptionsDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)

        self.restore_configuration()

    def accepted(self):
        """ Save settings before accepting the dialog """
        self.save_configuration()
        self.done(1)

    def get_inheritance_type(self):
        if self.smart1_radio_button.isChecked():
            return 'smart1'
        else:
            return 'smart2'

    def save_configuration(self):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2pg/inheritance', self.get_inheritance_type())

    def restore_configuration(self):
        settings = QSettings()
        inheritance = settings.value('QgsProjectGenerator/ili2pg/inheritance', 'smart2')
        if inheritance == 'smart1':
            self.smart1_radio_button.setChecked(True)
        else:
            self.smart2_radio_button.setChecked(True)

