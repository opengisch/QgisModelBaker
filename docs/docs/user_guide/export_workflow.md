You can export your data from an physical database into an `xtf` file (INTERLIS transfer file). Select *Export data from an existing database* in the intro page of the wizard.
## Database Selection

First you have to select the database schema or file to export your data from.

![wizard db configuration](../assets/workflow_wizard_db_configuration.png)

For more detailed description of the connection parameters, see the description in the [import workflow](../import_workflow/#database-selection)

When the database or the schema / file does not exist, a warning will appear.

## Export data

![wizard export data](../assets/workflow_wizard_export_data.png)
### XTF File

Set the `xtf` file where you want to export your data to.

### Filters

You can filter the data *either* by models *or* - if the database considers [Dataset and Basket Handling](../../background_info/basket_handling/) - by datasets *or* baskets. You can choose multiple models/datasets/baskets. But only one kind of filter (`--model`, `--dataset`, `--basket`) is given to the ili2db command (it would make no conjunction (AND) but a disjunction (OR) if multiple parameters are given (what is not really used). A conjunction can still be done by selecting the smallest instance (baskets)).

## Run ili2db Sessions

In the next step you can run the export in one single ili2db command.

With the ![run arrow_button](../assets/arrow_button.png) button next to *Run* the options are provided to run the command without any validation of your data or to edit the command manually before running it.

## Data Validation

If you did not choose *Run without constraints* on your export session, then the data are validated against their INTERLIS models. If this validation did not succeed, then the export will fail.

To check your data in advance against the INTERLIS model, use the [Model Baker Validator](../validation/).
