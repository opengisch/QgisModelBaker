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
from qgis.core import QgsCoordinateReferenceSystem
from qgis.gui import QgsProjectionSelectionDialog
from ..utils import get_ui_class

DIALOG_UI = get_ui_class('ili2pg_options.ui')


class Ili2pgOptionsDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.crs = 21781
        self.crs_selection_button.clicked.connect(self.select_crs)
        self.inheritance = 'smart1'

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)

        self.restore_configuration()

    def accepted(self):
        """ Save settings before accepting the dialog """
        self.save_configuration()
        self.done(1)

    def select_crs(self):
        """ Open a dialog to select CRS """
        crsSelector = QgsProjectionSelectionDialog(self)
        crsSelector.setCrs(QgsCoordinateReferenceSystem(self.crs, type=QgsCoordinateReferenceSystem.PostgisCrsId))
        res = crsSelector.exec()
        if res:
            self.crs = int(crsSelector.crs().authid().split(':')[1])
            self.set_crs_label()

    def set_crs_label(self):
        """ Update EPSG label and tooltip """
        self.crs_label.setText('EPSG {}'.format(self.crs))
        self.crs_label.setToolTip(QgsCoordinateReferenceSystem(self.crs, type=QgsCoordinateReferenceSystem.PostgisCrsId).description())

    def get_inheritance_type(self):
        if self.no_smart_radio_button.isChecked():
            return 'noSmart'
        elif self.smart1_radio_button.isChecked():
            return 'smart1'
        else:
            return 'smart2'

    def save_configuration(self):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2pg/epsg', self.crs)
        settings.setValue('QgsProjectGenerator/ili2pg/createEnumColAsItfCode', self.enum_col_as_itf_code.isChecked())
        settings.setValue('QgsProjectGenerator/ili2pg/nameByTopic', self.name_by_topic.isChecked())
        settings.setValue('QgsProjectGenerator/ili2pg/importTid', self.import_tid.isChecked())
        settings.setValue('QgsProjectGenerator/ili2pg/coalesceMultiSurface', self.coalesce_multi_surface.isChecked())
        settings.setValue('QgsProjectGenerator/ili2pg/inheritance', self.get_inheritance_type())

    def restore_configuration(self):
        settings = QSettings()

        self.crs = settings.value('QgsProjectGenerator/ili2pg/epsg', 21781)
        self.set_crs_label()
        self.enum_col_as_itf_code.setChecked(settings.value('QgsProjectGenerator/ili2pg/createEnumColAsItfCode', True))
        self.name_by_topic.setChecked(settings.value('QgsProjectGenerator/ili2pg/nameByTopic', True))
        self.import_tid.setChecked(settings.value('QgsProjectGenerator/ili2pg/importTid', True))
        self.coalesce_multi_surface.setChecked(settings.value('QgsProjectGenerator/ili2pg/coalesceMultiSurface', True))
        inheritance = settings.value('QgsProjectGenerator/ili2pg/inheritance', 'smart1')
        if inheritance == 'noSmart':
            self.no_smart_radio_button.setChecked(True)
        elif inheritance == 'smart1':
            self.smart1_radio_button.setChecked(True)
        else:
            self.smart2_radio_button.setChecked(True)

