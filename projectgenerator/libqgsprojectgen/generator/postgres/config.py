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
    't_ili2db_import_basket'
]

IGNORED_FIELDNAMES = [
    't_id',
    't_seq',
    't_basket'
]

READONLY_FIELDNAMES = [
    't_ili_tid'
]
