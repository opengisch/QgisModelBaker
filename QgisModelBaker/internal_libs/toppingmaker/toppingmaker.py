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
from typing import Union

from qgis.core import QgsProject

from QgisModelBaker.internal_libs.projecttopping.projecttopping import (
    ExportSettings,
    ProjectTopping,
    Target,
    toppingfile_link,
)

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


class Ili2dbSettings(dict):
    def __init__(self):
        self.parameters = {}
        self.metaattr_path = None
        self.postscript_path = None
        self.prescript_path = None
        self.models = []

    def parse_parameters_from_db(self, db_connector):
        # we do currently only care about the settings "known" by model baker (set by user in GUI or by modelbaker in the background)
        # and we set them when they are set (and do not unset them when they are not set)
        setting_records = db_connector.get_ili2db_settings()
        settings_dict = {}
        self.parameters = {}
        for setting_record in setting_records:
            settings_dict[setting_record["tag"]] = setting_record["setting"]
        # user settings
        if settings_dict.get("ch.ehi.ili2db.inheritanceTrafo", None) == "smart1":
            self.parameters["smart1Inheritance"] = True
        if settings_dict.get("ch.ehi.ili2db.inheritanceTrafo", None) == "smart2":
            self.parameters["smart2Inheritance"] = True
        if settings_dict.get("ch.ehi.ili2db.StrokeArcs", None) == "enable":
            self.parameters["strokeArcs"] = True
        if settings_dict.get("ch.ehi.ili2db.BasketHandling", None) == "readWrite":
            self.parameters["createBasketCol"] = True
        if settings_dict.get("ch.ehi.ili2db.defaultSrsAuthority", None):
            self.parameters["defaultSrsAuth"] = settings_dict[
                "ch.ehi.ili2db.defaultSrsAuthority"
            ]
        if settings_dict.get("ch.ehi.ili2db.StrokedefaultSrsCodeArcs", None):
            self.parameters["defaultSrsCode"] = settings_dict[
                "ch.ehi.ili2db.defaultSrsCode"
            ]

        # modelbaker default settings
        if settings_dict.get("ch.ehi.ili2db.catalogueRefTrafo", None) == "coalesce":
            self.parameters["coalesceCatalogueRef"] = True
        if (
            settings_dict.get("ch.ehi.ili2db.createEnumDefs", None)
            == "multiTableWithId"
        ):
            self.parameters["createEnumTabsWithId"] = True
        if settings_dict.get("ch.ehi.ili2db.numericCheckConstraints", None) == "create":
            self.parameters["createNumChecks"] = True
        if settings_dict.get("ch.ehi.ili2db.uniqueConstraints", None) == "create":
            self.parameters["createUnique"] = True
        if settings_dict.get("ch.ehi.ili2db.createForeignKey", None) == "yes":
            self.parameters["createFk"] = True
        if settings_dict.get("ch.ehi.ili2db.createForeignKeyIndex", None) == "yes":
            self.parameters["createFkIdx"] = True
        if settings_dict.get("ch.ehi.ili2db.multiSurfaceTrafo", None) == "coalesce":
            self.parameters["coalesceMultiSurface"] = True
        if settings_dict.get("ch.ehi.ili2db.multiLineTrafo", None) == "coalesce":
            self.parameters["coalesceMultiLine"] = True
        if settings_dict.get("ch.ehi.ili2db.multiPointTrafo", None) == "coalesce":
            self.parameters["coalesceMultiPoint"] = True
        if settings_dict.get("ch.ehi.ili2db.arrayTrafo", None) == "coalesce":
            self.parameters["coalesceArray"] = True
        if (
            settings_dict.get("ch.ehi.ili2db.beautifyEnumDispName", None)
            == "underscore"
        ):
            self.parameters["beautifyEnumDispName"] = True
        if settings_dict.get("ch.ehi.sqlgen.createGeomIndex", None) == "underscore":
            self.parameters["createGeomIdx"] = True
        if settings_dict.get("ch.ehi.ili2db.createMetaInfo", None):
            self.parameters["createMetaInfo"] = True
        if settings_dict.get("ch.ehi.ili2db.multilingualTrafo", None) == "expand":
            self.parameters["expandMultilingual"] = True
        if settings_dict.get("ch.ehi.ili2db.createTypeConstraint", None):
            self.parameters["createTypeConstraint"] = True
        if settings_dict.get("ch.ehi.ili2db.TidHandling", None) == "property":
            self.parameters["createTidCol"] = True

        return True


