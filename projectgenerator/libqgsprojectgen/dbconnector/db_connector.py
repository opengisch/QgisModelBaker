# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo
    email                :    gcarrillo@linuxmail.org
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
class DBConnector:
    """SuperClass for all DB connectors."""
    def __init__(self, uri, schema):
        pass

    def metadata_exists(self):
        return False

    def get_tables_info(self):
        return {}

    def get_fields_info(self, table_name):
        return {}

    def get_constraints_info(self, table_name):
        return {}

    def get_relations_info(self):
        return {}

    def get_domainili_domaindb_mapping(self):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_models(self):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_attrili_attrdb_mapping(self, models_info_with_ext):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}
