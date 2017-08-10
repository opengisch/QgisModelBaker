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
    from projectgenerator.qgs_project_generator import QgsProjectGeneratorPlugin
except ImportError as e:
    # As long as we don't deploy qgis on travis, there's nothing we can do... sorry
    if not 'TRAVIS' in os.environ:
        raise e
