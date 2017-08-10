# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 09/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

try:
    import os
    import qgis
    import nose2

    from projectgenerator.libqgsprojectgen.dataobjects import Project
    from qgis.testing import unittest, start_app
    from qgis.core import QgsProject, QgsEditFormConfig
    from projectgenerator.libqgsprojectgen.generator.postgres import Generator

    start_app()
except ImportError:
    # As long as we don't deploy qgis on travis, there's nothing we can do... sorry
    from nose2.compat import unittest
    pass


class TestProjectGen(unittest.TestCase):
    @unittest.skipIf('TRAVIS' in os.environ, 'Enable this test as soon as qgis is available on travis')
    def test_kbs(self):
        generator = Generator('dbname=interlis user=mkuhn host=localhost', 'kbs22', 'smart1')

        available_layers = generator.layers()
        relations = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.table_name == 'belasteter_standort' and layer.geometry_column == 'geo_lage_punkt':
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                self.assertEqual(edit_form_config.layout(), QgsEditFormConfig.TabLayout)
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                self.assertEqual(fields, set(['Katasternummer',
                                              'URL_Standort',
                                              'Standorttyp',
                                              'InBetrieb',
                                              'Nachsorge',
                                              'StatusAltlV',
                                              'Ersteintrag',
                                              'LetzteAnpassung',
                                              'URL_KbS_Auszug',
                                              'bemerkung',
                                              'bemerkung_de',
                                              'bemerkung_fr',
                                              'bemerkung_rm',
                                              'bemerkung_it',
                                              'bemerkung_en',
                                              'zustaendigkeitkataster',
                                              'Geo_Lage_Polygon',
                                              'Geo_Lage_Punkt']))

                self.assertEqual(tabs[1].name(), 'zustaendigkeitkataster') # This might need to be adjustet if we get better names

        self.assertEqual(count, 1)
        self.assertEqual(len(available_layers), 16)


if __name__ == '__main__':
    nose2.main()
