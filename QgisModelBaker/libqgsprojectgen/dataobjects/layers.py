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
import logging

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsDataSourceUri,
    QgsExpressionContextUtils,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication, QSettings

from QgisModelBaker.libqgsprojectgen.generator.config import IGNORED_FIELDNAMES

from .form import Form, FormFieldWidget, FormRelationWidget, FormTab


class Layer(object):
    def __init__(
        self,
        provider,
        uri,
        name,
        srid,
        extent,
        geometry_column=None,
        wkb_type=QgsWkbTypes.Unknown,
        alias=None,
        is_domain=False,
        is_structure=False,
        is_nmrel=False,
        display_expression=None,
        coordinate_precision=None,
        is_basket_table=False,
        is_dataset_table=False,
        ili_name=None,
    ):
        self.provider = provider
        self.uri = uri
        self.name = name
        if extent is not None:
            extent_coords = extent.split(";")
            extent = QgsRectangle(
                float(extent_coords[0]),
                float(extent_coords[1]),
                float(extent_coords[2]),
                float(extent_coords[3]),
            )
        self.extent = extent
        self.geometry_column = geometry_column
        self.wkb_type = wkb_type
        self.alias = alias
        self.__layer = None
        self.fields = list()
        self.is_domain = is_domain
        self.is_structure = is_structure

        self.is_nmrel = is_nmrel
        self.srid = srid
        """ If is_nmrel is set to true it is a junction table in a N:M relation.
        Or in ili2db terms, the table is marked as ASSOCIATION in t_ili2db_table_prop.settings. """

        self.display_expression = display_expression

        self.coordinate_precision = coordinate_precision

        self.is_basket_table = is_basket_table
        self.is_dataset_table = is_dataset_table

        self.ili_name = ili_name

        self.model_topic_name = ""
        if self.ili_name:
            if self.ili_name.count(".") > 1:
                self.model_topic_name = (
                    f"{self.ili_name.split('.')[0]}.{self.ili_name.split('.')[1]}"
                )

        self.__form = Form()

        # legend settings
        self.expanded = True
        self.checked = True
        self.featurecount = False

    def dump(self):
        definition = dict()
        definition["provider"] = self.provider
        definition["uri"] = self.uri
        definition["isdomain"] = self.is_domain
        definition["isstructure"] = self.is_structure
        definition["isnmrel"] = self.is_nmrel
        definition["isbaskettable"] = self.is_basket_table
        definition["isdatasettable"] = self.is_dataset_table
        definition["displayexpression"] = self.display_expression
        definition["coordinateprecision"] = self.coordinate_precision
        definition["modeltopicname"] = self.model_topic_name
        definition["form"] = self.__form.dump()
        return definition

    def load(self, definition):
        self.provider = definition["provider"]
        self.uri = definition["uri"]
        self.is_domain = definition["isdomain"]
        self.is_structure = definition["isstructure"]
        self.is_nmrel = definition["isnmrel"]
        self.is_basket_table = definition["isbaskettable"]
        self.is_dataset_table = definition["isdatasettable"]
        self.display_expression = definition["displayexpression"]
        self.coordinate_precision = definition["coordinateprecision"]
        self.model_topic_name = definition["modeltopicname"]
        self.__form.load(definition["form"])

    def create(self):
        if self.__layer is None:
            layer_name = self.alias or self.name

            settings = QSettings()
            # Take the "CRS for new layers" config, overwrite it while loading layers and...
            old_proj_value = settings.value(
                "/Projections/defaultBehaviour", "prompt", type=str
            )
            settings.setValue("/Projections/defaultBehaviour", "useProject")
            self.__layer = QgsVectorLayer(self.uri, layer_name, self.provider)
            settings.setValue("/Projections/defaultBehavior", old_proj_value)

            if (
                self.srid is not None
                and not self.__layer.crs().authid() == "EPSG:{}".format(self.srid)
            ):
                crs = QgsCoordinateReferenceSystem().fromEpsgId(self.srid)
                if not crs.isValid():
                    crs = QgsCoordinateReferenceSystem(self.srid)  # Fallback
                self.__layer.setCrs(crs)
            if self.is_domain or self.is_dataset_table:
                self.__layer.setReadOnly()
            if self.display_expression:
                self.__layer.setDisplayExpression(self.display_expression)
            if self.coordinate_precision and self.coordinate_precision < 1:
                self.__layer.geometryOptions().setGeometryPrecision(
                    self.coordinate_precision
                )
                self.__layer.geometryOptions().setRemoveDuplicateNodes(True)

            if self.model_topic_name:
                QgsExpressionContextUtils.setLayerVariable(
                    self.__layer, "interlis_topic", self.model_topic_name
                )

        for field in self.fields:
            field.create(self)

        return self.__layer

    def create_form(self, project):
        edit_form = self.__form.create(self, self.__layer, project)
        self.__layer.setEditFormConfig(edit_form)

    def post_generate(self, project):
        """
        Will be called when the whole project has been generated and
        therefore all relations are available and the form
        can also be generated.
        """
        has_tabs = False
        for relation in project.relations:
            if relation.referenced_layer == self:
                has_tabs = True
                break

        if has_tabs:
            num_fields = len([f for f in self.fields if not f.hidden])
            if num_fields > 5:
                num_tabs = 2
            else:
                num_tabs = 1
            tab = FormTab(QCoreApplication.translate("FormTab", "General"), num_tabs)
            for field in self.fields:
                if not field.hidden:
                    widget = FormFieldWidget(field.alias, field.name)
                    tab.addChild(widget)

            self.__form.add_element(tab)

            relations_to_add = []
            for relation in project.relations:
                if relation.referenced_layer == self:

                    # 1:m relation will be added only if does not point to a pure link table
                    if (
                        not relation.referencing_layer.isPureLinkTable(project)
                        or Qgis.QGIS_VERSION_INT < 31600
                    ):
                        relations_to_add.append((relation, None))

                    else:
                        for nm_relation in project.relations:
                            if nm_relation == relation:
                                continue

                            if nm_relation.referenced_layer == self:
                                continue

                            # relations to the same table with different geometries should not be added
                            if nm_relation.referenced_layer.srid == self.srid:
                                continue

                            if nm_relation.referenced_layer.is_basket_table:
                                continue

                            if (
                                nm_relation.referencing_layer
                                == relation.referencing_layer
                            ):
                                relations_to_add.append((relation, nm_relation))

            for relation, nm_relation in relations_to_add:
                if nm_relation and Qgis.QGIS_VERSION_INT < 31600:
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        'QGIS version older than 3.16. Relation editor widget for relation "{0}" will not be added.'.format(
                            nm_relation.name
                        )
                    )
                    continue

                if nm_relation:
                    tab = FormTab(nm_relation.referenced_layer.name)
                else:
                    tab = FormTab(relation.referencing_layer.name)

                widget = FormRelationWidget(relation, nm_relation)
                tab.addChild(widget)
                self.__form.add_element(tab)

        else:
            for field in self.fields:
                if not field.hidden:
                    widget = FormFieldWidget(field.alias, field.name)
                    self.__form.add_element(widget)

    def source(self):
        return QgsDataSourceUri(self.uri)

    @property
    def layer(self):
        return self.__layer

    @property
    def real_id(self):
        """
        The layer id. Only valid after creating the layer.
        """
        if self.__layer:
            return self.__layer.id()
        else:
            return None

    def isPureLinkTable(self, project):
        """
        Returns True if the layer is a pure link table in a n:m relation.
        With "pure" it is meant the layer has no more fields than foreign keys and its id.
        """

        remaining_fields = set()
        for field in self.fields:
            if field.name not in IGNORED_FIELDNAMES:
                remaining_fields.add(field.name)

        # Remove all fields that are referencing fields
        for relation in project.relations:
            if relation.referencing_layer != self:
                continue
            remaining_fields.discard(relation.referencing_field)

        return len(remaining_fields) == 0
