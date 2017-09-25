# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 24/08/17
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

from projectgenerator.libili2db.ili2dbconfig import ImportConfiguration, ExportConfiguration, BaseConfiguration


def iliimporter_config():
    base_config = BaseConfiguration()
    base_config.custom_model_directories = testdata_path('ilimodels')
    base_config.custom_model_directories_enabled = True

    configuration = ImportConfiguration()
    configuration.host = 'postgres'
    configuration.user = 'docker'
    configuration.password = 'docker'
    configuration.database = 'gis'
    return configuration

def iliexporter_config(tool_name='ili2pg'):
    base_config = BaseConfiguration()
    base_config.custom_model_directories = testdata_path('ilimodels')
    base_config.custom_model_directories_enabled = True
    configuration = ExportConfiguration()
    if tool_name == 'ili2pg':
        configuration.host = 'postgres'
        configuration.user = 'docker'
        configuration.password = 'docker'
        configuration.database = 'gis'
    elif tool_name == 'ili2gpkg':
        configuration.dbfile = testdata_path('geopackage/test_export.gpkg')

    return configuration

def testdata_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, 'testdata', path)

def rm_file(file):
    return os.remove(file)