class MetaConfig(object):

    METACONFIG_TYPE = "metaconfig"

    def __init__(self):
        # generated sections
        # configuration_section["ch.interlis.referenceData"] = ...
        # configuration_section["qgis.modelbaker.projecttopping"] = ...
        self.referencedata_paths = []
        self.projecttopping_path = None
        # ili2db configuration - toml and sql files should be appended as topping
        self.ili2db_settings = Ili2dbSettings()

    def update_referencedata_paths(self, value: Union[list, bool]):
        if isinstance(value, str):
            value = [value]
        self.referencedata_paths.extend(value)

    def update_projecttopping_path(self, value: str):
        self.projecttopping_path = value

    def generate_files(self, target: Target):
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

        configuration_section = {}

        # append project topping and reference data links
        if self.projecttopping_path:
            # generate toppingfile of projettopping (most possibly already an id, so no generation needed)
            projecttopping_link = self._generate_toppingfile_link(
                target, ProjectTopping.PROJECTTOPPING_TYPE, self.projecttopping_path
            )
            configuration_section[
                "qgis.modelbaker.projecttopping"
            ] = f"ilidata:{projecttopping_link}"

        if self.referencedata_paths:
            # generate toppingfiles of the reference data
            referencedata_links = ",".join(
                [
                    f"ilidata:{self._generate_toppingfile_link(target, ToppingMaker.REFERENCEDATA_TYPE, path)}"
                    for path in self.referencedata_paths
                ]
            )
            configuration_section["ch.interlis.referenceData"] = referencedata_links

        ili2db_section = {}

        # append models and the ili2db parameters
        ili2db_section["models"] = ",".join(self.ili2db_settings.models)
        ili2db_section.update(self.ili2db_settings.parameters)

        # generate metaattr and prescript / postscript files
        if self.ili2db_settings.metaattr_path:
            ili2db_section[
                "iliMetaAttrs"
            ] = f"ilidata:{self._generate_toppingfile_link(target, ToppingMaker.METAATTR_TYPE, self.ili2db_settings.metaattr_path)}"
        if self.ili2db_settings.prescript_path:
            ili2db_section[
                "preScript"
            ] = f"ilidata:{self._generate_toppingfile_link(target, ToppingMaker.SQLSCRIPT_TYPE, self.ili2db_settings.prescript_path)}"
        if self.ili2db_settings.postscript_path:
            ili2db_section[
                "postScript"
            ] = f"ilidata:{self._generate_toppingfile_link(target, ToppingMaker.SQLSCRIPT_TYPE, self.ili2db_settings.postscript_path)}"

        # make the full conifg
        metaconfig = configparser.ConfigParser()
        metaconfig["CONFIGURATION"] = configuration_section
        metaconfig["ch.ehi.ili2db"] = ili2db_section

        # write INI file
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

    def _generate_toppingfile_link(self, target: Target, type, path):
        if not os.path.isfile(path):
            # it's already an id pointing to somewhere, no toppingfile needs to be created
            return path
        # copy file from path to our target, and return the ilidata_pathresolved id
        return toppingfile_link(target, type, path)


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
        # setting objects
        self.target = Target(projectname, maindir, subdir, ilidata_path_resolver)
        self.export_settings = export_settings
        self.metaconfig = MetaConfig()
        self.project_topping = ProjectTopping()

    @property
    def models(self):
        return self.metaconfig.ili2db_settings.models

    def set_models(self, models: list = []):
        self.metaconfig.ili2db_settings.models = models

    def set_referencedata_paths(self, paths: list = []):
        self.metaconfig.referencedata_paths = paths

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

    def create_ili2dbsettings(self, configuration):
        """
        Parses in the metaconfig the db accordingly the configuration for available ili2db settings.
        """
        # needs to get the db:connector and load everything maybe... let's see return self.metaconfig.parse_ili2db_settings_from_db(db_connector)
        return True

    def generate_projecttoppingfiles(self):
        """
        Generates topping files (layertree and depending files like style etc) considering existing ProjectTopping and Target.
        Returns the ilidata id (according to path_resolver of Target) of the projecttopping file.
        """
        return self.project_topping.generate_files(self.target)

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
            # configuration passed here, so we parse it
            # maybe be able to add here referencedata and metaattr and sql etc.
            self.create_ili2dbsettings(configuration)

        # generate toppingfiles of ProjectTopping
        projecttopping_id = self.generate_projecttoppingfiles()

        # update metaconfig object
        self.metaconfig.update_projecttopping_path(projecttopping_id)

        # generate metaconfig (topping) file
        self.metaconfig.generate_files(self.target)

        # generate ilidata
        return self.generate_ilidataxml(self.target)


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
