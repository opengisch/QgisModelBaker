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

import logging

from PyQt5.QtWidgets import QGridLayout, QProgressBar
from qgis.core import Qgis
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QGridLayout, QSizePolicy, QTextBrowser, QWidget

from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import color_log_text
from QgisModelBaker.utils.gui_utils import LogColor


class LogPanel(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.txtStdout = QTextBrowser()
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)
        self.scrollbar = self.txtStdout.verticalScrollBar()

        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setTextVisible(True)
        self.busy_bar.setVisible(False)

        layout = QGridLayout()
        layout.addWidget(self.txtStdout)
        layout.addWidget(self.busy_bar)

        self.setLayout(layout)

    def sizeHint(self):
        return QSize(
            self.fontMetrics().lineSpacing() * 48, self.fontMetrics().lineSpacing() * 10
        )

    def print_info(self, text, text_color=LogColor.COLOR_INFO):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)

        if text_color == LogColor.COLOR_INFO:
            logging.info(text)
        elif text_color == LogColor.COLOR_SUCCESS:
            logging.info(text)
        elif text_color == LogColor.COLOR_WARNING:
            logging.warning(text)
        elif text_color == LogColor.COLOR_FAIL:
            logging.error(text)
        elif text_color == LogColor.COLOR_TOPPING:
            logging.info(text)

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)
