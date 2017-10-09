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

    def get_fields_info(self):
        return {}

    def get_constraints_info(self):
        return {}

    def get_relations_info(self):
        return {}
