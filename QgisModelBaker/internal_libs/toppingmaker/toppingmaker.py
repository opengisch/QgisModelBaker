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
import mimetypes
import os
import uuid
import xml.dom.minidom as minidom
import xml.etree.cElementTree as ET

from qgis.core import QgsDataSourceUri, QgsMapLayer, QgsProject

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

from .utils import slugify


class IliData(object):
    class DatasetMetadata(object):
        def __init__(
            self,
            dataset_version: str = None,
            publishing_date: str = None,
            owner: str = None,
            project_name: str = None,
            id: str = None,
            file_type: str = None,
            file_path: str = None,
            linking_models: list = [],
        ):
            self.id = id
            self.file_type = file_type
            self.file_path = file_path
            self.linking_models = linking_models

            self.version = dataset_version
            self.publishing_date = publishing_date
            self.owner = owner
            self.project_name = project_name

            self.title = f"QGIS {self.file_type} file for {self.project_name} - {os.path.splitext(os.path.basename(self.file_path))}"
            self.file_mimetype = self._file_mime_type(self.file_path)

        def _file_mime_type(self, file_path: str = None) -> str:
            mimetype = mimetypes.guess_type(file_path)
            if mimetype[0] is None:
                # ugly fallback
                return "text/plain"
            return mimetype[0]

        def make_xml_element(self, element):

            ET.SubElement(element, "id").text = self.id
            ET.SubElement(element, "version").text = self.version
            ET.SubElement(element, "publishingDate").text = self.publishing_date
            ET.SubElement(element, "owner").text = self.owner

            title = ET.SubElement(element, "title")
            datsetidx16_multilingualtext = ET.SubElement(
                title, "DatasetIdx16.MultilingualText"
            )
            localisedtext = ET.SubElement(datsetidx16_multilingualtext, "LocalisedText")
            datasetidx16_localisedtext = ET.SubElement(
                localisedtext, "DatasetIdx16.LocalisedText"
            )
            ET.SubElement(datasetidx16_localisedtext, "Text").text = self.title

            categories = ET.SubElement(element, "categories")
            type_datasetidx16_code = ET.SubElement(categories, "DatasetIdx16.Code_")
            ET.SubElement(
                type_datasetidx16_code, "value"
            ).text = f"http://codes.interlis.ch/type/{self.file_type}"

            if self.file_type in ["metaconfig", "referencedata"]:
                for linking_model in self.linking_models:
                    linking_model_datasetidx16_code = ET.SubElement(
                        categories, "DatasetIdx16.Code_"
                    )
                    ET.SubElement(
                        linking_model_datasetidx16_code, "value"
                    ).text = f"http://codes.interlis.ch/model/{linking_model}"

            files = ET.SubElement(element, "files")
            datsaetidx16_datafile = ET.SubElement(files, "DatasetIdx16.DataFile")
            ET.SubElement(datsaetidx16_datafile, "fileFormat").text = self.file_mimetype
            file = ET.SubElement(datsaetidx16_datafile, "file")
            datsetidx16_file = ET.SubElement(file, "DatasetIdx16.File")
            ET.SubElement(datsetidx16_file, "path").text = self.file_path

    def __init__(self):
        pass

    def generate_file(self, target: Target, linking_models: list = []):
        # - [ ] publishing_date
        # - [ ] owner
        transfer = ET.Element("TRANSFER", xmlns="http://www.interlis.ch/INTERLIS2.3")

        headersection = ET.SubElement(
            transfer, "HEADERSECTION", SENDER="ModelBaker ToppingMaker", VERSION="2.3"
        )
        models = ET.SubElement(headersection, "MODELS")
        ET.SubElement(
            models,
            "MODEL",
            NAME="DatasetIdx16",
            VERSION="2018-11-21",
            URI="mailto:ce@eisenhutinformatik.ch",
        )

        datasection = ET.SubElement(transfer, "DATASECTION")
        data_index = ET.SubElement(
            datasection, "DatasetIdx16.DataIndex", BID=str(uuid.uuid4())
        )

        for toppingfileinfo in target.toppingfileinfo_list:
            dataset_metadata_element = ET.SubElement(
                data_index,
                "DatasetIdx16.DataIndex.DatasetMetadata",
                TID=str(uuid.uuid4()),
            )
            dataset = IliData.DatasetMetadata(
                toppingfileinfo["version"],
                "publishing_date",
                "owner",
                target.projectname,
                toppingfileinfo["id"],
                toppingfileinfo["type"],
                toppingfileinfo["path"],
                linking_models,
            )
            dataset.make_xml_element(dataset_metadata_element)

        tree = ET.ElementTree(transfer)
        xmlstr = minidom.parseString(ET.tostring(tree.getroot())).toprettyxml(
            indent="   "
        )
        ilidata_path = os.path.join(target.main_dir, "ilidata.xml")
        with open(ilidata_path, "w") as f:
            f.write(xmlstr)
            return ilidata_path


