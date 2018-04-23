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

    def __init__(self, provider, uri, name, geometry_column=None, wkb_type=QgsWkbTypes.Unknown, alias='', is_domain=False, is_nmrel=False):
        self.provider = provider
        self.uri = uri
        self.name = name
        self.geometry_column = geometry_column
        self.wkb_type = wkb_type
        self.alias = alias
        self.__layer = None
        self.fields = list()
        self.is_domain = is_domain

        self.is_nmrel = is_nmrel
        """ If is_nmrel is set to true it is a junction table in a N:M relation.
        Or in ili2db terms, the table is marked as ASSOCIATION in t_ili2db_table_prop.settings. """

        self.__form = Form()

    def dump(self):
        definition = dict()
        definition['provider'] = self.provider
        definition['uri'] = self.uri
        definition['isdomain'] = self.is_domain
        definition['isnmrel'] = self.is_nmrel
        definition['form'] = self.__form.dump()
        return definition

    def load(self, definition):
        self.provider = definition['provider']
        self.uri = definition['uri']
        self.is_domain = definition['isdomain']
        self.is_nmrel = definition['isnmrel']
        self.__form.load(definition['form'])

    def create(self):
        if self.__layer is None:
            layer_name = self.alias or self.name
            self.__layer = QgsVectorLayer(self.uri, layer_name, self.provider)
            if self.is_domain:
                self.__layer.setReadOnly()

        for field in self.fields:
            field.create(self)

        return self.__layer

    def create_form(self, project):
        edit_form = self.__form.create(self, self.__layer, project)
        self.__layer.setEditFormConfig(edit_form)

    def post_generate(self, project):
        '''
        Will be called when the whole project has been generated and
        therefore all relations are available and the form
        can also be generated.
        '''
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
                if relation.referenced_layer == self:
                    tab = FormTab(relation.referencing_layer.name)
                    widget = FormRelationWidget(relation)
                    tab.addChild(widget)
                    self.__form.add_element(tab)
        else:
            for field in self.fields:
                if field.widget != 'Hidden':
                    widget = FormFieldWidget(field.alias, field.name)
                    self.__form.add_element(widget)

    @property
    def layer(self):
        return self.__layer

    @property
    def real_id(self):
        '''
        The layer id. Only valid after creating the layer.
        '''
        if self.__layer:
            return self.__layer.id()
        else:
            return None
