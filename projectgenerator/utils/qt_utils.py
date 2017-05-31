# -*- coding: utf-8 -*-

"""
/***************************************************************************
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
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QObject,
    QFile,
    QIODevice,
    QEventLoop,
    QUrl
)
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsNetworkAccessManager
from functools import partial


def selectFileName(line_edit_widget, title, file_filter, parent):
    filename, matched_filter = QFileDialog.getOpenFileName(parent, title, line_edit_widget.text(), file_filter)
    line_edit_widget.setText(filename)

def make_file_selector(widget, title=QCoreApplication.translate('projectgenerator', 'Open File'), file_filter=QCoreApplication.translate('projectgenerator', 'Any file(*)'), parent=None):
    return partial(selectFileName, line_edit_widget=widget, title=title, file_filter=file_filter, parent=parent)

def selectFileNameToSave(line_edit_widget, title, file_filter, parent):
    filename, matched_filter = QFileDialog.getSaveFileName(parent, title, line_edit_widget.text(), file_filter)
    line_edit_widget.setText(filename if filename.endswith('.xtf') else filename + '.xtf')

def make_save_file_selector(widget, title=QCoreApplication.translate('projectgenerator', 'Open File'), file_filter=QCoreApplication.translate('projectgenerator', 'Any file(*)'), parent=None):
    return partial(selectFileNameToSave, line_edit_widget=widget, title=title, file_filter=file_filter, parent=parent)

def selectFolder(line_edit_widget, title, parent):
    foldername = QFileDialog.getExistingDirectory(parent, title, line_edit_widget.text())
    line_edit_widget.setText(foldername)

def make_folder_selector(widget, title=QCoreApplication.translate('projectgenerator', 'Open Folder'), parent=None):
    return partial(selectFolder, line_edit_widget=widget, title=title, parent=parent)


class NetworkError(RuntimeError):
    def __init__(self, error_code, msg):
        self.msg = msg
        self.error_code = error_code


def download_file(url, filename, on_progress=None):
    """
    Will download the file from url to a local filename.
    The method will only return once it's finished.

    While downloading it will repeatedly report progress by calling on_progress
    with two parameters bytes_received and bytes_total.

    If an error occurs, it raises a NetworkError exception.

    It will return the filename if everything was ok.
    """
    network_access_manager = QgsNetworkAccessManager.instance()

    req = QNetworkRequest(QUrl(url))
    reply = network_access_manager.get(req)

    def on_download_progress(bytes_received, bytes_total):
        on_progress(bytes_received, bytes_total)

    def finished():
        print('Download finished {} ({})'.format(filename, reply.error()))
        file = QFile(filename)
        file.open(QIODevice.WriteOnly)
        file.write(reply.readAll())
        file.close()

    if on_progress:
        reply.downloadProgress.connect(on_download_progress)

    reply.finished.connect(finished)

    loop = QEventLoop()
    reply.finished.connect(loop.quit)
    loop.exec_()
    reply.deleteLater()

    if reply.error():
        raise NetworkError(reply.error(), reply.errorMessage)
    else:
        return filename
