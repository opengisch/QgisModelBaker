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

from qgis.core import Qgis
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import (
    QGridLayout,
    QProgressBar,
    QSizePolicy,
    QTextBrowser,
    QWidget,
)

from QgisModelBaker.utils.gui_utils import (
    LogLevel,
    get_parsed_log_text_level,
    get_text_color_object,
)


class LogPanel(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.logger = logging.getLogger("qgismodelbaker")
        self.txtStdout = QTextBrowser()
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignmentFlag.AlignTop)
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

    def print_info(self, text, level=LogLevel.INFO):
        self.txtStdout.setTextColor(get_text_color_object(level))
        self.txtStdout.append(text)

        if level in (LogLevel.INFO, LogLevel.SUCCESS, LogLevel.TOPPING):
            self.logger.info(text)
        elif level == LogLevel.WARNING:
            self.logger.warning(text)
        elif level == LogLevel.FAIL:
            self.logger.error(text)

    def print_stdout_info(self, text):
        self.print_info(text, get_parsed_log_text_level(text))

    def show_message(self, level, message):
        if level == Qgis.MessageLevel.Warning:
            self.bar.pushMessage(message, Qgis.MessageLevel.Info, 10)
        elif level == Qgis.MessageLevel.Critical:
            self.bar.pushMessage(message, Qgis.MessageLevel.Warning, 10)
