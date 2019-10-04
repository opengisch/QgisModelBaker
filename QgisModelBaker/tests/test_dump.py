# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    24.5.2018
    git sha              :    :%H$
    copyright            :    (C) 2018 Matthias Kuhn
    email                :    matthias@opengis.ch
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

import nose2

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import testdata_path
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from qgis.testing import unittest, start_app

from subprocess import call
import os

start_app()


class TestCustomDump(unittest.TestCase):

    def test_ili2pg_dump_without_metattr(self):
        myenv = os.environ.copy()
        myenv['PGPASSWORD'] = 'docker'

        call(["psql", "-Fc", "-Fc", "-hpostgres", "-Udocker", "-dgis", "--command=CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""], env=myenv)
        call(["pg_restore", "-Fc", "-hpostgres", "-Udocker", "-dgis", testdata_path("dumps/_nupla_dump")], env=myenv)

        generator = Generator(DbIliMode.ili2pg,
                              'dbname=gis user=docker password=docker host=postgres',
                              'smart1',
                              '_nupla')

        available_layers = generator.layers()

        self.assertEqual(len(available_layers), 15)


if __name__ == '__main__':
    nose2.main()
