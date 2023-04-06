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

from qgis.PyQt.QtWidgets import QWidget

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

WIDGET_UI = gui_utils.get_ui_class("export_models_panel.ui")


# could be renamed since it's not only model - it's dataset and basket as well
class ExportModelsPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

    def setup_dialog(self, validation=False):
        self._generate_texts(validation)
        self.export_models_checkbox.setChecked(False)
        self.items_view.setVisible(False)
        if self.parent:
            self.items_view.setModel(self.parent.current_export_models_model)
            self.items_view.clicked.connect(self.items_view.model().check)
            self.items_view.space_pressed.connect(self.items_view.model().check)

            self.export_models_checkbox.setChecked(
                self.parent.current_export_models_active
            )
            self.export_models_checkbox.stateChanged.connect(self._active_state_changed)
            self._active_state_changed(self.parent.current_export_models_active)

    def _generate_texts(self, validation):
        self.export_models_checkbox.setText(
            self.tr(
                "{verb} the data in a model other than the one where it is stored"
            ).format(verb="Validate" if validation else "Export")
        )
        self.export_models_checkbox.setToolTip(
            self.tr(
                """
            <html><head/><body>
            <p>If your data is in the format of the cantonal model, but you want to {verb} it in the format of the national model.</p>
            <p>The data that cannot be {pastverb} in the selected model is {pastverb} in the model it is stored.</p>
            <p>Usually, this is one single model. However, it is also possible to pass multiple models, which makes sense if there are multiple base models in the schema you want to {verb}.</p>
            <p>This is the value passed to <span style=" font-family:'monospace';">--exportModels</span></p>
            </body></html>
            """
            ).format(
                verb="validate" if validation else "export",
                pastverb="validated" if validation else "exported",
            )
        )

    def _active_state_changed(self, checked):
        self.items_view.setVisible(checked)
        if not checked:
            # on uncheck disable all
            self.items_view.model().check_all([])
        self.parent.current_export_models_active = checked
