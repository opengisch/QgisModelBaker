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


from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import QDialog, QSplitter, QVBoxLayout, QWizard

from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.topping_wizard.additives_page import AdditivesPage
from QgisModelBaker.gui.topping_wizard.generation_page import GenerationPage
from QgisModelBaker.gui.topping_wizard.ili2dbsettings_page import Ili2dbSettingsPage
from QgisModelBaker.gui.topping_wizard.layers_page import LayersPage
from QgisModelBaker.gui.topping_wizard.models_page import ModelsPage
from QgisModelBaker.gui.topping_wizard.referencedata_page import ReferencedataPage
from QgisModelBaker.gui.topping_wizard.target_page import TargetPage
from QgisModelBaker.libs.modelbaker.ilitoppingmaker import IliProjectTopping
from QgisModelBaker.utils.gui_utils import ToppingWizardPageIds


class ToppingWizard(QWizard):
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
        self.base_config = base_config

        self.topping = IliProjectTopping()
        self.topping.stdout.connect(self.log_panel.print_info)

        # pages setup
        self.target_page = TargetPage(
            self, self._current_page_title(ToppingWizardPageIds.Target)
        )
        self.models_page = ModelsPage(
            self, self._current_page_title(ToppingWizardPageIds.Models)
        )
        self.layers_page = LayersPage(
            self, self._current_page_title(ToppingWizardPageIds.Layers)
        )
        self.additives_page = AdditivesPage(
            self, self._current_page_title(ToppingWizardPageIds.Additives)
        )
        self.referencedata_page = ReferencedataPage(
            self, self._current_page_title(ToppingWizardPageIds.ReferenceData)
        )
        self.ili2dbsettings_page = Ili2dbSettingsPage(
            self, self._current_page_title(ToppingWizardPageIds.Ili2dbSettings)
        )
        self.generation_page = GenerationPage(
            self, self._current_page_title(ToppingWizardPageIds.Generation)
        )

        self.setPage(ToppingWizardPageIds.Target, self.target_page)
        self.setPage(ToppingWizardPageIds.Models, self.models_page)
        self.setPage(ToppingWizardPageIds.Layers, self.layers_page)
        self.setPage(ToppingWizardPageIds.Additives, self.additives_page)
        self.setPage(ToppingWizardPageIds.ReferenceData, self.referencedata_page)
        self.setPage(ToppingWizardPageIds.Ili2dbSettings, self.ili2dbsettings_page)
        self.setPage(ToppingWizardPageIds.Generation, self.generation_page)

        self.currentIdChanged.connect(self.id_changed)

    def sizeHint(self):
        return QSize(
            self.fontMetrics().lineSpacing() * 48, self.fontMetrics().lineSpacing() * 48
        )

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}")
        )

    def busy(self, page, busy, text="Busy..."):
        page.setEnabled(not busy)
        self.log_panel.busy_bar.setVisible(busy)
        if busy:
            self.log_panel.busy_bar.setFormat(text)
        else:
            self.log_panel.scrollbar.setValue(self.log_panel.scrollbar.maximum())

    def _current_page_title(self, id):
        if id == ToppingWizardPageIds.Target:
            return self.tr("Target Folder Selection")
        elif id == ToppingWizardPageIds.Models:
            return self.tr("Model and Source Selection")
        elif id == ToppingWizardPageIds.Layers:
            return self.tr("Layer Configuration")
        elif id == ToppingWizardPageIds.Additives:
            return self.tr("Additive Project Settings")
        elif id == ToppingWizardPageIds.ReferenceData:
            return self.tr("Reference Data Selection")
        elif id == ToppingWizardPageIds.Ili2dbSettings:
            return self.tr("Schema with ili2db Settings Selection")
        elif id == ToppingWizardPageIds.Generation:
            return self.tr("Make the Topping")
        else:
            return self.tr("Model Baker - Workflow Wizard")


class ToppingWizardDialog(QDialog):
    def __init__(self, iface, base_config, parent):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.base_config = base_config

        self.setWindowTitle(self.tr("Model Baker - UsabILIty Hub Topping Maker Wizard"))
        self.log_panel = LogPanel()
        self.topping_wizard = ToppingWizard(self.iface, self.base_config, self)
        self.topping_wizard.setStartId(ToppingWizardPageIds.Target)
        self.topping_wizard.setWindowFlags(Qt.Widget)
        self.topping_wizard.show()

        self.topping_wizard.finished.connect(self.done)
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.topping_wizard)
        splitter.addWidget(self.log_panel)
        layout.addWidget(splitter)
        self.setLayout(layout)
