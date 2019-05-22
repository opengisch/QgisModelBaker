# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    30/04/19
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


class LayerUri:

    def __init__(self, uri):
        self.uri = uri
        self.provider = None

    @abstractmethod
    def get_data_source_uri(self, record):
        pass
