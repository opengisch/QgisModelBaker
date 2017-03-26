# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2016-12-21
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
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


class LegendGroup(object):

    def __init__(self, name=None, items=list()):
        self.name = name
        self.items = items

    def dump(self):
        definition = list()
        for item in self.items:
            definition.append(item.dump())
        return definition

    def load(self, definition):
        pass

    def create(self):
        pass
