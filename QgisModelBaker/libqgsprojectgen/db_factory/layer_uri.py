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


class LayerUri(ABC):
    """Provides layer uri based on database uri (connection string) and specific information of the data source. This is a abstract class.

    This **layer uri** is used to create a Qgis layer.

    :ivar str uri: Database uri.
    :ivar str provider: Database provider.
    """

    def __init__(self, uri):
        """
        :param str uri: Database uri. This is the same database uri of the db connectors.
        """
        self.uri = uri
        self.provider = None

    @abstractmethod
    def get_data_source_uri(self, record: dict):
        """Provides layer uri based on database uri and specific information of the data source.

        :param str record: Dictionary containing specific information of the data source.
        :return: Layer uri.
        :rtype: str
        """
