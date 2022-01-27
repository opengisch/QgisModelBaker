You can validate your physical data against the INTERLIS models directly in QGIS. Open the Model Baker Validator Panel by the menu *Database > Model Baker > Data Validator* or *View > Panels > Model Baker Data Validator*

![validation](../assets/validation.gif)

## Database
The database connection parameter are emitted from the currently selected layer. Mostly this is representative for the whole project, since mostly a project bases on one single database schema/file. In case of multiple used database sources, it's possible to *switch* between the validation results when switching the layers.

## Filters
You can filter the data being validated *either* by models *or* - if the database considers [Dataset and Basket Handling](../../background_info/basket_handling/) - by datasets *or* baskets. You can choose multiple models/datasets/baskets. But only one kind of filter (`--model`, `--dataset`, `--basket`) is given to the ili2db command (it would make no conjunction (AND) but a disjunction (OR) if multiple parameters are given (what is not really used). A conjunction can still be done by selecting the smallest instance (baskets)).

## Results
After running the validation by pressing the ![checkmark](../assets/checkmark_button.png) the results are listed.

With *right click* on the error a menu is opened with the following options:
- Zoom to coordinates (if coordinates are provided)
- Open form (if a stable t_ili_tid is available)
- Set to fixed (marking the entry mark green to have organize the fixing process)

## ili2db with `--validate` in the background
On running the validation `ili2db` is used in the background with the parameter `--validate`. This means no export of the data is needed. The output is parsed by Model Baker and provided in the result list.

Entries of the type `Error` and `Warning` are listed.
