# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2015-05-20
        git sha              : :%H$
        copyright            : (C) 2015 by OPENGIS.ch
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

def classFactory(iface):
    from .qgs_project_generator import QgsProjectGeneratorPlugin
    return QgsProjectGeneratorPlugin(iface)


