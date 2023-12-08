"""
/***************************************************************************
                              -------------------
        begin                : 17.11.2023
        git sha              : :%H$
        copyright            : (C) 2023 by Dave Signer
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


from qgis.PyQt.QtWidgets import QWidget

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode

WIDGET_UI = gui_utils.get_ui_class("set_sequence_panel.ui")


class SetSequencePanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.configuration = None
        self.pg_use_super_login.stateChanged.connect(self._set_superuser)

    def set_configuration(self, configuration):
        self.configuration = configuration
        self.pg_use_super_login.setVisible(self.configuration.tool & DbIliMode.pg)

    def _set_superuser(self, state):
        if self.configuration:
            self.configuration.db_use_super_login = state

    def load_sequence(self):
        db_connector = db_utils.get_db_connector(self.configuration)
        if db_connector:
            sequence_value = db_connector.get_ili2db_sequence_value()
            self.sequence_value_edit.setValue(sequence_value)

    def save_sequence(self):
        db_connector = db_utils.get_db_connector(self.configuration)
        if self.sequence_group.isChecked():
            if db_connector:
                return db_connector.set_ili2db_sequence_value(
                    self.sequence_value_edit.value()
                )
            return False, self.tr("Could not reset T_Id - no db_connector...")
        else:
            return True, self.tr("T_Id not set.")
