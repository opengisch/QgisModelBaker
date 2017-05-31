# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo
        email                : gcarrillo@linuxmail.org
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
from qgis.PyQt.QtCore import QObject

ILI2PG_VERSION = '3.8.1'
ILI2PG_URL = 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(ILI2PG_VERSION)


class ImportConfiguration(object):
    def __init__(self):
        self.host = ''
        self.user = ''
        self.database = ''
        self.schema = ''
        self.password = ''
        self.ilifile = ''
        self.port = ''
        self.inheritance = 'smart1'
        self.epsg = 21781  # Default EPSG code in ili2pg

    @property
    def uri(self):
        uri = []
        uri += ['dbname={}'.format(self.database)]
        uri += ['user={}'.format(self.user)]
        if self.password:
            uri += ['password={}'.format(self.password)]
        uri += ['host={}'.format(self.host)]
        if self.port:
            uri += ['port={}'.format(self.port)]

        return ' '.join(uri)


class ExportConfiguration(object):
    def __init__(self):
        self.host = ''
        self.user = ''
        self.database = ''
        self.schema = ''
        self.password = ''
        self.xtffile = ''
        self.ilifolder = ''
        self.ilimodels = ''
        self.port = ''


class JavaNotFoundError(FileNotFoundError):
    pass

