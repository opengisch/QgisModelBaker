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


class PgUri(DbUri):

    def get_uri_from_conf(self, configuration, su=False):
        uri = []

        uri += ['dbname={}'.format(configuration.database)]
        if su:
            uri += ['user={}'.format(configuration.base_configuration.super_pg_user)]
            if configuration.base_configuration.super_pg_password:
                uri += ['password={}'.format(configuration.base_configuration.super_pg_password)]
        else:
            uri += ['user={}'.format(configuration.dbusr)]
            if configuration.dbpwd:
                uri += ['password={}'.format(configuration.dbpwd)]
        uri += ['host={}'.format(configuration.dbhost)]
        if configuration.dbport:
            uri += ['port={}'.format(configuration.dbport)]

        return ' '.join(uri)

    def get_db_args_from_conf(self, configuration, hide_password=False):
        db_args = list()
        db_args += ["--dbhost", configuration.dbhost]
        if configuration.dbport:
            db_args += ["--dbport", configuration.dbport]
        db_args += ["--dbusr", configuration.dbusr]
        if configuration.dbpwd:
            if hide_password:
                db_args += ["--dbpwd", '******']
            else:
                db_args += ["--dbpwd", configuration.dbpwd]
        db_args += ["--dbdatabase", configuration.database.strip("'")]
        db_args += ["--dbschema",
                 configuration.dbschema or configuration.database]
        return db_args