class MetaConfig(object):

    METACONFIG_TYPE = "metaconfig"

    def __init__(self):
        # generated sections
        # configuration_section["ch.interlis.referenceData"] = ...
        # configuration_section["qgis.modelbaker.projecttopping"] = ...
        self.configuration_section = {}
        # ili2db configuration - toml and sql files should be appended as topping
        self.ili2db_section = {}

    def parse_ili2db_settings(
        self, configuration: Ili2DbCommandConfiguration = Ili2DbCommandConfiguration()
    ):
        # - [ ] To Do: go into db (according configuration) and read the settings and map them to this section
        db_settings = {}

        self.ili2db_section.update(db_settings)
        return True

    def update_ili2db_settings(self, key: str, value: str):
        self.ili2db_section[key] = value

    def update_configuration_settings(self, key: str, value: str):
        self.configuration_section[key] = value

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
        metaconfig["CONFIGURATION"] = self.configuration_section
        metaconfig["ch.ehi.ili2db"] = self.ili2db_section

        # write file
        metaconfig_slug = f"{slugify(target.projectname)}.ini"
        absolute_filedir_path, relative_filedir_path = target.filedir_path(
            MetaConfig.METACONFIG_TYPE
        )

        with open(
            os.path.join(absolute_filedir_path, metaconfig_slug), "w"
        ) as configfile:
            output = metaconfig.write(configfile)
            print(output)

        return target.path_resolver(target, metaconfig_slug, MetaConfig.METACONFIG_TYPE)


