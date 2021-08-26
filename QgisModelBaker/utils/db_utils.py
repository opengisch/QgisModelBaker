# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 18.08.2021
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

from QgisModelBaker.utils.qt_utils import slugify
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration
from QgisModelBaker.libili2db.globals import DbIliMode

def get_schema_identificator(layer_source_name, layer_source):
    if layer_source_name == 'postgres' or layer_source_name == 'mssql':
        return slugify(f'{layer_source.host()}_{layer_source.database()}_{layer_source.schema()}')
    elif layer_source_name == 'ogr':
        return slugify(layer_source.uri().split('|')[0].strip())
    return ''

def get_configuration(layer_source_name, layer_source):
    mode = ''
    configuration = Ili2DbCommandConfiguration()
    if layer_source_name == 'postgres':
        mode = DbIliMode.pg
        configuration.dbhost = layer_source.host()
        configuration.dbusr = layer_source.username()
        configuration.dbpwd = layer_source.password()
        configuration.database = layer_source.database()
        configuration.dbschema = layer_source.schema()
    elif layer_source_name == 'ogr':
        mode = DbIliMode.gpkg
        configuration.dbfile = layer_source.uri().split('|')[0].strip()
    elif layer_source_name == 'mssql':
        mode = DbIliMode.mssql
        configuration.dbhost = layer_source.host()
        configuration.dbusr = layer_source.username()
        configuration.dbpwd = layer_source.password()
        configuration.database = layer_source.database()
        configuration.dbschema = layer_source.schema()
    return mode, configuration