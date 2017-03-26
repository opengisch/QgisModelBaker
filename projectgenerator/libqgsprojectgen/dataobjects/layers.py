# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2016-11-14
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
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

from qgis.core import QgsVectorLayer, QgsDataSourceUri


class Layer:
    def __init__(self, provider, uri):
        self.provider = provider
        self.uri = uri
        self.__layer = None

    def dump(self):
        definition = dict()
        definition['provider'] = self.provider
        definition['uri'] = self.uri

        return definition

    def load(self, definition):
        self.provider = definition['provider']
        self.uri = definition['uri']

    def create(self):
        if not self.__layer:
            layer_name = self.table_name()
            print(' ==> Creating layer "{}"'.format(layer_name))
            self.__layer = QgsVectorLayer(self.uri, layer_name, self.provider)
        return self.__layer

    def table_name(self):
        return QgsDataSourceUri(self.uri).table()