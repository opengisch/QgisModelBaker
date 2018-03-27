IGNORED_SCHEMAS = [
    'pg_catalog',
    'information_schema'
]

IGNORED_TABLES = [
    'spatial_ref_sys',
    't_ili2db_import_object',
    't_ili2db_dataset',
    't_ili2db_attrname',
    't_ili2db_basket',
    't_ili2db_settings',
    't_ili2db_import',
    't_ili2db_inheritance',
    't_ili2db_model',
    't_ili2db_classname',
    't_ili2db_import_basket',
    'gpkg_contents',
    'gpkg_geometry_columns',
    'gpkg_extensions',
    'gpkg_spatial_ref_sys',
    'gpkg_ogr_contents',
    'gpkg_tile_matrix_set',
    'gpkg_tile_matrix',
    'gpkg_metadata',
    'gpkg_metadata_reference',
    'sqlite_sequence',
    'T_ILI2DB_DATASET',
    'T_ILI2DB_TABLE_PROP',
    'T_ILI2DB_INHERITANCE',
    'T_ILI2DB_ATTRNAME',
    'T_ILI2DB_SETTINGS',
    'T_KEY_OBJECT',
    'T_ILI2DB_MODEL',
    'T_ILI2DB_IMPORT',
    'T_ILI2DB_TRAFO',
    'T_ILI2DB_COLUMN',
    'T_ILI2DB_COLUMN_PROP',
    'T_ILI2DB_CLASSNAME',
    'T_ILI2DB_BASKET',
    'T_ILI2DB_IMPORT_OBJECT',
    'T_ILI2DB_IMPORT_BASKET',
    'ogr_empty_table'
]

IGNORED_FIELDNAMES = [
    't_id',
    't_seq',
    't_basket',
    'T_Id',
    'T_basket',
    'T_Seq'
]

READONLY_FIELDNAMES = [
    't_ili_tid'
]
