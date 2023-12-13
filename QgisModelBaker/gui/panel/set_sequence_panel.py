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
        self.last_loaded_sequence_value = None
        self.sequence_value_edit.setSpecialValueText("-")

    def set_configuration(self, configuration):
        self.configuration = configuration
        self.pg_use_super_login.setVisible(self.configuration.tool & DbIliMode.pg)

    def _set_superuser(self, state):
        if self.configuration:
            self.configuration.db_use_super_login = state

    def load_sequence(self):
        db_connector = db_utils.get_db_connector(self.configuration)
        if db_connector:
            self.last_loaded_sequence_value = (
                db_connector.get_ili2db_sequence_value() or 0
            )
        else:
            self.last_loaded_sequence_value = 0

        # not loaded is 0
        self.sequence_value_edit.setValue(self.last_loaded_sequence_value)
        if self.last_loaded_sequence_value == 0:
            return False, self.tr("Could not load T_Id. Maybe wrong credentials.")
        else:
            return True, self.tr("T_Id loaded.")

    def save_sequence(self):
        if (
            self.sequence_value_edit.value()
            != self.sequence_value_edit.minimum()  # what is used for "NULL"
            and self.sequence_value_edit.value() != self.last_loaded_sequence_value
        ):
            # only if it changed
            if self.sequence_group.isChecked():
                result, message = False, None
                db_connector = db_utils.get_db_connector(self.configuration)
                if db_connector:
                    result, message = db_connector.set_ili2db_sequence_value(
                        self.sequence_value_edit.value()
                    )
                if not result:
                    # reset value
                    if self.last_loaded_sequence_value is None:
                        self.sequence_value_edit.setValue(
                            self.sequence_value_edit.minimum()
                        )  # used for "NULL", what leads to displaying the special text value "-"
                    else:
                        self.sequence_value_edit.setValue(
                            self.last_loaded_sequence_value
                        )
                    return False, message or self.tr(
                        "Could not set T_Id. No connection to data source. Maybe wrong credentials."
                    )
                else:
                    return True, self.tr("T_Id changed.")
        return True, self.tr("T_Id not changed.")
