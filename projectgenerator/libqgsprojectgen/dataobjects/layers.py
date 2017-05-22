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

from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsWkbTypes


class Layer:
    def __init__(self, provider, uri, is_domain=False):
        self.provider = provider
        self.uri = uri
        self.__layer = None
        self.fields = list()
        self.is_domain = is_domain

    def dump(self):
        definition = dict()
        definition['provider'] = self.provider
        definition['uri'] = self.uri
        definition['isdomain'] = self.is_domain

        return definition

    def load(self, definition):
        self.provider = definition['provider']
        self.uri = definition['uri']
        self.is_domain = definition['isdomain']

    def create(self):
        if not self.__layer:
            layer_name = self.table_name
            self.__layer = QgsVectorLayer(self.uri, layer_name, self.provider)
            if self.is_domain:
                self.__layer.setReadOnly()

        for field in self.fields:
            field.create(self)

        return self.__layer

    @property
    def layer(self):
        return self.__layer

    @property
    def real_id(self):
        if self.__layer:
            return self.__layer.id()
        else:
            return None

    @property
    def table_name(self):
        return QgsDataSourceUri(self.uri).table()

    @property
    def geometry_column(self):
        return QgsDataSourceUri(self.uri).geometryColumn()

    @property
    def wkb_type(self) -> QgsWkbTypes.Type:
        return QgsDataSourceUri(self.uri).wkbType()
