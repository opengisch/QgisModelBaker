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

from QgisModelBaker.internal_libs.projecttopping.projecttopping import Target


class MetaConfigInfo(object):
    """
    What needs to go to the metaconfig INI file.
    - models (to scan for maybe added in metaconfig file)
    - ili2db settings (or source and uri from schema where to get it from)
    - referenceData (to upload and store in metaconfig file)
    """

    def __init__(self):
        self.models = []
        self.ili2db_settings = None
        self.reference_data = []

    def write_ini(self, target: Target, projecttopping_path: str) -> str:
        return None


class ToppingGenerator(object):
    def __init__(
        self,
        target: Target,
        metaconfig_info: MetaConfigInfo,
        projecttopping: ProjectTopping,
    ):
        self.target = target
        self.metaconfig_info = metaconfig_info
        self.projecttopping = projecttopping

    def generate(self):
        self.target.create_dirs()
        # having valid dirs here

        projecttopping_path = self.projecttopping.write_yaml(self.target)

        # having all the topping files and yaml path
        self.metaconfig_info.write_ini(self.target, projecttopping_path)

        # having the metaconfig_file
        self._write_ilidata()

    def _write_ilidata(self):
        pass
