# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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
import errno
import os
import re
import sqlite3
import uuid

import qgis.utils
from qgis.core import Qgis

from ..generator.config import GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX
from .db_connector import DBConnector, DBConnectorError

GPKG_METADATA_TABLE = "T_ILI2DB_TABLE_PROP"
GPKG_METAATTRS_TABLE = "T_ILI2DB_META_ATTRS"
GPKG_SETTINGS_TABLE = "T_ILI2DB_SETTINGS"
GPKG_DATASET_TABLE = "T_ILI2DB_DATASET"
GPKG_BASKET_TABLE = "T_ILI2DB_BASKET"


class GPKGConnector(DBConnector):
    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)

        if not os.path.isfile(uri):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), uri)

        try:
            self.conn = qgis.utils.spatialite_connect(uri)
        except sqlite3.Error as e:
            raise DBConnectorError(str(e), e)

        self.conn.row_factory = sqlite3.Row
        self.uri = uri
        self._bMetadataTable = self._metadata_exists()
        self._tables_info = self._get_tables_info()
        self.iliCodeName = "iliCode"
        self.tid = "T_Id"
        self.tilitid = "T_Ili_Tid"
        self.dispName = "dispName"
        self.basket_table_name = GPKG_BASKET_TABLE
        self.dataset_table_name = GPKG_DATASET_TABLE

    def map_data_types(self, data_type):
        """GPKG date/time types correspond to QGIS date/time types"""
        return data_type.lower()

    def db_or_schema_exists(self):
        return os.path.isfile(self.uri)

    def create_db_or_schema(self, usr):
        """Create the DB (for GPKG)."""
        raise NotImplementedError

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT count(name)
            FROM sqlite_master
            WHERE name = '{}';
                    """.format(
                GPKG_METADATA_TABLE
            )
        )
        return cursor.fetchone()[0] == 1

    def _table_exists(self, tablename):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT count(name)
            FROM sqlite_master
            WHERE name = '{}';
                    """.format(
                tablename
            )
        )
        return cursor.fetchone()[0] == 1

    def get_tables_info(self):
        return self._tables_info

    def _get_tables_info(self):
        cursor = self.conn.cursor()
        interlis_fields = ""
        interlis_joins = ""

        if self.metadata_exists():
            interlis_fields = """p.setting AS kind_settings,
                alias.setting AS table_alias,
                c.iliname AS ili_name,
                (
                SELECT GROUP_CONCAT("setting", ';') FROM (
                    SELECT tablename, setting
                    FROM T_ILI2DB_COLUMN_PROP AS cprop
                    LEFT JOIN gpkg_geometry_columns g
                    ON cprop.tablename == g.table_name
                        WHERE cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                         'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                        AND cprop.tablename = s.name
                    ORDER BY CASE TAG
                        WHEN 'ch.ehi.ili2db.c1Min' THEN 1
                        WHEN 'ch.ehi.ili2db.c2Min' THEN 2
                        WHEN 'ch.ehi.ili2db.c1Max' THEN 3
                        WHEN 'ch.ehi.ili2db.c2Max' THEN 4
                        END ASC
                    ) WHERE g.geometry_type_name IS NOT NULL
                    GROUP BY tablename
                ) AS extent,
                (
                SELECT ( CASE MAX(INSTR("setting",'.')) WHEN 0 THEN 0 ELSE MAX( LENGTH("setting") -  INSTR("setting",'.') ) END)
                    FROM T_ILI2DB_COLUMN_PROP AS cprop
                    LEFT JOIN gpkg_geometry_columns g
                    ON cprop.tablename == g.table_name
                        WHERE cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                         'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
						AND cprop.tablename = s.name
                    GROUP BY tablename
                )  as coord_decimals,
                substr(c.iliname, 0, instr(c.iliname, '.')) AS model,
                attrs.sqlname as attribute_name, """
            interlis_joins = """LEFT JOIN T_ILI2DB_TABLE_PROP p
                   ON p.tablename = s.name
                      AND p.tag = 'ch.ehi.ili2db.tableKind'
                LEFT JOIN t_ili2db_table_prop alias
                   ON alias.tablename = s.name
                      AND alias.tag = 'ch.ehi.ili2db.dispName'
                LEFT JOIN t_ili2db_classname c
                   ON s.name == c.sqlname
                LEFT JOIN t_ili2db_attrname attrs
                   ON c.iliname = attrs.iliname """

        try:
            cursor.execute(
                """
                SELECT NULL AS schemaname,
                    s.name AS tablename,
                    NULL AS primary_key,
                    g.column_name AS geometry_column,
                    g.srs_id AS srid,
                    {interlis_fields}
                    g.geometry_type_name AS type
                FROM sqlite_master s
                LEFT JOIN gpkg_geometry_columns g
                   ON g.table_name = s.name
                {interlis_joins}
                WHERE s.type='table';
            """.format(
                    interlis_fields=interlis_fields, interlis_joins=interlis_joins
                )
            )
            records = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If the geopackage is empty, geometry_columns table does not exist
            return []

        # Use prefix-suffix pairs defined in config to filter out matching tables
        filtered_records = records[:]
        for prefix_suffix in GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX:
            suffix_regexp = (
                "(" + "|".join(prefix_suffix["suffix"]) + ")$"
                if prefix_suffix["suffix"]
                else ""
            )
            regexp = r"{}[\W\w]+{}".format(prefix_suffix["prefix"], suffix_regexp)

            p = re.compile(
                regexp
            )  # e.g., 'rtree_[\W\w]+_(geometry|geometry_node|geometry_parent|geometry_rowid)$'
            for record in records:
                if p.match(record["tablename"]):
                    if record in filtered_records:
                        filtered_records.remove(record)

        # Get pk info and update each record storing it in a list of dicts
        complete_records = list()
        for record in filtered_records:
            cursor.execute(
                """
                PRAGMA table_info({})
                """.format(
                    record["tablename"]
                )
            )
            table_info = cursor.fetchall()

            primary_key_list = list()
            for table_record in table_info:
                if table_record["pk"] > 0:
                    primary_key_list.append(table_record["name"])
            primary_key = ",".join(primary_key_list) or None

            dict_record = dict(zip(record.keys(), tuple(record)))
            dict_record["primary_key"] = primary_key
            complete_records.append(dict_record)

        cursor.close()
        return complete_records

    def get_meta_attrs_info(self):
        if not self._table_exists(GPKG_METAATTRS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """
                        SELECT *
                        FROM {meta_attr_table}
        """.format(
                meta_attr_table=GPKG_METAATTRS_TABLE
            )
        )
        records = cursor.fetchall()
        cursor.close()
        return records

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(GPKG_METAATTRS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """
                        SELECT
                          attr_name,
                          attr_value
                        FROM {meta_attr_table}
                        WHERE ilielement='{ili_name}'
        """.format(
                meta_attr_table=GPKG_METAATTRS_TABLE, ili_name=ili_name
            )
        )
        records = cursor.fetchall()
        cursor.close()
        return records

    def get_fields_info(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info({});".format(table_name))
        columns_info = cursor.fetchall()

        columns_prop = list()
        columns_full_name = list()
        meta_attrs = list()

        if self.metadata_exists():
            cursor.execute(
                """
                SELECT *
                FROM t_ili2db_column_prop
                WHERE tablename = '{}'
                """.format(
                    table_name
                )
            )
            columns_prop = cursor.fetchall()

        if self.metadata_exists():
            if self.ili_version() == 3:
                cursor.execute(
                    """
                    SELECT SqlName, IliName
                    FROM t_ili2db_attrname
                    WHERE owner = '{}'
                    """.format(
                        table_name
                    )
                )
            else:
                cursor.execute(
                    """
                    SELECT SqlName, IliName
                    FROM t_ili2db_attrname
                    WHERE colowner = '{}'
                    """.format(
                        table_name
                    )
                )
            columns_full_name = cursor.fetchall()

        if self.metadata_exists() and self._table_exists(GPKG_METAATTRS_TABLE):
            meta_attrs = self.get_meta_attrs_info()

        complete_records = list()
        for column_info in columns_info:
            record = {}
            record["column_name"] = column_info["name"]
            record["data_type"] = column_info["type"]
            record["comment"] = None
            record["unit"] = None
            record["texttype"] = None
            record["column_alias"] = None
            record["enum_domain"] = None

            if record["column_name"] == "T_Id" and Qgis.QGIS_VERSION_INT >= 30500:
                # Calculated on client side, since sqlite doesn't provide the means to pre-evaluate serials
                record[
                    "default_value_expression"
                ] = "sqlite_fetch_and_increment(@layer, 'T_KEY_OBJECT', 'T_LastUniqueId', 'T_Key', 'T_Id', map('T_LastChange','date(''now'')','T_CreateDate','date(''now'')','T_User','''' || @user_account_name || ''''))"

            for column_full_name in columns_full_name:
                if column_full_name["sqlname"] == column_info["name"]:
                    record["fully_qualified_name"] = column_full_name["iliname"]
                    break

            for column_prop in columns_prop:
                if column_prop["columnname"] == column_info["name"]:
                    if column_prop["tag"] == "ch.ehi.ili2db.unit":
                        record["unit"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.textKind":
                        record["texttype"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.dispName":
                        record["column_alias"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.enumDomain":
                        record["enum_domain"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.oidDomain":
                        # Calculated on client side, since sqlite doesn't provide the means to pre-evaluate UUID
                        if (
                            record["column_name"] == "T_Ili_Tid"
                            and column_prop["setting"] == "INTERLIS.UUIDOID"
                        ):
                            record["default_value_expression"] = "substr(uuid(), 2, 36)"

            record["attr_order"] = "999"
            if (
                "fully_qualified_name" in record
            ):  # e.g., t_id's don't have a fully qualified name
                attr_order_found = False
                attr_mapping_found = False
                for meta_attr in meta_attrs:
                    if record["fully_qualified_name"] != meta_attr["ilielement"]:
                        continue

                    if meta_attr["attr_name"] == "form_order":
                        record["attr_order"] = meta_attr["attr_value"]
                        attr_order_found = True

                    if meta_attr["attr_name"] == "ili2db.mapping":
                        record["attr_mapping"] = meta_attr["attr_value"]
                        attr_mapping_found = True

                    if attr_order_found and attr_mapping_found:
                        break

            complete_records.append(record)

        # Finally, let's order the records by attr_order
        complete_records = sorted(complete_records, key=lambda k: int(k["attr_order"]))

        cursor.close()
        return complete_records

    def get_min_max_info(self, table_name):
        constraint_mapping = dict()
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT sql
                          FROM sqlite_master
                          WHERE name = '{}' AND type = 'table'
                       """.format(
                table_name
            )
        )

        # Create a mapping in the form of
        #
        # fieldname: (min, max)
        res1 = re.findall(r"CHECK\((.*)\)", cursor.fetchone()[0])
        for res in res1:
            res2 = re.search(
                r"(\w+) BETWEEN ([-?\d\.E]+) AND ([-?\d\.E]+)", res
            )  # Might contain scientific notation
            if res2:
                constraint_mapping[res2.group(1)] = (res2.group(2), res2.group(3))

        return constraint_mapping

    def get_relations_info(self, filter_layer_list=[]):
        # We need to get the PK for each table, so first get tables_info
        # and then build something more searchable
        tables_info_dict = dict()
        for table_info in self._tables_info:
            tables_info_dict[table_info["tablename"]] = table_info

        cursor = self.conn.cursor()
        complete_records = list()
        for table_info_name, table_info in tables_info_dict.items():
            cursor.execute("PRAGMA foreign_key_list({});".format(table_info_name))
            foreign_keys = cursor.fetchall()

            for foreign_key in foreign_keys:
                record = {}
                record["referencing_table"] = table_info["tablename"]
                record["referencing_column"] = foreign_key["from"]
                record["referenced_table"] = foreign_key["table"]
                record["referenced_column"] = tables_info_dict[foreign_key["table"]][
                    "primary_key"
                ]
                record["constraint_name"] = "{}_{}_{}_{}".format(
                    record["referencing_table"],
                    record["referencing_column"],
                    record["referenced_table"],
                    record["referenced_column"],
                )
                if self._table_exists(GPKG_METAATTRS_TABLE):
                    cursor.execute(
                        """SELECT META_ATTRS.attr_value as strength
                        FROM t_ili2db_attrname AS ATTRNAME
                        INNER JOIN t_ili2db_meta_attrs AS META_ATTRS
                        ON META_ATTRS.ilielement = ATTRNAME.iliname AND META_ATTRS.attr_name = 'ili2db.ili.assocKind'
                        WHERE ATTRNAME.sqlname = '{referencing_column}' AND ATTRNAME.{colowner} = '{referencing_table}' AND ATTRNAME.target = '{referenced_table}'
                    """.format(
                            referencing_column=foreign_key["from"],
                            referencing_table=table_info["tablename"],
                            referenced_table=foreign_key["table"],
                            colowner="owner" if self.ili_version() == 3 else "colowner",
                        )
                    )
                    strength_record = cursor.fetchone()
                    record["strength"] = (
                        strength_record["strength"] if strength_record else ""
                    )

                complete_records.append(record)

        cursor.close()
        return complete_records

    def get_bags_of_info(self):
        cursor = self.conn.cursor()
        if self.metadata_exists():
            cursor.execute(
                """SELECT cprop.tablename as current_layer_name, cprop.columnname as attribute, cprop.setting as target_layer_name,
                            meta_attrs_cardinality_min.attr_value as cardinality_min, meta_attrs_cardinality_max.attr_value as cardinality_max
                            FROM t_ili2db_column_prop as cprop
                            LEFT JOIN t_ili2db_classname as cname
                            ON cname.sqlname = cprop.tablename
                            LEFT JOIN t_ili2db_meta_attrs as meta_attrs_array
                            ON LOWER(meta_attrs_array.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_array.attr_name = 'ili2db.mapping'
                            LEFT JOIN t_ili2db_meta_attrs as meta_attrs_cardinality_min
                            ON LOWER(meta_attrs_cardinality_min.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_cardinality_min.attr_name = 'ili2db.ili.attrCardinalityMin'
                            LEFT JOIN t_ili2db_meta_attrs as meta_attrs_cardinality_max
                            ON LOWER(meta_attrs_cardinality_max.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_cardinality_max.attr_name = 'ili2db.ili.attrCardinalityMax'
                            WHERE cprop.tag = 'ch.ehi.ili2db.foreignKey' AND meta_attrs_array.attr_value = 'ARRAY'
                            """
            )
        return cursor

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        # Map domain ili name with its correspondent sql name
        if self.metadata_exists():
            cursor = self.conn.cursor()

            where = ""
            if sqlnames:
                names = "'" + "','".join(sqlnames) + "'"
                where = "WHERE sqlname IN ({})".format(names)

            cursor.execute(
                """SELECT iliname, sqlname
                              FROM t_ili2db_classname
                              {where}
                           """.format(
                    where=where
                )
            )
            return cursor

        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        class_names = (
            "'"
            + "','".join(list(models_info.keys()) + list(extended_classes.keys()))
            + "'"
        )
        cursor.execute(
            """SELECT *
                           FROM t_ili2db_classname
                           WHERE iliname IN ({class_names})
                        """.format(
                class_names=class_names
            )
        )
        return cursor

    def get_attrili_attrdb_mapping(self, attrs_list):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        attr_names = "'" + "','".join(attrs_list) + "'"
        cursor.execute(
            """SELECT iliname, sqlname, owner
                           FROM t_ili2db_attrname
                           WHERE iliname IN ({attr_names})
                        """.format(
                attr_names=attr_names
            )
        )
        return cursor

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        owner_names = "'" + "','".join(owners) + "'"
        cursor.execute(
            """SELECT iliname, sqlname, owner
                           FROM t_ili2db_attrname
                           WHERE owner IN ({owner_names})
                        """.format(
                owner_names=owner_names
            )
        )
        return cursor

    def get_models(self):
        """Needed for exportmodels"""
        # Get MODELS
        cursor = self.conn.cursor()

        cursor.execute(
            """SELECT distinct substr(iliname, 1, pos-1) AS modelname from
                                    (SELECT *, instr(iliname,'.') AS pos FROM t_ili2db_trafo)"""
        )

        models = cursor.fetchall()

        cursor.execute(
            """SELECT modelname, content
                          FROM t_ili2db_model """
        )

        contents = cursor.fetchall()

        result = dict()
        list_result = []

        for content in contents:
            for model in models:
                if model["modelname"] in re.sub(
                    r"(?:\{[^\}]*\}|\s)", "", content["modelname"]
                ):
                    result["modelname"] = model["modelname"]
                    result["content"] = content["content"]
                    list_result.append(result)
                    result = dict()

        return list_result

    def ili_version(self):
        cursor = self.conn.cursor()
        cursor.execute("""PRAGMA table_info(t_ili2db_attrname)""")
        table_info = cursor.fetchall()
        result = 0
        for column_info in table_info:
            if column_info[1] == "Owner":
                result += 1
        cursor.execute("""PRAGMA table_info(t_ili2db_model)""")
        table_info = cursor.fetchall()
        for column_info in table_info:
            if column_info[1] == "file":
                result += 1
        if result > 1:
            self.new_message.emit(
                Qgis.Warning,
                "DB schema created with ili2db version 3. Better use version 4.",
            )
            return 3
        else:
            return 4

    def get_basket_handling(self):
        if self._table_exists(GPKG_SETTINGS_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT setting
                            FROM {}
                            WHERE tag = ?
                            """.format(
                    GPKG_SETTINGS_TABLE
                ),
                ["ch.ehi.ili2db.BasketHandling"],
            )
            content = cursor.fetchone()
            if content:
                return content[0] == "readWrite"
        return False

    def get_baskets_info(self):
        if self._table_exists(GPKG_BASKET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT b.t_id as basket_t_id,
                            b.t_ili_tid as basket_t_ili_tid,
                            b.topic as topic,
                            d.t_id as dataset_t_id,
                            d.datasetname as datasetname from {basket_table} b
                            JOIN {dataset_table} d
                            ON b.dataset = d.t_id
                        """.format(
                    basket_table=GPKG_BASKET_TABLE, dataset_table=GPKG_DATASET_TABLE
                )
            )
            contents = cur.fetchall()
            return contents
        return {}

    def get_datasets_info(self):
        if self._table_exists(GPKG_DATASET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT t_id, datasetname
                           FROM {dataset_table}
                        """.format(
                    dataset_table=GPKG_DATASET_TABLE
                )
            )
            contents = cur.fetchall()
            return contents
        return {}

    def create_dataset(self, datasetname):
        if self._table_exists(GPKG_DATASET_TABLE):
            cur = self.conn.cursor()
            try:
                (
                    status,
                    next_id,
                    fetch_and_increment_feedback,
                ) = self._fetch_and_increment_key_object(self.tid)
                if not status:
                    return False, self.tr('Could not create dataset "{}": {}').format(
                        datasetname, fetch_and_increment_feedback
                    )

                cur.execute(
                    """
                    INSERT INTO {dataset_table} ({tid_name},datasetName) VALUES (:next_id, :datasetname)
                    """.format(
                        tid_name=self.tid, dataset_table=GPKG_DATASET_TABLE
                    ),
                    {"datasetname": datasetname, "next_id": next_id},
                )
                self.conn.commit()
                return True, self.tr('Successfully created dataset "{}".').format(
                    datasetname
                )
            except sqlite3.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr('Could not create dataset "{}": {}').format(
                    datasetname, error_message
                )
        return False, self.tr('Could not create dataset "{}".').format(datasetname)

    def rename_dataset(self, tid, datasetname):
        if self._table_exists(GPKG_DATASET_TABLE):
            cur = self.conn.cursor()
            try:
                cur.execute(
                    """
                    UPDATE {dataset_table} SET datasetName = :datasetname WHERE {tid_name} = {tid}
                    """.format(
                        dataset_table=GPKG_DATASET_TABLE, tid_name=self.tid, tid=tid
                    ),
                    {"datasetname": datasetname},
                )
                self.conn.commit()
                return True, self.tr('Successfully renamed dataset to "{}".').format(
                    datasetname
                )
            except sqlite3.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr('Could not rename dataset to "{}": {}').format(
                    datasetname, error_message
                )
        return False, self.tr('Could not rename dataset to "{}".').format(datasetname)

    def get_topics_info(self):
        if self._table_exists("T_ILI2DB_CLASSNAME"):
            cur = self.conn.cursor()
            cur.execute(
                """
                    SELECT DISTINCT substr(IliName, 0, instr(IliName, '.')) as model,
                    substr(substr(IliName, instr(IliName, '.')+1),0, instr(substr(IliName, instr(IliName, '.')+1),'.')) as topic
                    FROM T_ILI2DB_CLASSNAME
					WHERE topic != ''
                """
            )
            contents = cur.fetchall()
            return contents
        return {}

    def create_basket(self, dataset_tid, topic):
        if self._table_exists(GPKG_BASKET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """
                    SELECT * FROM {basket_table}
                    WHERE dataset = {dataset_tid} and topic = '{topic}'
                """.format(
                    basket_table=GPKG_BASKET_TABLE, dataset_tid=dataset_tid, topic=topic
                )
            )
            if cur.fetchone():
                return False, self.tr('Basket for topic "{}" already exists.').format(
                    topic
                )
            try:
                (
                    status,
                    next_id,
                    fetch_and_increment_feedback,
                ) = self._fetch_and_increment_key_object(self.tid)
                if not status:
                    return False, self.tr(
                        'Could not create basket for topic "{}": {}'
                    ).format(topic, fetch_and_increment_feedback)
                cur.execute(
                    """
                    INSERT INTO {basket_table} ({tid_name}, dataset, topic, {tilitid_name}, attachmentkey )
                    VALUES ({next_id}, {dataset_tid}, '{topic}', '{uuid}', 'Qgis Model Baker')
                """.format(
                        tid_name=self.tid,
                        tilitid_name=self.tilitid,
                        basket_table=GPKG_BASKET_TABLE,
                        next_id=next_id,
                        dataset_tid=dataset_tid,
                        topic=topic,
                        uuid=uuid.uuid4(),
                    )
                )
                self.conn.commit()
                return True, self.tr(
                    'Successfully created basket for topic "{}".'
                ).format(topic)
            except sqlite3.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr(
                    'Could not create basket for topic "{}": {}'
                ).format(topic, error_message)
        return False, self.tr('Could not create basket for topic "{}".').format(topic)

    def get_tid_handling(self):
        if self._table_exists(GPKG_SETTINGS_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT setting
                            FROM {}
                            WHERE tag = ?
                            """.format(
                    GPKG_SETTINGS_TABLE
                ),
                ["ch.ehi.ili2db.TidHandling"],
            )
            content = cursor.fetchone()
            if content:
                return content[0] == "property"
        return False

    def _fetch_and_increment_key_object(self, field_name):
        next_id = 0
        if self._table_exists("T_KEY_OBJECT"):
            # fetch last unique id of field_name
            cur = self.conn.cursor()
            cur.execute(
                """
                    SELECT T_LastUniqueId, T_CreateDate FROM T_KEY_OBJECT
                    WHERE T_Key = ?
                """,
                [field_name],
            )

            content = cur.fetchone()

            create_date = "date('now')"

            # increment
            if content:
                next_id = content[0] + 1
                create_date = content[1]

            # and update
            try:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO T_KEY_OBJECT (T_Key, T_LastUniqueId, T_LastChange, T_CreateDate, T_User )
                    VALUES (:key, :next_id, date('now'), :create_date, 'Qgis Model Baker')
                """,
                    {"key": field_name, "next_id": next_id, "create_date": create_date},
                )
                self.conn.commit()
                return (
                    True,
                    next_id,
                    self.tr("Successfully set the T_LastUniqueId to {}.").format(
                        next_id
                    ),
                )
            except sqlite3.Error as e:
                error_message = " ".join(e.args)

                return (
                    False,
                    next_id,
                    self.tr("Could not set the T_LastUniqueId to {}: {}").format(
                        next_id, error_message
                    ),
                )
        return (
            False,
            next_id,
            self.tr(
                "Could not fetch T_LastUniqueId because T_KEY_OBJECT does not exist."
            ),
        )
