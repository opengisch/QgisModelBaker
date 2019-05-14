# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    13/05/19
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


class DbCommandConfigManager:

    def __init__(self, configuration):
        self.configuration = configuration

    @abstractmethod
    def get_uri(self, su):
        pass

    @abstractmethod
    def get_db_args(self, hide_password=False):
        pass

    @abstractmethod
    def save_config_in_qsettings(self):
        pass

    @abstractmethod
    def load_config_from_qsettings(self):
        pass
