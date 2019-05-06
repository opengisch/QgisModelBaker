# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    25/04/19
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
from .db_uri import DbUri


class GpkgUri(DbUri):

    def get_uri_from_conf(self, configuration, su=False):
        return configuration.dbfile

    def get_db_args_from_conf(self, configuration, hide_password=False):
        return ["--dbfile", configuration.dbfile]

    def get_specific_params_schema_import(self):
        return list()
