# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    09/05/19
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
from .layer_uri import LayerUri


class MssqlLayerUri(LayerUri):
    def __init__(self, uri):
        LayerUri.__init__(self, uri)
        self.provider = "mssql"

    def get_data_source_uri(self, record):
        if record["geometry_column"]:
            data_source_uri = '{uri} key={primary_key} estimatedmetadata=true srid={srid} type={type} table="{schema}"."{table}" ({geometry_column}) sql='.format(
                uri=self._get_layer_uri_common(),
                primary_key=record["primary_key"],
                srid=record["srid"],
                type=record["type"],
                schema=record["schemaname"],
                table=record["tablename"],
                geometry_column=record["geometry_column"],
            )
        else:
            data_source_uri = '{uri} key={primary_key} estimatedmetadata=true srid=0 table="{schema}"."{table}" sql='.format(
                uri=self._get_layer_uri_common(),
                primary_key=record["primary_key"],
                schema=record["schemaname"],
                table=record["tablename"],
            )

        return data_source_uri

    def _get_layer_uri_common(self):
        param_db = dict()
        lst_item = self.uri.split(";")
        for item in lst_item:
            key_value = item.split("=")
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                param_db[key] = value

        uri = "service='driver={drv}' dbname='{database}' host={server} user='{uid}' password='{pwd}' ".format(
            drv=param_db["DRIVER"],
            database=param_db["DATABASE"],
            server=param_db["SERVER"],
            uid=param_db["UID"],
            pwd=param_db["PWD"],
        )

        return uri
