# -*- coding: utf-8 -*-

import sqlite3
import qgis
from qgis.core import (
    qgsfunction,
    QgsExpression,
    QgsProject
)

def on_form_open(dialog, layer, feature):
    """
    Whenever the form opens, check if the get_ili2gpkg_t_id
    function already exists and add it if not.
    """

    if not hasattr(qgis, '__ili2gpkg_t_id_generator'):
        @qgsfunction(args='auto', group='custom', usesgeometry=False, register=False)
        def get_ili2gpkg_t_id(feature, parent, context):
            """
            Gets a new unique t_id for ili2gpkg created geopackages.
            The value is managed via the T_KEY_OBJECT table within the geopackage
            and is compatible with the internal counter managed by ili2gpkg for
            import and export.
            """
            layer = QgsProject.instance().mapLayer(context.variable('layer_id'))
            gpkg = layer.dataProvider().dataSourceUri().split('|')[0]
            conn = sqlite3.connect(gpkg)
            c = conn.cursor()
            c.execute('''
              SELECT
                T_Key,
                T_LastChange
              FROM T_KEY_OBJECT
              WHERE
              T_LastUniqueId = "T_Id"''')
            res = c.fetchone()

            if res:
                t_key = res[0]
                unique_id = res[1] + 1
            else:
                unique_id = 0
                c.execute('''SELECT max(T_Key)+1 FROM T_KEY_OBJECT''')
                res = c.fetchone()
                if res:
                    t_key = res[0]

                if not t_key:
                    t_key = 0

            c.execute(r'''INSERT OR REPLACE INTO T_KEY_OBJECT
              (T_Key, T_LastUniqueId, T_LastChange, T_CreateDate, T_User)
              VALUES
              (
                ?,
                ?,
                ?,
                ?,
                ''
              )''', (t_key, 'T_Id', unique_id, 'date(\'now\')'))
            conn.commit()
            conn.close()

            return unique_id


        qgis.__ili2gpkg_t_id_generator = dict()
        # Increase this if improved versions are shipped
        # and unregister the previously registered one before registering
        # the new version
        qgis.__ili2gpkg_t_id_generator['version'] = 1
        qgis.__ili2gpkg_t_id_generator['function'] = get_ili2gpkg_t_id

        QgsExpression.registerFunction(qgis.__ili2gpkg_t_id_generator['function'])
