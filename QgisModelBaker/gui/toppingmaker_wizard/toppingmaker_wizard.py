# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-08-01
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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
from qgis.PyQt.QtWidgets import QDialog, QSplitter, QVBoxLayout, QWizard

from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.toppingmaker_wizard.generation_page import GenerationPage
from QgisModelBaker.gui.toppingmaker_wizard.ili2dbsettings_page import (
    Ili2dbSettingsPage,
)
from QgisModelBaker.gui.toppingmaker_wizard.layers_page import LayersPage
from QgisModelBaker.gui.toppingmaker_wizard.models_page import ModelsPage
from QgisModelBaker.gui.toppingmaker_wizard.referencedata_page import ReferencedataPage
from QgisModelBaker.gui.toppingmaker_wizard.target_page import TargetPage
from QgisModelBaker.utils.gui_utils import ToppingMakerPageIds


class ToppingMakerWizard(QWizard):
    def __init__(self, iface, base_config, parent):
        QWizard.__init__(self, parent)

        self.setWindowTitle(
            self.tr("QGIS Model Baker UsabILIty Hub Topping Maker Wizard")
        )
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoCancelButtonOnLastPage)

        self.current_id = 0

        self.iface = iface
        self.log_panel = parent.log_panel

        # pages setup
        self.target_page = TargetPage(
            self, self._current_page_title(ToppingMakerPageIds.Target)
        )
        self.models_page = ModelsPage(
            self, self._current_page_title(ToppingMakerPageIds.Models)
        )
        self.layers_page = LayersPage(
            self, self._current_page_title(ToppingMakerPageIds.Layers)
        )
        self.referencedata_page = ReferencedataPage(
            self, self._current_page_title(ToppingMakerPageIds.ReferenceData)
        )
        self.ili2dbsettings_page = Ili2dbSettingsPage(
            self, self._current_page_title(ToppingMakerPageIds.Ili2dbSettings)
        )
        self.generation_page = GenerationPage(
            self, self._current_page_title(ToppingMakerPageIds.Generation)
        )

        self.setPage(ToppingMakerPageIds.Target, self.target_page)
        self.setPage(ToppingMakerPageIds.Models, self.models_page)
        self.setPage(ToppingMakerPageIds.Layers, self.layers_page)
        self.setPage(ToppingMakerPageIds.ReferenceData, self.referencedata_page)
        self.setPage(ToppingMakerPageIds.Ili2dbSettings, self.ili2dbsettings_page)
        self.setPage(ToppingMakerPageIds.Generation, self.generation_page)

        self.currentIdChanged.connect(self.id_changed)

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}")
        )

    def _current_page_title(self, id):
        if id == ToppingMakerPageIds.Target:
            return self.tr("Target Folder Selection")
        elif id == ToppingMakerPageIds.Models:
            return self.tr("Model Selection")
        elif id == ToppingMakerPageIds.Layers:
            return self.tr("Layer Configuration")
        elif id == ToppingMakerPageIds.ReferenceData:
            return self.tr("Reference Data Selection")
        elif id == ToppingMakerPageIds.Ili2dbSettings:
            return self.tr("Schema with ili2db Settings Selection")
        elif id == ToppingMakerPageIds.Generation:
            return self.tr("Make the Topping")
        else:
            return self.tr("Model Baker - Workflow Wizard")


class ToppingMakerWizardDialog(QDialog):
    def __init__(self, iface, base_config, parent):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.base_config = base_config

        self.setWindowTitle(self.tr("Model Baker - UsabILIty Hub Topping Maker Wizard"))
        self.log_panel = LogPanel()
        self.toppingmaker_wizard = ToppingMakerWizard(
            self.iface, self.base_config, self
        )
        self.toppingmaker_wizard.setStartId(ToppingMakerPageIds.Target)
        self.toppingmaker_wizard.setWindowFlags(Qt.Widget)
        self.toppingmaker_wizard.setFixedHeight(self.fontMetrics().lineSpacing() * 48)
        self.toppingmaker_wizard.setMinimumWidth(self.fontMetrics().lineSpacing() * 48)
        self.toppingmaker_wizard.show()

        self.toppingmaker_wizard.finished.connect(self.done)
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.toppingmaker_wizard)
        splitter.addWidget(self.log_panel)
        layout.addWidget(splitter)
        self.setLayout(layout)
