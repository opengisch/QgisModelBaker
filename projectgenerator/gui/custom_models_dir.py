# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 11.08.2017
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
from projectgenerator.utils.qt_utils import selectFolder

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem


DIALOG_UI = get_ui_class('custom_models_dir.ui')

class CustomModelsDir(QDialog, DIALOG_UI):
    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        self.parent = parent
        string_model = self.configuration()
        
        if ";" in string_model: 
            list_model = string_model.split(";")
            self.model_dir_list.addItems([model for model in list_model if model.strip()])
            for i in range(self.model_dir_list.count()):
                self.flags_on(self.model_dir_list.item(i)) 
        else:        
            list_model = string_model     
            self.model_dir_list.addItem(list_model)
            self.flags_on(self.model_dir_list.item(0))
        
        self.model_dir_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.add_button.clicked.connect(self.add_model_dir)
        self.rem_button.clicked.connect(self.rem_model_dir)
        self.browse_button.clicked.connect(self.browse_dir)        
        self.buttonBox.accepted.connect(self.accepted)

        self.browse_button.setEnabled(False)
        self.rem_button.setEnabled(False)
        
    def add_model_dir(self):
        item = QListWidgetItem()
        self.flags_on(item)
        self.model_dir_list.addItem(item)
                
    def rem_model_dir(self):
        for item in self.model_dir_list.selectedItems():
            self.model_dir_list.takeItem(self.model_dir_list.row(item))

    def accepted(self):
        items = []
        for x in range(self.model_dir_list.count()):
            item = self.model_dir_list.item(x)
            items.append(item)
        model_dir = [i.text().strip() for i in items if i.text().strip()]
        model_dirs = ";".join(model_dir)
        self.parent.custom_model_directories_line_edit.setText(model_dirs) 
        
    def browse_dir(self):    
        selectFolder(self.model_dir_list.currentItem(), title=QCoreApplication.translate('projectgenerator', 'Open Folder With ili models'), parent=None)
        
    def flags_on(self,item):
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)

    def on_selection_changed(self):
        self.browse_button.setEnabled(True)
        self.rem_button.setEnabled(True)
        print("cambio de seleccion")
        return True
