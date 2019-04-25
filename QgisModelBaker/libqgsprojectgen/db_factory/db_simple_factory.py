# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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
from .pg_factory import PgFactory
from .gpkg_factory import GpkgFactory


class DbSimpleFactory:

    def create_factory(self, ili_mode):
        result = None

        if ili_mode == 'pg' or ili_mode == 'ili2pg':
            result = PgFactory()
        elif ili_mode == 'gpkg' or ili_mode == 'ili2gpkg':
            result = GpkgFactory()

        return result

    def get_db_list(self, is_schema_import=False):
        result = ['pg', 'gpkg']
        if is_schema_import:
            result = ['ili2pg', 'ili2gpkg', 'pg', 'gpkg']
        return result

    def get_db_id(self, ili_mode):
        lst_db_item = dict()
        lst_db_item['ili2pg'] = 'pg'
        lst_db_item['ili2gpkg'] = 'gpkg'
        lst_db_item['pg'] = 'pg'
        lst_db_item['gpkg'] = 'gpkg'

        return lst_db_item[ili_mode]

    def db_display(self, ili_mode):
        lst_name_display = dict()
        lst_name_display['ili2pg'] = 'Interlis (use PostGIS)'
        lst_name_display['ili2gpkg'] = 'Interlis (use GeoPackage)'
        lst_name_display['pg'] = 'PostGIS'
        lst_name_display['gpkg'] = 'GeoPackage'

        return lst_name_display[ili_mode]

    def is_interlis_mode(self, ili_mode):
        prefix = 'ili'

        index = ili_mode.find(prefix)

        return index == 0
