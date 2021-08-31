IGNORED_FIELDNAMES = ["t_id", "t_seq", "t_ili_tid", "T_Id", "T_Seq", "T_Ili_Tid"]

BASKET_FIELDNAMES = ["t_basket", "T_basket"]

READONLY_FIELDNAMES = ["t_ili_tid"]

# Some GeoPackage clients might add tables that we need to ignore based on
# prefix-suffix matches, here we define some known prefix-suffix pairs
GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX = [
    {
        "prefix": "rtree_",
        "suffix": [
            "_geometry",
            "_geometry_node",
            "_geometry_parent",
            "_geometry_rowid",
            "_geom",
            "_geom_node",
            "_geom_parent",
            "_geom_rowid",
        ],
    },
    {"prefix": "vgpkg_", "suffix": []},
]
