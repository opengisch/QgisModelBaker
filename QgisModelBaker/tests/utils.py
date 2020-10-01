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
import pytest
from subprocess import call

from QgisModelBaker.libili2db import ili2dbconfig
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libili2db.ili2dbconfig import SchemaImportConfiguration, ExportConfiguration, \
    ImportDataConfiguration, BaseConfiguration, UpdateDataConfiguration
from QgisModelBaker.libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory

def iliimporter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = SchemaImportConfiguration()
    configuration.tool = tool
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = os.environ['PGHOST']
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = 'mssql'
        configuration.dbusr = 'sa'
        configuration.dbpwd = '<YourStrong!Passw0rd>'
        configuration.database = 'gis'
    configuration.base_configuration = base_config

    return configuration


def iliexporter_config(tool=DbIliMode.ili2pg, modeldir=None, gpkg_path='geopackage/test_export.gpkg'):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ExportConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = os.environ['PGHOST']
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = 'mssql'
        configuration.dbusr = 'sa'
        configuration.dbpwd = '<YourStrong!Passw0rd>'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2gpkg:
        configuration.dbfile = testdata_path(gpkg_path)
    configuration.base_configuration = base_config

    return configuration


def ilidataimporter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ImportDataConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = os.environ['PGHOST']
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = 'mssql'
        configuration.dbusr = 'sa'
        configuration.dbpwd = '<YourStrong!Passw0rd>'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2gpkg:
        configuration.dbfile = testdata_path('geopackage/test_export.gpkg')
    configuration.base_configuration = base_config

    return configuration


def iliupdater_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = UpdateDataConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = os.environ['PGHOST']
        configuration.dbusr = 'docker'
        configuration.dbpwd = 'docker'
        configuration.database = 'gis'
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = 'mssql'
        configuration.dbusr = 'sa'
        configuration.dbpwd = '<YourStrong!Passw0rd>'
        configuration.database = 'gis'

    configuration.base_configuration = base_config

    return configuration

@pytest.mark.skip('This is a utility function, not a test function')
def testdata_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, 'testdata', path)


def get_pg_conn(schema):
    myenv = os.environ.copy()
    myenv['PGPASSWORD'] = 'docker'

    call(["pg_restore", "-Fc", "-h" + os.environ['PGHOST'], "-Udocker", "-dgis", testdata_path("dumps/{}_dump".format(schema))], env=myenv)
    db_factory = DbSimpleFactory().create_factory(DbIliMode.pg)
    configuration = ili2dbconfig.ExportConfiguration()

    configuration.database = "gis"
    configuration.dbhost = os.environ['PGHOST']
    configuration.dbusr = "docker"
    configuration.dbpwd = "docker"
    configuration.dbport = "5432"

    config_manager = db_factory.get_db_command_config_manager(configuration)
    db_connector = db_factory.get_db_connector(config_manager.get_uri(), schema)
    return db_connector

def get_gpkg_conn(gpkg):
    db_factory = DbSimpleFactory().create_factory(DbIliMode.gpkg)
    db_connector = db_factory.get_db_connector(testdata_path('geopackage/{}.gpkg'.format(gpkg)), None)
    return db_connector

def get_pg_connection_string():
    pg_host = os.environ['PGHOST']
    return 'dbname=gis user=docker password=docker host={pg_host}'.format(pg_host=pg_host)

