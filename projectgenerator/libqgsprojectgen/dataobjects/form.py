# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 08/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
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

from qgis.core import (
    QgsEditFormConfig,
    QgsAttributeEditorContainer,
    QgsAttributeEditorRelation,
    QgsAttributeEditorField
)


class Form(object):

    def __init__(self):
        self.__elements = list()

    def elements(self):
        return self.__elements

    def create(self, layer):
        edit_form_config = layer.editFormConfig()
        root_container = edit_form_config.invisibleRootContainer()
        root_container.clear()
        for element in self.__elements:
            root_container.addChildElement(
                element.create(root_container, layer))
        edit_form_config.setLayout(QgsEditFormConfig.TabLayout)
        return edit_form_config

    def add_element(self, element):
        self.__elements.append(element)


class FormTab(object):

    def __init__(self, name, columns=1):
        self.name = name
        self.children = list()
        self.columns = columns

    def addChild(self, child):
        self.children.append(child)

    def create(self, parent, layer):
        container = QgsAttributeEditorContainer(self.name, parent)
        container.setIsGroupBox(False)
        container.setColumnCount(self.columns)

        for child in self.children:
            container.addChildElement(child.create(container, layer))
        return container


class FormGroupBox(object):

    def __init__(self, name, columns=1):
        self.name = name
        self.children = list()
        self.columns = columns

    def addChild(self, child):
        self.children.append(child)

    def create(self, parent, layer):
        container = QgsAttributeEditorContainer(self.name)
        container.setIsGroupBox(True)
        container.setColumnCount(self.columns)

        for child in self.children:
            container.addChildElement(child, layer)
        return container


class FormFieldWidget(object):

    def __init__(self, name, field_name):
        self.name = name if name else field_name
        self.field_name = field_name

    def create(self, parent, layer):
        index = layer.fields().indexOf(self.field_name)
        widget = QgsAttributeEditorField(self.field_name, index, parent)
        return widget


class FormRelationWidget(object):

    def __init__(self, relation):
        self.relation = relation

    def create(self, parent, layer):
        try:
            widget = QgsAttributeEditorRelation(
               self.relation.id, parent)
        except TypeError:
            # Feed deprecated API for 3.0.0 and 3.0.1
            widget = QgsAttributeEditorRelation(
               self.relation.id, self.relation.id, parent)
        return widget
