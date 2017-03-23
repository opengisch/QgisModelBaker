import psycopg2

from dataobjects.relations import Relation

class PostgresRelation(Relation):
    pass

    @classmethod
    def find_relations(cls, layers, conn):

        mapped_layers = {layer.table_name() : layer for layer in layers}

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""SELECT RC.CONSTRAINT_NAME, KCU1.TABLE_NAME AS referencing_table_name, KCU1.COLUMN_NAME AS referencing_column_name, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME AS referenced_table_name, KCU2.COLUMN_NAME AS referenced_column_name, KCU1.ORDINAL_POSITION
                        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU1
                        ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU2
                          ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
                          AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
                        GROUP BY RC.CONSTRAINT_NAME, KCU1.TABLE_NAME, KCU1.COLUMN_NAME, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME, KCU2.COLUMN_NAME, KCU1.ORDINAL_POSITION
                        ORDER BY KCU1.ORDINAL_POSITION
                        """)

        relations = list()

        for record in cur:
            print ('Checking relation')
            if record['referencing_table_name'] in mapped_layers.keys() and record['referenced_table_name'] in mapped_layers.keys():
                relation = Relation()
                relation.referencing_layer = mapped_layers[record['referencing_table_name']].inner_id
                relation.referenced_layer = mapped_layers[record['referenced_table_name']].inner_id
                relation.referencing_field = record['referencing_column_name']
                relation.referenced_field = record['referenced_column_name']
                relation.name = record['constraint_name']

                relations.append(relation)

        return relations
