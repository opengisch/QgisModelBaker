## What is it about?

With Model Baker **additional information** for models can be found automatically via the web.

**Additional information** such as:

- ili2db settings ([Metaconfiguration](#metaconfiguration))
- Data files, like catalogs ([Referenced Data](#referenced-data))
- QGIS project configurations (so called [Toppings](#toppings))

This means that complex configurations can be made *once* and used *multiple times*.

### Metaconfiguration

The metaconfiguration can be found before creating the physical data model on the *Schema Import Configuration* page.

![metaconfig](../../assets/usabilityhub-abstract-metaconfig.png)

The metaconfiguration can contain the ili2db settings as well as links to the required QGIS project configurations (toppings) and data files (referenced data).

Find technical background and detailed information about the metaconfiguration [here](../modelbaker_integration/#metaconfiguration)

### Referenced data

The referenced data required for a model, such as catalogs and codelists, can be found in the *Data Import Configuration*.

![referenced data](../../assets/usabilityhub-abstract-referenceddata.png)

They may already have been linked via the [metaconfiguration](#metaconfiguration) before as well.

Find technical background and detailed information about the referenced data integration [here](../modelbaker_integration/#referenced-data).

### Toppings

The QGIS project configurations or so called "toppings" can - if not already linked via the [metaconfiguration](#metaconfiguration) - be found each time on the *Project Generation* page via a "projecttopping" file.

![projecttopping](../../assets/usabilityhub-abstract-projecttopping.png)

The projecttopping defines general project configurations such as layertree, variables etc. and links to the required toppings such as layerstyle etc. which are then downloaded and applied when the project is generated.

![topping download](../../assets/usabilityhub-abstract-toppingdownload.png)

Find technical background and detailed information about the toppings [here](../modelbaker_integration/#toppings).

## Where do those additional information come from?

Just as we can now find INTERLIS models by searching the ilimodels.xml files on the repositories we can find this additional information via the `ilidata.xml` file.

It filters the entries by the **name** of the used INTERLIS **model**.

More information about the technical background you can find [here](../../background_info/usabilityhub/technical_concept.md)

## What are the Workflows?

All these **additional information** are concernig a specific model. That's why they are found according to the selected model's name.

![model selection](../../assets/usabilityhub-abstract-modelselection.png)

### On choosing a metaconfiguration

...that links to *referenced data* and a *projecttopping* the workflow looks like this:

1. User enters the model name in the **Source Selection**
2. *ilidata.xml* is parsed for links to *metaconfiguration files* according to the model name
3. User selects a *metaconfiguration*

    ![metaconfig](../../assets/usabilityhub-abstract-metaconfig.png)

4. *Metaconfiguration file* is downloaded and the ili2db settings are read from the *metaconfiguration*
5. ili2db settings are considered in the creation of the physical model
6. Links to the *referenced data* are read from the *metaconfiguration*
7. *ilidata.xml* is parsed for links to the *referenced data*
8. *Referenced data files* are downloaded and imported
9. Links to the *projecttopping* is read from the *metaconfiguration*
10. *ilidata.xml* is parsed for links to the *projecttopping*
11. *Projecttopping file* is downloaded and links to the *other toppings* (like layerstyles etc.) is read from the *projecttopping*
12. *ilidata.xml* is parsed for links to the *toppings*
13. *Topping files* are downloaded
14. The information is read from the *projettopping* and the linked *toppings* and included in the generation of the QGIS project

### On choosing referenced data directly

...from the repositories in the **Data Import Configuration** the steps are:

1. *ilidata.xml* is parsed for links to the *referenced data* according to the model name.
2. User selects *referenced data*

    ![referenced data](../../assets/usabilityhub-abstract-referenceddata.png)

3. *Referenced data files* are downloaded and imported

!!! Note
    The links to the *referenced data* are found according to the used model name.

### On choosing project topping directly

... from the repositories in **Project Generation** the steps are:

1. *ilidata.xml* is parsed for links to the *projecttoppings* according to the model name
2. User selects a *projecttopping*

    ![projecttopping](../../assets/usabilityhub-abstract-projecttopping.png)

3. *Projecttopping file* is downloaded and links to the *other toppings* (like layerstyles etc.) is read from the *projecttopping*
4. *ilidata.xml* is parsed for links to the  *toppings*
5. *Topping file* are downloaded
6. The information is read from the *projettopping* and the linked *toppings* and included in the generation of the QGIS project.

!!! Note
    A *projecttopping* can be chosen from the local system as well.

## How to make my own Toppings?

This can be easily made with the [Model Baker Topping Exporter](../../user_guide/topping_exporter.md) from an exiting QGIS Project.
