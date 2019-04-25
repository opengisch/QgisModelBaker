# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    23/04/19
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


class DbConfigPanel:

    def __init__(self):
        pass

    @abstractmethod
    def show_panel(self, interlis_mode=False):
        pass

    @abstractmethod
    def get_fields(self, configuration):
        """
        Get Panel fields into 'configuration' parameter
        :param configuration: (Ili2DbCommandConfiguration)
        """
        pass

    @abstractmethod
    def set_fields(self, configuration):
        """
        Set Panel fields
        :param configuration: (Ili2DbCommandConfiguration)
        """
        pass

    @abstractmethod
    def is_valid(self):
        pass