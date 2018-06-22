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
        self.init_function = None
        self.init_code = None
        self.init_code_source = None

    def elements(self):
        return self.__elements

    def create(self, layer, qgis_layer, project):
        edit_form_config = qgis_layer.editFormConfig()
        root_container = edit_form_config.invisibleRootContainer()
        root_container.clear()
        for element in self.__elements:
            root_container.addChildElement(
                element.create(root_container, qgis_layer))
        edit_form_config.setLayout(QgsEditFormConfig.TabLayout)
        # set nm-rel if referencing tables are junction table
        for relation in project.relations:
            if relation.referenced_layer == layer:
                # get other relations, that have the same referencing_layer and set the first as nm-rel
                for other_relation in project.relations:
                    if other_relation.referencing_field != relation.referencing_field and other_relation.referencing_layer == relation.referencing_layer and relation.referencing_layer.is_nmrel:
                        edit_form_config.setWidgetConfig(relation.id, {'nm-rel': other_relation.id})
                        break

        if self.init_function:
            edit_form_config.setInitFunction(self.init_function)

        if self.init_code:
            edit_form_config.setInitCode(self.init_code)

        if self.init_code_source:
            if self.init_code_source == 'CodeSourceNone':
                edit_form_config.setInitCodeSource(QgsEditFormConfig.CodeSourceNone)
            elif self.init_code_source == 'CodeSourceFile':
                edit_form_config.setInitCodeSource(QgsEditFormConfig.CodeSourceFile)
            elif self.init_code_source == 'CodeSourceDialog':
                edit_form_config.setInitCodeSource(QgsEditFormConfig.CodeSourceDialog)
            elif self.init_code_source == 'CodeSourceEnvironment':
                edit_form_config.setInitCodeSource(QgsEditFormConfig.CodeSourceEnvironment)


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
