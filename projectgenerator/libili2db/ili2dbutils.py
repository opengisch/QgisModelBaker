# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 14.9.17
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
import os
import tempfile
import zipfile
import glob

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor

from projectgenerator.utils.qt_utils import download_file, NetworkError


def get_ili2db_bin(tool_name, stdout, stderr, ili2db_tools):
    if not tool_name:
        return
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ili2db_dir = '{}-{}'.format(tool_name, ili2db_tools[tool_name]['version'])

    ili2db_file = os.path.join(
        dir_path, 'bin', ili2db_dir, '{}.jar'.format(tool_name))
    if not os.path.isfile(ili2db_file):
        try:
            os.mkdir(os.path.join(dir_path, 'bin'))
        except FileExistsError:
            pass

        tmpfile = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)

        stdout.emit(QCoreApplication.translate('ili2dbutils', 'Downloading {} version {}…'.format(
            tool_name, ili2db_tools[tool_name]['version'])))

        try:
            download_file(ili2db_tools[tool_name][
                          'url'], tmpfile.name, on_progress=lambda received, total: stdout.emit('.'))
        except NetworkError as e:
            stderr.emit(
                QCoreApplication.translate('ili2dbutils',
                                           'Could not download {tool_name}\n\n  Error: {error}\n\nFile "{file}" not found. Please download and extract <a href="{ili2db_url}">{ili2db_url}</a>'.format(
                                               ili2db_url=ili2db_tools[
                                                   tool_name]['version'],
                                               error=e.msg,
                                               file=ili2db_file)
                                           )
            )
            return None

        try:
            with zipfile.ZipFile(tmpfile.name, "r") as z:
                z.extractall(os.path.join(dir_path, 'bin'))
        except zipfile.BadZipFile:
            # We will realize soon enough that the files were not extracted
            pass

        if not os.path.isfile(ili2db_file):
            stderr.emit(
                QCoreApplication.translate('ili2dbutils',
                                           'File "{file}" not found. Please download and extract <a href="{ili2db_url}">{ili2db_url}</a>.'.format(
                                               file=ili2db_file,
                                               ili2db_url=ili2db_tools[tool_name]['version'])))
            return None

    return ili2db_file

def get_all_modeldir_in_path(path, lambdafunction=None):
    all_subdirs = [path[0] for path in os.walk(path)] # include path
    modeldir = ''
    for subdir in all_subdirs:
        if os.path.isdir(subdir) and '/.' not in subdir and len(glob.glob(subdir + '/*.ili')) > 0:
            if lambdafunction is not None:
                lambdafunction(subdir)
            modeldir += subdir + ';'
    return modeldir[:-1]  # remove last ';'

def color_log_text(text, txt_edit):
    textlines = text.splitlines()
    for textline in textlines:
        if textline.startswith("Warning:"):
            txt_edit.setTextColor(QColor('#FFBF00'))
            txt_edit.append(textline)
        elif "error" in textline.lower() or "failed" in textline.lower():
            txt_edit.setTextColor(QColor('#aa2222'))
            txt_edit.append(textline)
        else:
            txt_edit.setTextColor(QColor('#2a2a2a'))
            txt_edit.append(textline)
