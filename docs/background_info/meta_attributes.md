> To a metaelement metaattributes could be compositional assigned (class "MetaAttribut"). The metaattributes are neither defined by the language INTERLIS nor by the meta model. They exist that the information that exceed INTERLIS could still be a component of the model data. The metaattributes has a name (attribute "Name"), that have to be unique among the the metaattributes of this metaelement, and it has a value (attribute: "Value").

Translated from source: [STAN_d_DEF_2011-06-22_eCH-0117 Meta-Attribute für INTERLIS-Modelle.pdf](https://www.ech.ch/alfresco/s/ech/download?nodeid=788eb38a-bf2b-4f3d-96a8-addc37bba41f) (German) from eCH www.interlis.ch

## Meta Attributes in Interlis Files

### Comment vs. Meta Attribute

An Interlis comment starts with `!!` and ends with a line end. A meta attribute starts with `!!` as well but followed by an `@`:

### Syntax

After the start of `!!@` the meta attribute name follows, then equal `=`, then the attribute value:

```
!!@<name>=<value>
```
Followed by the referenced element (MODEL, TOPIC, CLASS etc.)

### Example

ExceptionalLoadsRoute.ili:
```
!!@ furtherInformation=https://www.astra.admin.ch/
MODEL ExceptionalLoadsCatalogues_V1 (en)
AT "http://models.geo.admin.ch/ASTRA/"
VERSION "2017-02-08"  =
    IMPORTS CatalogueObjects_V1,Units;
    !!@ topicInformation="Route-Type"
    TOPIC TypeOfRouteCatalogue
    EXTENDS CatalogueObjects_V1.Catalogues =
    !!@ dispExpression="CONCAT(type, ' sometext')"
    CLASS TypeOfRoute
    EXTENDS CatalogueObjects_V1.Catalogues.Item =
```

`furtherInformation` is referenced to `ExceptionalLoadsCatalogues_V1`, `topicInformation` to `TypeOfRouteCatalogue` and `dispExpression` to `TypeOfRoute`.

For more complex usage see the [specification of the Verein eCH](https://www.ech.ch/alfresco/s/ech/download?nodeid=788eb38a-bf2b-4f3d-96a8-addc37bba41f).

### Meta Attributes in the Database

When importing the data from the Interlis file to the DB, with ili2db integrated in the Model Baker, the meta attributes are stored in the table **t_ili2db_meta_attrs**:

| ilielement                                                     | attr_name          | attr_value                  |
|----------------------------------------------------------------|--------------------|-----------------------------|
| ExceptionalLoadsCatalogues_V1                                  | furtherInformation | https://www.astra.admin.ch/ |
| ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue             | topicInformation   | Route-Type                  |
| ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue.TypeOfRoute | dispExpression     | CONCAT(type, ' sometext')   |

## Model Baker Specific Meta Attributes

Some additional non standard meta attributes are understood by the Model Baker as properties in the QGIS project.

### List of specific Attributes

- **dispExpression**
Used as the display expression for a layer. The display expression is the *name* that is used to identify a feature by text. One of the places where this is used is the combobox that is shown for a Relation Reference Widget on feature forms. ![relation reference](../assets/meta_attributes_relation_reference.png)


## Extra Model Information File

In these external files the meta attributes can be stored instead of having them directly in the Interlis files.

These files are written in TOML and have the filename extension `.toml`

You can select the extra meta attribute files in the **Advanced Options**. This configuration is stored for the model. This means when you reselect the same model later again, the file is still referenced. This information will be displayed on the main dialog of the Project Generator.

In the background ili2pg writes the meta attributes from the external meta attribute file to the PostGIS or GeoPackage storage, where the Project Generator can use them to build the QGIS project.


### TOML Examples

ExceptionalLoadsRoute.toml:

```ini
["ExceptionalLoadsRoute.TypeOfRouteCatalogue.TypeOfRoute"]
dispExpression="type"
```
Or using a more complex expression:
```ini
["ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue.TypeOfRoute"]
dispExpression="CONCAT(type, ' sometext')"
```

The keys that need to be used for the TOML sections are the *fully qualified Interlis names* of the objects. In the example above this is `["ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue.TypeOfRoute"]`. A list of all available names can be found in the database table `t_ili2db_classname` after doing a schema import.

### Interlis Example

The above example would be written as follows directly in an Interlis file (ExceptionalLoadsRoute.ili). If the above configuration is in the ini file, the ili meta attribute is no longer required, this is only here for reference.
```
  !!@dispExpression="type"
  CLASS TypeOfRoute=
    type: MANDATORY TEXT*25;
  END TypeOfRoute;
```
