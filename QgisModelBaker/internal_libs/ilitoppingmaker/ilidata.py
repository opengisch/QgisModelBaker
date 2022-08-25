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

import mimetypes
import os
import uuid
import xml.dom.minidom as minidom
import xml.etree.cElementTree as ET

from .ilitarget import IliTarget


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

    def generate_file(self, target: IliTarget, linking_models: list = []):
        transfer = ET.Element("TRANSFER", xmlns="http://www.interlis.ch/INTERLIS2.3")

        headersection = ET.SubElement(
            transfer,
            "HEADERSECTION",
            SENDER="ModelBaker IliProjectTopping",
            VERSION="2.3",
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
                toppingfileinfo.get("version", target.default_version),
                toppingfileinfo.get("publishing_date", target.default_publishing_date),
                toppingfileinfo.get("owner", target.default_owner),
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
