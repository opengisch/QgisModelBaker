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


class Ili2gpkgArgs(IliArgs):

    def get_db_args_from_conf(self, configuration, hide_password=False):
        return ["--dbfile", configuration.dbfile]

    def get_schema_import_args(self):
        return list()
