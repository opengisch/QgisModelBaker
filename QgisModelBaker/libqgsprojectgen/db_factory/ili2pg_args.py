# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    06/05/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania (BSF Swissphoto)
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
from abc import ABC, abstractmethod
from .ili_args import IliArgs


class Ili2pgArgs(IliArgs):
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

    def get_schema_import_args(self):
        args = list()
        args += ["--setupPgExt"]
        return args

