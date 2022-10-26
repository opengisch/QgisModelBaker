You can validate your physical data against the INTERLIS models directly in QGIS. Open the Model Baker Validator Panel by the menu *Database > Model Baker > Data Validator* or *View > Panels > Model Baker Data Validator*

![validation](../assets/validation.gif)

## Database
The database connection parameter are emitted from the currently selected layer. Mostly this is representative for the whole project, since mostly a project bases on one single database schema/file. In case of multiple used database sources, it's possible to *switch* between the validation results when switching the layers.

## Filters
You can filter the data being validated *either* by models *or* - if the database considers [Dataset and Basket Handling](../../background_info/basket_handling/) - by datasets *or* baskets. You can choose multiple models/datasets/baskets. But only one kind of filter (`--model`, `--dataset`, `--basket`) is given to the ili2db command (it would make no conjunction (AND) but a disjunction (OR) if multiple parameters are given (what is not really used). A conjunction can still be done by selecting the smallest instance (baskets)).

## Skip Geometry Errors
When geometry errors are skipped like for example:

- Intersecting geometries
- Duplicate coordinates
- Overlaying geometries

## Configuration File
As well as configuring [meta attributes](../../background_info/meta_attributes/) used for the physical database implementation and for QGIS project generation, meta attributes can be used for additional configuration of the validation like e.g. disable specific checks on specific objects.

Single checks can be configured directly in the INTERLIS model:

```
    CLASS Dokument =
      DokumentID : TEXT*16;
      !!@ ilivalid.multiplicity = off
      Titel : MANDATORY TEXT*80;
```

The mandatory constraint will not be considered in the validation.

This can be configured in the configuration file like this:

```ini
["SO_Nutzungsplanung_20171118.Rechtsvorschriften.Dokument.Titel"]
multiplicity="off"
```

As well checks can be generally disabled by using the `"PARAMETER"` section:

```ini
["PARAMETER"]
multiplicity="off"
```

### Meta Attribute File Examples

ExceptionalLoadsRoute.ini:

```ini
["ExceptionalLoadsRoute.TypeOfRouteCatalogue.TypeOfRoute"]
dispExpression="type"
```
Or using a more complex expression:
```ini
["ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue.TypeOfRoute"]
dispExpression="CONCAT(type, ' sometext')"
```

The keys that need to be used for the INI sections are the *fully qualified INTERLIS names* of the objects. In the example above this is `["ExceptionalLoadsCatalogues_V1.TypeOfRouteCatalogue.TypeOfRoute"]`. A list of all available names can be found in the database table `t_ili2db_classname` after doing a schema import.

### INTERLIS Example

The above example would be written as follows directly in an INTERLIS file (ExceptionalLoadsRoute.ili). If the above configuration is in the ini file, the ili meta attribute is no longer required, this is only here for reference.
```
  !!@dispExpression="type"
  CLASS TypeOfRoute=
    type: MANDATORY TEXT*25;
  END TypeOfRoute;
```

## Results
After running the validation by pressing the ![checkmark](../assets/checkmark_button.png) the results are listed.

With *right click* on the error a menu is opened with the following options:
- Zoom to coordinates (if coordinates are provided)
- Open form (if a stable t_ili_tid is available)
- Set to fixed (marking the entry mark green to have organize the fixing process)
- Copy (to copy the message text)

Automatic pan, zoom and highlight features or coordinates are performed by clicking on the result tables entry.

## ili2db with `--validate` in the background
On running the validation `ili2db` is used in the background with the parameter `--validate`. This means no export of the data is needed. The output is parsed by Model Baker and provided in the result list.

Entries of the type `Error` and `Warning` are listed.
