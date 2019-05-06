# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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
from qgis.PyQt.QtCore import QSettings
from .db_factory import DbFactory
from ..dbconnector.gpkg_connector import GPKGConnector
from .gpkg_uri import GpkgUri
from .gpkg_layer_uri import GpkgLayerUri
from ...gui.panel.gpkg_config_panel import GpkgConfigPanel


class GpkgFactory(DbFactory):

    def get_db_connector(self, uri, schema):
        return GPKGConnector(uri, None)

    def get_config_panel(self, parent, db_action_type):
        return GpkgConfigPanel(parent, db_action_type)

    def get_db_uri(self):
        return GpkgUri()

    def get_layer_uri(self, uri):
        return GpkgLayerUri(uri)

    def pre_generate_project(self, configuration):
        pass

    def post_generate_project_validations(self, configuration):
        return True, ''

    def save_settings(self, configuration):
        # TODO repair string path settings
        settings = QSettings()
        settings.setValue('QgisModelBaker/ili2gpkg/dbfile', configuration.dbfile)

    def load_settings(self, configuration):
        settings = QSettings()
        configuration.dbfile = settings.value('QgisModelBaker/ili2gpkg/dbfile')

    def get_tool_version(self):
        return '3.11.3'

    def get_tool_url(self):
        return 'http://www.eisenhutinformatik.ch/interlis/ili2gpkg/ili2gpkg-{}.zip'.format(self.get_tool_version())
