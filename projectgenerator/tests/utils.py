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

from projectgenerator.libili2db.ili2dbconfig import SchemaImportConfiguration, ExportConfiguration, ImportDataConfiguration, BaseConfiguration


def iliimporter_config(tool_name='ili2pg', modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = SchemaImportConfiguration()
    configuration.tool_name = tool_name
    if tool_name == 'ili2pg':
        configuration.dbhost = 'postgres'
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    configuration.base_configuration = base_config

    return configuration


def iliexporter_config(tool_name='ili2pg', modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ExportConfiguration()
    if tool_name == 'ili2pg':
        configuration.dbhost = 'postgres'
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool_name == 'ili2gpkg':
        configuration.dbfile = testdata_path('geopackage/test_export.gpkg')
    configuration.base_configuration = base_config

    return configuration


def ilidataimporter_config(tool_name='ili2pg', modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ImportDataConfiguration()
    if tool_name == 'ili2pg':
        configuration.dbhost = 'postgres'
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool_name == 'ili2gpkg':
        configuration.dbfile = testdata_path('geopackage/test_export.gpkg')
    configuration.base_configuration = base_config

    return configuration


def testdata_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, 'testdata', path)
