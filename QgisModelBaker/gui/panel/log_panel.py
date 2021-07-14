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

from PyQt5.QtWidgets import QGridLayout
from qgis.PyQt.QtWidgets import (
    QWidget,
    QTextBrowser,
    QSizePolicy,
    QGridLayout
)
from qgis.PyQt.QtGui import (
    QColor
)

from qgis.PyQt.QtCore import (
    Qt
)

from qgis.gui import (
    QgsMessageBar
)
from qgis.core import (
    Qgis
)

from QgisModelBaker.libili2db.ili2dbutils import color_log_text

class LogPanel(QWidget):

    COLOR_INFO = '#000000'
    COLOR_SUCCESS = '#004905'
    COLOR_FAIL = '#aa2222'
    COLOR_TOPPING = '#341d5c'

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        self.txtStdout = QTextBrowser()
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        layout = QGridLayout()
        layout.addWidget(self.txtStdout)
        self.setLayout(layout)

    def print_info(self, text, text_color='#000000'):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)