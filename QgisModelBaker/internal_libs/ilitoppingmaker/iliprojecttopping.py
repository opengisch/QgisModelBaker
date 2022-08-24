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

import datetime
import os

from qgis.core import QgsProject

from QgisModelBaker.internal_libs.toppingmaker import (
    ExportSettings,
    ProjectTopping,
    Target,
)
from QgisModelBaker.internal_libs.toppingmaker.utils import slugify

from .ilidata import IliData
from .metaconfig import MetaConfig


class IliProjectTopping(ProjectTopping):
    """
    To create a "Topping" used for INTERLIS projects having artefacts like ilidata, metaconfigfile (ini) etc.

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
        super().__init__()
        # should those be set in ProjectTopping?
        self.target = Target(projectname, maindir, subdir, ilidata_path_resolver)
        self.export_settings = export_settings

        self.metaconfig = MetaConfig()

    @property
    def models(self):
        return self.metaconfig.ili2db_settings.models

    def set_models(self, models: list = []):
        self.metaconfig.ili2db_settings.models = models

    def set_referencedata_paths(self, paths: list = []):
        self.metaconfig.referencedata_paths = paths

    def create_target(self, projectname, maindir, subdir):
        """
        Creates and sets the target of this IliProjectTopping with the ili specific path resolver.
        And overrides target created in constructor.
        """
        self.target = Target(projectname, maindir, subdir, ilidata_path_resolver)
        return True

    def create_projecttopping(self, project: QgsProject):
        """
        Creates and sets the project_topping considering the passed QgsProject and the existing ExportSettings set in the constructor or directly.
        """
        return self.parse_project(project, self.export_settings)

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
        return self.generate_files(self.target)

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
- [ ] should maybe be part of a class (like IliProjectTopping)
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