class ToppingMaker(object):
    """
    To create a "Topping" used for INTERLIS projects having artefacts like ilidata, metaconfigfile (ini) etc.

    - [ ] Maybe rename it to IliToppingMaker to clearify it's purpose
    - Gateway to backend library ProjectTopping (by passing ili-specific path_resolver etc.)
    - [ ] MetaConfig generator
    - [ ] ilidata-File generator
    """

    REFERENCEDATA_TYPE = "referencedata"
    METAATTR_TYPE = "metaattributes"
    SQLSCRIPT_TYPE = "sql"

    def __init__(
        self,
        projectname: str = None,
        maindir: str = None,
        subdir: str = None,
        export_settings: ExportSettings = ExportSettings(),
        referencedata_paths: list = [],
    ):
        # ProjectTopping objects for the basic topping creation
        self.target = Target(projectname, maindir, subdir, ilidata_path_resolver)
        self.export_settings = export_settings
        self.project_topping = ProjectTopping()

        # ToppingMaker objects used for the ili specific topping creation / maybe the path can be moved to MetaConfig
        self.metaconfig = MetaConfig()
        self.referencedata_paths = referencedata_paths
        self.metaattr_filepath = None
        self.prescript_filepath = None
        self.postscript_filepath = None

        # - [ ] should the model be in the toppingmaker or should it preferly only act as library used without gui
        self.models_model = SchemaModelsModel()

    @property
    def models(self):
        return self.models_model.checked_entries()

    def create_target(self, projectname, maindir, subdir):
        """
        Creates and sets the target of this ToppingMaker with the ili specific path resolver.
        And overrides target created in constructor.
        """
        self.target = Target(projectname, maindir, subdir, ilidata_path_resolver)
        return True

    def create_projecttopping(self, project: QgsProject):
        """
        Creates and sets the project_topping considering the passed QgsProject and the existing ExportSettings set in the constructor or directly.
        """
        return self.project_topping.parse_project(project, self.export_settings)

    def create_ili2dbsettings(
        self, configuration: Ili2DbCommandConfiguration = Ili2DbCommandConfiguration()
    ):
        """
        Parses in the metaconfig the db accordingly the configuration for available ili2db settings.
        """
        return self.metaconfig.parse_ili2db_settings(configuration)

    def generate_projecttoppingfiles(self):
        """
        Generates topping files (layertree and depending files like style etc) considering existing ProjectTopping and Target.
        Returns the ilidata id (according to path_resolver of Target) of the projecttopping file.
        """
        return self.project_topping.generate_files(self.target)

    def generate_toppingfile_link(self, target: Target, type, path):
        if "ilidata:" in path or "file:" in path:
            # it's already an id pointing to somewhere, no toppingfile needs to be created
            return path
        # copy file from path to our target, and return the ilidata_pathresolved id
        return self.project_topping.toppingfile_link(target, type, path)

    def generate_ilidataxml(self, target: Target):
        # generate ilidata.xml
        ilidata = IliData()
        return ilidata.generate_file(target, self.models)

    def bakedycakedy(self, project: QgsProject = None, configuration=None):
        # - [ ] Provide possiblity to pass here all the data
        if project:
            # project passed here, so we parse it and override the current ProjectTopping
            self.create_projecttopping(project)
        if configuration:
            # configuration passed here, so we parse it and update the current ili2dbsection of MetaConfig
            self.create_ili2dbsettings(configuration)

        # generate toppingfiles of ProjectTopping
        projecttopping_id = self.generate_projecttoppingfiles()

        # generate toppingfiles of the reference data
        referencedata_ids = ",".join(
            [
                self.generate_toppingfile_link(
                    self.target, ToppingMaker.REFERENCEDATA_TYPE, path
                )
                for path in self.referencedata_paths
            ]
        )

        # - [ ] maybe the whole metaconfig part can go to metaconfig. So there is no big logic in this function. But let's see.
        # update MetaConfig with toppingfile ids
        self.metaconfig.update_configuration_settings(
            "qgis.modelbaker.projecttopping", projecttopping_id
        )
        self.metaconfig.update_configuration_settings(
            "ch.interlis.referenceData", referencedata_ids
        )

        # generate toppingfiles used for ili2db
        if self.metaattr_filepath:
            self.metaconfig.update_ili2db_settings(
                "iliMetaAttrs",
                self.generate_toppingfile_link(
                    self.target, ToppingMaker.METAATTR_TYPE, self.metaattr_filepath
                ),
            )
        if self.prescript_filepath:
            self.metaconfig.update_ili2db_settings(
                "preScript",
                self.generate_toppingfile_link(
                    self.target, ToppingMaker.SQLSCRIPT_TYPE, self.prescript_filepath
                ),
            )
        if self.postscript_filepath:
            self.metaconfig.update_ili2db_settings(
                "postScript",
                self.generate_toppingfile_link(
                    self.target, ToppingMaker.SQLSCRIPT_TYPE, self.postscript_filepath
                ),
            )

        # generate metaconfig (topping) file
        self.metaconfig.generate_file(self.target)

        # generate ilidata
        return self.generate_ilidataxml(self.target)

    """
    Providing info
    """

    def load_available_models(self, project: QgsProject):
        """
        Collects all the available sources in the project and makes the models_model to refresh accordingly.
        """
        checked_identificators = []
        db_connectors = []
        for layer in project.mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
                schema_identificator = (
                    db_utils.get_schema_identificator_from_layersource(
                        source_provider, source
                    )
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


"""
Path resolver function
- [ ] should maybe be part of a class (like ToppingMaker)
"""


def ilidata_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)

    # - [ ] toppingfileinfo_list wird irgendwie doppelt am ende (jeder eintrag des toppings 2 mal)
    # can I access here self (member) variables from the Target?
    id = unique_id_in_target_scope(
        target, slugify(f"{target.projectname}.{type}_{name}_001")
    )
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
