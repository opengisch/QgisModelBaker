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
from .form import Form, FormTab, FormRelationWidget, FormFieldWidget
from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsWkbTypes
from qgis.PyQt.QtCore import QCoreApplication


class Layer(object):
    def __init__(self, provider, uri, is_domain=False):
        self.provider = provider
        self.uri = uri
        self.__layer = None
        self.fields = list()
        self.is_domain = is_domain
        self.__form = Form()

    def dump(self):
        definition = dict()
        definition['provider'] = self.provider
        definition['uri'] = self.uri
        definition['isdomain'] = self.is_domain
        definition['form'] = self.__form.dump()
        return definition

    def load(self, definition):
        self.provider = definition['provider']
        self.uri = definition['uri']
        self.is_domain = definition['isdomain']
        self.__form.load(definition['form'])

    def create(self):
        if self.__layer is None:
            layer_name = self.name
            self.__layer = QgsVectorLayer(self.uri, layer_name, self.provider)
            if self.is_domain:
                self.__layer.setReadOnly()

        for field in self.fields:
            field.create(self)

        return self.__layer

    def create_form(self, qgis_project):
        edit_form = self.__form.create(self.__layer)
        self.__layer.setEditFormConfig(edit_form)

    def post_generate(self, project):
        has_tabs = False
        for relation in project.relations:
            if relation.referencing_layer == self:
                has_tabs = True

        if has_tabs:
            tab = FormTab(QCoreApplication.translate('FormTab', 'General'))
            for field in self.fields:
                if field.widget != 'Hidden':
                    widget = FormFieldWidget(field.alias, field.name)
                    tab.addChild(widget)

            self.__form.add_element(tab)

            for relation in project.relations:
                if relation.referencing_layer == self:
                    tab = FormTab(relation.referenced_layer.name)
                    widget = FormRelationWidget(relation.referenced_layer.name, relation)
                    tab.addChild(widget)
                    self.__form.add_element(tab)

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

    @property
    def name(self) -> str:
        return self.table_name
