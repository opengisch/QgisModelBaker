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

import os
from subprocess import call

from qgis.testing import start_app, unittest

from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.tests.utils import get_pg_connection_string, testdata_path

start_app()


class TestCustomDump(unittest.TestCase):
    def test_ili2db3_ili2pg_dump_without_metattr(self):
        myenv = os.environ.copy()
        myenv["PGPASSWORD"] = "docker"
        call(
            [
                "pg_restore",
                "-Fc",
                "-h" + os.environ["PGHOST"],
                "-Udocker",
                "-dgis",
                testdata_path("dumps/_nupla_dump"),
            ],
            env=myenv,
        )

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), "smart1", "_nupla"
        )

        available_layers = generator.layers()

        assert len(available_layers) == 15

    def test_ili2pg_dump_without_metattr(self):
        myenv = os.environ.copy()
        myenv["PGPASSWORD"] = "docker"
        call(
            [
                "psql",
                "-Fc",
                "-Fc",
                "-h" + os.environ["PGHOST"],
                "-Udocker",
                "-dgis",
                '--command=CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
            ],
            env=myenv,
        )
        call(
            [
                "pg_restore",
                "-Fc",
                "-h" + os.environ["PGHOST"],
                "-Udocker",
                "-dgis",
                testdata_path("dumps/_nupla_ili2db4_dump"),
            ],
            env=myenv,
        )

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), "smart1", "_nupla_ili2db4"
        )

        available_layers = generator.layers()

        assert len(available_layers) == 15
