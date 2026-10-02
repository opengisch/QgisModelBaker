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
import os
import sys

# add libs path to be able to use libraries with absolute paths in the modelbaker package
_libs_dir = os.path.join(os.path.dirname(__file__), "libs")
_modelbaker_libs_dir = os.path.join(_libs_dir, "modelbaker", "libs")
for _path in (_modelbaker_libs_dir, _libs_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def classFactory(iface):
    from .qgismodelbaker import QgisModelBakerPlugin

    return QgisModelBakerPlugin(iface)
