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
from QgisModelBaker.libili2db.globals import DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration


class DbFactory:

    @abstractmethod
    def get_db_connector(self, uri: str, schema: str):
        pass

    @abstractmethod
    def get_config_panel(self, parent, db_action_type: DbActionType):
        pass

    @abstractmethod
    def get_db_command_config_manager(self, configuration: Ili2DbCommandConfiguration):
        pass

    @abstractmethod
    def get_layer_uri(self, uri: str):
        pass

    @abstractmethod
    def pre_generate_project(self, configuration: Ili2DbCommandConfiguration):
        pass

    @abstractmethod
    def post_generate_project_validations(self, configuration: Ili2DbCommandConfiguration):
        pass

    @abstractmethod
    def get_tool_version(self):
        pass

    @abstractmethod
    def get_tool_url(self):
        pass

    def get_specific_messages(self):
        messages = {
            'db_or_schema': 'schema',
            'layers_source':   'schema'
        }

        return messages
