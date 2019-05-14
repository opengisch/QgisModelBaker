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
from abc import ABC, abstractmethod


class DbFactory:

    @abstractmethod
    def get_db_connector(self, uri, schema):
        pass

    @abstractmethod
    def get_config_panel(self, parent, db_action_type):
        pass

    @abstractmethod
    def get_db_command_config_manager(self, configuration):
        pass

    @abstractmethod
    def get_layer_uri(self, uri):
        pass

    @abstractmethod
    def pre_generate_project(self, configuration):
        pass

    @abstractmethod
    def post_generate_project_validations(self, configuration):
        pass

    @abstractmethod
    def get_tool_version(self):
        pass

    @abstractmethod
    def get_tool_url(self):
        pass

    def get_schema_import_args(self):
        return list()

    def get_specific_messages(self):
        messages = {
            'db_or_schema': 'schema',
            'layers_source':   'schema'
        }

        return messages
