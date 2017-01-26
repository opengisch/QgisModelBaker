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

    def dump(self):
        definition = dict()
        definition['provider'] = self.provider
        definition['uri'] = self.uri

        return definition

    def load(self, definition):
        self.provider = definition['provider']
        self.uri = definition['uri']

    def create(self):
        print(self.uri)
        layer = QgsVectorLayer(self.uri, QgsDataSourceUri(self.uri).table(), self.provider)
        print('done')
        return layer
