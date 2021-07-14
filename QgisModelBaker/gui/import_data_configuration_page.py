# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 06.07.2021
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

import os
import pathlib
import configparser

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.ilicache import (
    IliMetaConfigCache,
    IliMetaConfigItemModel,
    MetaConfigCompleterDelegate,
    IliToppingFileCache,
    IliToppingFileItemModel
)
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.options import ModelListView

from qgis.PyQt.QtCore import (
    Qt, 
    QSettings,
    QTimer,
    QEventLoop
)

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QCompleter,
    QSizePolicy,
    QGridLayout,
    QMessageBox,
    QAction,
    QToolButton,
    QHeaderView,
    QAbstractItemView
)
from qgis.PyQt.QtGui import QPixmap
from qgis.gui import QgsGui, QgsMessageBar
from qgis.core import QgsCoordinateReferenceSystem

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_data_configuration.ui')

class ImportDataConfigurationPage(QWizardPage, PAGE_UI):

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)
        
        self.setupUi(self)
        self.setFixedSize(1200,800)
        self.setTitle(self.tr("Data import configuration"))
        self.log_panel = LogPanel()
        layout = self.layout()
        layout.addWidget(self.log_panel)
        self.setLayout(layout)

        self.import_wizard = parent
        self.is_complete = True
        
        self.import_wizard.import_data_file_model.sourceModel().setHorizontalHeaderLabels([self.tr('Import File'),self.tr('Dataset')])
        self.file_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table_view.setModel(self.import_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)