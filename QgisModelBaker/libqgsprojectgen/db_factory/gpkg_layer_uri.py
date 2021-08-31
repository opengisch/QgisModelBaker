# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    30/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
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
from .layer_uri import LayerUri


class GpkgLayerUri(LayerUri):
    """Provides layer uri based on database uri (connection string) and specific information of the data source.

    This **layer uri** is used to create a Qgis layer.

    :ivar str uri: Database uri.
    """

    def __init__(self, uri):
        LayerUri.__init__(self, uri)
        self.provider = "ogr"

    def get_data_source_uri(self, record):
        data_source_uri = "{uri}|layername={table}".format(
            uri=self.uri, table=record["tablename"]
        )
        return data_source_uri
