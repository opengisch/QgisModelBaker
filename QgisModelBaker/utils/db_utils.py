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
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory

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

def get_db_connector(configuration):
    db_simple_factory = DbSimpleFactory()
    schema = configuration.dbschema

    db_factory = db_simple_factory.create_factory(configuration.tool)
    config_manager = db_factory.get_db_command_config_manager(configuration)
    uri_string = config_manager.get_uri(configuration.db_use_super_login)

    try:
        return db_factory.get_db_connector(uri_string, schema)
    except (DBConnectorError, FileNotFoundError):
        return None

def db_ili_version(configuration):
    """
    Returns the ili2db version the database has been created with or None if the database
    could not be detected as a ili2db database
    """ 
    db_connector = get_db_connector(configuration)
    if db_connector:
        return db_connector.ili_version()