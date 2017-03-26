# -*- coding: utf-8 -*-

"""
/***************************************************************************
 QFieldSync
                              -------------------
        begin                : 2016
        copyright            : (C) 2016 by OPENGIS.ch
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

import inspect
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication
from functools import partial
import importlib
from qgis.PyQt.QtCore import qVersion


def selectFolder(line_edit_widget, title, file_filter, parent):
    filename, matched_filter = QtWidgets.QFileDialog.getOpenFileName(parent, title, line_edit_widget.text(), file_filter)
    line_edit_widget.setText(filename)


def make_file_selector(widget, title=QCoreApplication.translate('projectgenerator', 'Open File'), file_filter=QCoreApplication.translate('projectgenerator', 'Any file(*)'), parent=None):
    return partial(selectFolder, line_edit_widget=widget, title=title, file_filter=file_filter, parent=parent)
