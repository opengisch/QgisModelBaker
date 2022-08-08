# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
        email                : david at opengis ch
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

import configparser
import datetime
import os

from qgis.core import QgsDataSourceUri, QgsProject

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.internal_libs.projecttopping.projecttopping import (
    ExportSettings,
    ProjectTopping,
    Target,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.utils.gui_utils import SchemaModelsModel


class MetaConfig(object):
    def __init__(self):
        self.configuration_settings = {}
        # set configuration_section["ch.interlis.referenceData"] = ...
        # set configuration_section["qgis.modelbaker.projecttopping"] = ...

        self.ili2db_settings = {}
        # set ili2db configuration - toml and sql files should be appended as topping

    def parse_ili2db_settings(self, configuration: Ili2DbCommandConfiguration):
        self.ili2db_section = {}

    def update_ili2db_settings(self, key: str, value: str):
        self.ili2db_section[key] = value

    def update_configuration_settings(self, key: str, value: str):
        self.configuration_settings[key] = value

    def generate_file(self, target: Target):
        """
        [CONFIGURATION]
        qgis.modelbaker.projecttopping=ilidata:ch.opengis.config.KbS_LV95_V1_4_projecttopping
        ch.interlis.referenceData=ilidata:ch.opengis.config.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        defaultSrsCode = 2056
        smart2Inheritance = true
        strokeArcs = false
        importTid = true
        createTidCol = false
        models = KbS_Basis_V1_4
        preScript=ilidata:ch.opengis.config.KbS_LV95_V1_4_prescript
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml
        """

        metaconfig = configparser.ConfigParser()
        metaconfig["CONFIGURATION"] = self.configuration_settings
        metaconfig["ch.ehi.ili2db"] = self.ili2db_settings

        # write file
        # self.generate_toppingfile
        # return id


class ToppingMaker(object):
    def __init__(self):
        # the information set by the external party (e.g. GUI)
        self.target = Target()
        self.exportsettings = ExportSettings()
        self.referencedata_paths = []
        self.ili2dbsettings = {}
        self.metaattr_filepath = None
        self.prescript_filepath = None
        self.postscript_filepath = None

        # received by topping maker
        self.metaconfig = MetaConfig()
        self.project_topping = ProjectTopping()
        self.models_model = SchemaModelsModel()

    def load_available_models(self, project: QgsProject):
        root = project.layerTreeRoot()
        checked_identificators = []
        db_connectors = []
        for layer_node in root.findLayers():
            source_provider = layer_node.layer().dataProvider()
            source = QgsDataSourceUri(layer_node.layer().dataProvider().dataSourceUri())
            schema_identificator = db_utils.get_schema_identificator_from_layersource(
                source_provider, source
            )
            if schema_identificator in checked_identificators:
                continue
            else:
                checked_identificators.append(schema_identificator)
                current_configuration = Ili2DbCommandConfiguration()
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, current_configuration
                )
                if valid and mode:
                    current_configuration.tool = mode
                    db_connector = db_utils.get_db_connector(current_configuration)
                    db_connectors.append(db_connector)
        self.models_model.refresh_model(db_connectors)

    def create_target(self, projectname, maindir, subdir):
        self.target = Target(projectname, maindir, subdir, [], ilidata_path_resolver)
        return True

    def create_projecttopping(self, project: QgsProject):
        self.project_topping.parse_project(project)

    def create_ili2dbsettings(
        self,
        configuration: Ili2DbCommandConfiguration,
        metaattr_filepath: str,
        prescript_filepath: str,
        postscript_filepath: str,
    ):
        self.metaconfig.parse_ili2db_settings(configuration)
        self.metaattr_filepath = metaattr_filepath
        self.prescript_filepath = prescript_filepath
        self.postscript_filepath = postscript_filepath

    def generate(self):
        # generate layer topping files (including projecttopping (tree, order) file)
        projecttopping_id = self.project_topping.generate_files(self.target)

        # generate referencedata toppingfiles
        referencedata_ids = ",".join(
            [self.generate_toppingfile(path) for path in self.referencedata_paths]
        )

        # generate toppingfiles used for ili2db
        metaattr_id = self.generate_toppingfile(self.metaattr_filepath)
        prescript_id = self.generate_toppingfile(self.prescript_filepath)
        postscript_id = self.generate_toppingfile(self.postscript_filepath)

        # update metaconfig with toppingfile ids
        self.metaconfig.update_configuration_settings(
            "qgis.modelbaker.projecttopping", projecttopping_id
        )
        self.metaconfig.update_configuration_settings(
            "ch.interlis.referenceData", referencedata_ids
        )
        self.metaconfig.update_ili2db_settings("iliMetaAttrs", metaattr_id)
        self.metaconfig.update_ili2db_settings("preScript", prescript_id)
        self.metaconfig.update_ili2db_settings("postScript", postscript_id)

        # generate metaconfig file
        self.metaconfig.generate_file(self.target)

        # generate ilidata.xml
        self.generate_ilidataxml(self.target)

    def generate_toppingfile(self, path):
        if "ilidata:" in path or "file:" in path:
            # it's already an id pointing to somewhere, no toppingfile needs to be created
            return path
        # copy file from path to our target, and return the ilidata_pathresolved id
        return id

    def generate_ilidataxml(self, target: Target):
        return True


def ilidata_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)

    # can I access here self (member) variables from the Target?
    id = unique_id_in_target_scope(target, f"{target.projectname}.{type}_{name}_001")
    path = os.path.join(relative_filedir_path, name)
    type = type
    version = datetime.datetime.now().strftime("%Y-%m-%d")
    toppingfile = {"id": id, "path": path, "type": type, "version": version}
    # can I access here self (member) variables from the Target?
    target.toppingfileinfo_list.append(toppingfile)
    return id


def unique_id_in_target_scope(target: Target, id):
    for toppingfileinfo in target.toppingfileinfo_list:
        if "id" in toppingfileinfo and toppingfileinfo["id"] == id:
            iterator = int(id[-3:])
            iterator += 1
            id = f"{id[:-3]}{iterator:03}"
            return unique_id_in_target_scope(target, id)
    return id
