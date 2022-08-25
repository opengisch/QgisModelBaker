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


class Ili2dbSettings(dict):
    def __init__(self):
        self.parameters = {}
        self.metaattr_path = None
        self.postscript_path = None
        self.prescript_path = None
        self.models = []

    def parse_parameters_from_db(self, db_connector):
        """
        We do only care about the settings "known" by model baker (set by user in GUI or by modelbaker in the background).
        And we set them when they are set (and do not unset them when they are not set).
        """

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
