## What are Datasets and Baskets

A dataset contains data of a certain spatial or thematic area, which does not affect the model structure. The data of a dataset can thus be managed, validated and exported independently of the other data. Baskets are a smaller instance. While the datasets usually comprise the whole model (or even several), the baskets are usually a part of a topic. Often they are even the subset of topic and dataset.

Datasets and baskets allow you to seperate your data thematically without affecting the INTERLIS model. They do only concern the data. You can import, export and validate them seperately by the provided filter methods of ili2db and Model Baker.

## An example

Let's say we have two melted twin cities "Beźel" and "Ul Qoma" and we want to import into the same physical data model but handle them always seperately.

### Model `City_V1`

Here we have a simple model representing a city with constructions (buildings and streets) and nature (parks).

```
INTERLIS 2.3;

MODEL City_V1 (en)
AT "https://signedav.github.io/usabilitydave/models"
VERSION "2020-06-22" =
  IMPORTS GeometryCHLV95_V1;

  DOMAIN
    Line = POLYLINE WITH (STRAIGHTS) VERTEX GeometryCHLV95_V1.Coord2;
    Surface = SURFACE WITH (STRAIGHTS) VERTEX GeometryCHLV95_V1.Coord2 WITHOUT OVERLAPS > 0.005;

  STRUCTURE Address =
    Street: TEXT;
    Number: TEXT;
  END Address;

  TOPIC Constructions =
    OID AS INTERLIS.UUIDOID;
    BASKET OID AS INTERLIS.UUIDOID;

    CLASS Buildings  =
      Code : MANDATORY TEXT*15;
      Description : MANDATORY TEXT*99;
      Address : Address;
      Geometry: Surface;
    END Buildings;

    CLASS Street  =
      Code : MANDATORY TEXT*15;
      Description : MANDATORY TEXT*99;
      Address : Address;
      Geometry: Line;
    END Street;

  END Constructions;

  TOPIC Nature =
    OID AS INTERLIS.UUIDOID;
    BASKET OID AS INTERLIS.UUIDOID;

    CLASS Parks  =
      Name : MANDATORY TEXT*99;
      Address : Address;
      Geometry: Surface;
    END Parks;

  END Nature;

END City_V1.
```

The model defines `BASKET OID` this means ... and `OID` what means ...

We need to create the physical model the ili2db parameter `--createBasketCol`. This we can activate by setting with *Create Basket Column* in the Model Baker Wizard. Ili2db creates a new column `T_basket` in class tables which references entries in the additional table `t_ili2db_baskets`. The `T_basket` column needs to be filled with the basket to which an object belongs. But no worry, it's supereasy with [dataset selector](#dataset-selector).

### Data of Ul Qoma

And here are the data from one of the cities (Ul Qoma):
```
<?xml version="1.0" encoding="UTF-8"?><TRANSFER xmlns="http://www.interlis.ch/INTERLIS2.3">
<HEADERSECTION SENDER="ili2pg-4.6.1-63db90def1260a503f0f2d4cb846686cd4851184" VERSION="2.3"><MODELS><MODEL NAME="City_V1" VERSION="2020-06-22" URI="https://signedav.github.io/usabilitydave/models"></MODEL></MODELS></HEADERSECTION>
<DATASECTION>
<City_V1.Constructions BID="7dc3c035-b281-412f-9ba3-c69481054974">
  <City_V1.Constructions.Buildings TID="c7c3e013-b5bb-474d-b7d8-1f8de718e160"><Address><City_V1.Address><Street>Rue des Fleures</Street><Number>1</Number></City_V1.Address></Address><Description>Maison Une</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698895.284</C1><C2>1262445.346</C2></COORD><COORD><C1>2698902.726</C1><C2>1262460.945</C2></COORD><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
  <City_V1.Constructions.Buildings TID="3d6ceabe-7674-4436-8316-ef3b72ba1327"><Address><City_V1.Address><Street>Rue des Fleures</Street><Number>2</Number></City_V1.Address></Address><Description>Maison2</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD><COORD><C1>2698902.726</C1><C2>1262460.945</C2></COORD><COORD><C1>2698911.469</C1><C2>1262479.960</C2></COORD><COORD><C1>2698906.189</C1><C2>1262485.007</C2></COORD><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
  <City_V1.Constructions.Buildings TID="d93069ea-ca81-4891-8055-e5791d1be167"><Description>Maison trois</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD><COORD><C1>2698923.489</C1><C2>1262491.762</C2></COORD><COORD><C1>2698928.297</C1><C2>1262492.854</C2></COORD><COORD><C1>2698926.858</C1><C2>1262505.315</C2></COORD><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
  <City_V1.Constructions.Buildings TID="100415e2-db32-49aa-8d44-9eff1f38e372"><Address><City_V1.Address><Street>Parque de la Musique</Street><Number>1</Number></City_V1.Address></Address><Description>Maison Quatre</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD><COORD><C1>2698934.854</C1><C2>1262426.195</C2></COORD><COORD><C1>2698949.060</C1><C2>1262428.600</C2></COORD><COORD><C1>2698947.958</C1><C2>1262441.422</C2></COORD><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
  <City_V1.Constructions.Street TID="451cfaee-299f-4b72-bcc2-6b6a097ee0d2"><Name>Rue des Fleures</Name><Geometry><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD><COORD><C1>2698929.609</C1><C2>1262506.186</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
  <City_V1.Constructions.Street TID="d6ed2502-7161-4e04-8589-3cd6c84a51e0"><Name>Rue de la Musique</Name><Geometry><POLYLINE><COORD><C1>2698929.609</C1><C2>1262506.186</C2></COORD><COORD><C1>2698943.596</C1><C2>1262509.027</C2></COORD><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD><COORD><C1>2698959.332</C1><C2>1262489.795</C2></COORD><COORD><C1>2698980.969</C1><C2>1262480.834</C2></COORD><COORD><C1>2698993.863</C1><C2>1262415.486</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
  <City_V1.Constructions.Street TID="1f47c793-326a-47ba-b076-8ae9f25b2990"><Name>Rue de la Soleil</Name><Geometry><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698901.415</C1><C2>1262410.460</C2></COORD><COORD><C1>2698902.071</C1><C2>1262390.790</C2></COORD><COORD><C1>2698906.005</C1><C2>1262389.041</C2></COORD><COORD><C1>2698935.510</C1><C2>1262391.227</C2></COORD><COORD><C1>2698984.684</C1><C2>1262406.307</C2></COORD><COORD><C1>2698993.863</C1><C2>1262415.486</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
</City_V1.Constructions>
<City_V1.Nature BID="6cc059e9-0182-4c9f-9208-28be3c172471">
  <City_V1.Nature.Parks TID="3445b04b-a4ed-4a03-bb09-c9e52134cad6"><Name>Parque de la Musique</Name><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD><COORD><C1>2698932.231</C1><C2>1262487.828</C2></COORD><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD><COORD><C1>2698963.922</C1><C2>1262442.368</C2></COORD><COORD><C1>2698963.484</C1><C2>1262465.754</C2></COORD><COORD><C1>2698982.968</C1><C2>1262470.701</C2></COORD><COORD><C1>2698980.969</C1><C2>1262480.834</C2></COORD><COORD><C1>2698959.332</C1><C2>1262489.795</C2></COORD><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Nature.Parks>
  <City_V1.Nature.Parks TID="d7e73464-f27e-4d2d-848c-66735f3fe5af"><Name>Parque des Fleures</Name><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698901.415</C1><C2>1262410.460</C2></COORD><COORD><C1>2698903.164</C1><C2>1262439.309</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Nature.Parks>
</City_V1.Nature>
</DATASECTION>
</TRANSFER>
```

These are basicly the data in a dataset. You might already notice the `BID` fields. These identify the baskets for each topic. It would be technically possible to have multiple baskets per topic in the same dataset but it's usually not used.

## Data Update

We need to import the data of Ul Qoma now into our physical model with the ili2db parameter `--dataset "Ul Qoma"`. When the dataset already exists in the physical database we do not make an `--import`, but an `--update` instead. This means all the data in this dataset are updated with the data from the `xtf` file (and removed if not existent there).

## Dataset Manager

With the Model Baker we do make generally an `--update`, because we import only into exiting datasets. To have a dataset called "Ul Qoma" selectable, we need to create it in the Dataset Manager.

![dataset manager](../assets/baskets_dataset_manager.png)

After that you can double-click the dataset field and choose "Ul Qoma". This command will be excecuted in the background:
```
java -jar /home/freddy/ili2pg-4.6.1.jar --update --dbhost localhost --dbport 5432 --dbusr postgres --dbpwd ****** --dbdatabase freds_bakery --dbschema thecityandthecity --importTid --importBid --dataset "Ul Qoma" /home/freddy/referencedata/TheCity_V1-ulqoma.xtf
```

As you can see `--importTid` and `--importBid` are automatically adde to the command. This because ...

## Structure in the Database

You don't need to know that but you might be interested in it.

### Dataset "Ul Qoma"

After importing your data of the city "Ul Qoma", there are now these two tables in the database. They look like this:

**t_ili2db_dataset**
```
 t_id | datasetname
------+-------------
    4 | Ul Qoma
```

**t_ili2db_basket**
```
 t_id | dataset |         topic         |              t_ili_tid               |      attachmentkey      | domains
------+---------+-----------------------+--------------------------------------+-------------------------+---------
    5 |       4 | City_V1.Constructions | d861b84f-7068-43d0-b8c1-f0d2f200b075 | TheCity_V1-ulqoma.xtf-5 |
   23 |       4 | City_V1.Nature        | 8d4b122c-3582-447c-b933-3175674151e0 | TheCity_V1-ulqoma.xtf-5 |
```

As you can see the two baskets have been created and connected to the dataset you created before. In fact they do not exactly look like this on your system. There will be the default dataset called `Baseset` created by Model Baker on the creation of the physical database and the corresponding baskets per topic.

### Data of "Ul Qoma"
When we check out the data now, we see that they are referencing the baskets (which further references the dataset).

**parks**
```
 t_id | t_basket |              t_ili_tid               |       aname       |      ageometry
------+----------+--------------------------------------+-------------------+--------------------
   19 |        5 | 7bcc0efd-1d81-400a-8dfb-1f17f4e72287 | Main Route        | 01020000200808[...]
   20 |        5 | 3eab5bd9-3dc8-4e73-81f1-b8d8cfaba748 | Tiny Route        | 01020000200804[...]
   21 |        5 | b5c3d22c-974f-49c9-b361-d85dbdc4000b | Park Way          | 01020000200808[...]
   22 |        5 | d954d3c4-ec24-44cd-af2d-d7f3af781a18 | Mullholland Drive | 01020000200808[...]
```

**street**
```
 t_id | t_basket |              t_ili_tid               |   aname     |      ageometry
------+----------+--------------------------------------+-------------+--------------------------
   24 |       23 | dbe968d7-e41d-4c14-9560-c2161bea76db | UlQoma Park | 01030000200808000800[...]
   25 |       23 | 574eed9f-4cef-4747-8cbb-5e8519898626 | Big Green   | 01030000200808000000[...]
   26 |       23 | d92d5cde-7ef3-48e8-b6cc-e370a5cba64d | Selmas Park | 01030000200080033330[...]
```

### Data after import of "Besźel"

Well that does not look that interesting with only one dataset. So let's import the data of "Besźel" as well.

```
<?xml version="1.0" encoding="UTF-8"?><TRANSFER xmlns="http://www.interlis.ch/INTERLIS2.3">
<HEADERSECTION SENDER="ili2pg-4.6.1-63db90def1260a503f0f2d4cb846686cd4851184" VERSION="2.3"><MODELS><MODEL NAME="City_V1" VERSION="2020-06-22" URI="https://signedav.github.io/usabilitydave/models"></MODEL></MODELS></HEADERSECTION>
<DATASECTION>
<City_V1.Constructions BID="7dc3c035-b281-412f-9ba3-c69481054974">
<City_V1.Constructions.Buildings TID="c7c3e013-b5bb-474d-b7d8-1f8de718e160"><Address><City_V1.Address><Street>Rue des Fleurs</Street><Number>1</Number></City_V1.Address></Address><Description>Maison Une</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698895.284</C1><C2>1262445.346</C2></COORD><COORD><C1>2698902.726</C1><C2>1262460.945</C2></COORD><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
<City_V1.Constructions.Buildings TID="3d6ceabe-7674-4436-8316-ef3b72ba1327"><Address><City_V1.Address><Street>Rue des Fleurs</Street><Number>2</Number></City_V1.Address></Address><Description>Maison 2</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD><COORD><C1>2698902.726</C1><C2>1262460.945</C2></COORD><COORD><C1>2698911.469</C1><C2>1262479.960</C2></COORD><COORD><C1>2698906.189</C1><C2>1262485.007</C2></COORD><COORD><C1>2698895.825</C1><C2>1262467.883</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
<City_V1.Constructions.Buildings TID="d93069ea-ca81-4891-8055-e5791d1be167"><Description>Maison trois</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD><COORD><C1>2698923.489</C1><C2>1262491.762</C2></COORD><COORD><C1>2698928.297</C1><C2>1262492.854</C2></COORD><COORD><C1>2698926.858</C1><C2>1262505.315</C2></COORD><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
<City_V1.Constructions.Buildings TID="100415e2-db32-49aa-8d44-9eff1f38e372"><Address><City_V1.Address><Street>Parque de la Musique</Street><Number>1</Number></City_V1.Address></Address><Description>Maison Quatre</Description><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD><COORD><C1>2698934.854</C1><C2>1262426.195</C2></COORD><COORD><C1>2698949.060</C1><C2>1262428.600</C2></COORD><COORD><C1>2698947.958</C1><C2>1262441.422</C2></COORD><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Constructions.Buildings>
<City_V1.Constructions.Street TID="451cfaee-299f-4b72-bcc2-6b6a097ee0d2"><Name>Rue des Fleurs</Name><Geometry><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698916.495</C1><C2>1262502.034</C2></COORD><COORD><C1>2698929.609</C1><C2>1262506.186</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
<City_V1.Constructions.Street TID="d6ed2502-7161-4e04-8589-3cd6c84a51e0"><Name>Rue de la Musique</Name><Geometry><POLYLINE><COORD><C1>2698929.609</C1><C2>1262506.186</C2></COORD><COORD><C1>2698943.596</C1><C2>1262509.027</C2></COORD><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD><COORD><C1>2698959.332</C1><C2>1262489.795</C2></COORD><COORD><C1>2698980.969</C1><C2>1262480.834</C2></COORD><COORD><C1>2698993.863</C1><C2>1262415.486</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
<City_V1.Constructions.Street TID="1f47c793-326a-47ba-b076-8ae9f25b2990"><Name>Rue de neuf Soleils</Name><Geometry><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698901.415</C1><C2>1262410.460</C2></COORD><COORD><C1>2698902.071</C1><C2>1262390.790</C2></COORD><COORD><C1>2698906.005</C1><C2>1262389.041</C2></COORD><COORD><C1>2698935.510</C1><C2>1262391.227</C2></COORD><COORD><C1>2698984.684</C1><C2>1262406.307</C2></COORD><COORD><C1>2698993.863</C1><C2>1262415.486</C2></COORD></POLYLINE></Geometry></City_V1.Constructions.Street>
</City_V1.Constructions>
<City_V1.Nature BID="6cc059e9-0182-4c9f-9208-28be3c172471">
<City_V1.Nature.Parks TID="3445b04b-a4ed-4a03-bb09-c9e52134cad6"><Name>Parque de la Musique</Name><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD><COORD><C1>2698932.231</C1><C2>1262487.828</C2></COORD><COORD><C1>2698934.417</C1><C2>1262440.620</C2></COORD><COORD><C1>2698963.922</C1><C2>1262442.368</C2></COORD><COORD><C1>2698963.484</C1><C2>1262465.754</C2></COORD><COORD><C1>2698982.968</C1><C2>1262470.701</C2></COORD><COORD><C1>2698980.969</C1><C2>1262480.834</C2></COORD><COORD><C1>2698959.332</C1><C2>1262489.795</C2></COORD><COORD><C1>2698940.099</C1><C2>1262488.920</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Nature.Parks>
<City_V1.Nature.Parks TID="d7e73464-f27e-4d2d-848c-66735f3fe5af"><Name>Parque des Fleurs</Name><Geometry><SURFACE><BOUNDARY><POLYLINE><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD><COORD><C1>2698901.415</C1><C2>1262410.460</C2></COORD><COORD><C1>2698903.164</C1><C2>1262439.309</C2></COORD><COORD><C1>2698886.335</C1><C2>1262452.203</C2></COORD><COORD><C1>2698866.447</C1><C2>1262410.241</C2></COORD></POLYLINE></BOUNDARY></SURFACE></Geometry></City_V1.Nature.Parks>
</City_V1.Nature>
</DATASECTION>
</TRANSFER>
```

We create the dataset "Besźel" with the Dataset Manager and update the data with the following command.
```
java -jar /home/freddy/ili2pg-4.6.1.jar --update --dbhost localhost --dbport 5432 --dbusr postgres --dbpwd ****** --dbdatabase freds_bakery --dbschema thecityandthecity --importTid --importBid --dataset Besźel /home/dave/dev/gh_signedav/usabilitydave/referencedata/TheCity_V1-beszel.xtf
```

```
 t_id | datasetname
------+-------------
    1 | Baseset
    4 | Ul Qoma
   28 | Besźel

 t_id | dataset |         topic         |              t_ili_tid               |      attachmentkey       | domains
------+---------+-----------------------+--------------------------------------+--------------------------+---------
    2 |       1 | City_V1.Constructions | b99939c9-8567-4eef-9ff7-451f5ed38f8d | Qgis Model Baker         |
    3 |       1 | City_V1.Nature        | d310e3c0-db59-43f6-9982-7b49923d2a96 | Qgis Model Baker         |
    5 |       4 | City_V1.Constructions | d861b84f-7068-43d0-b8c1-f0d2f200b075 | TheCity_V1-ulqoma.xtf-5  |
   23 |       4 | City_V1.Nature        | 8d4b122c-3582-447c-b933-3175674151e0 | TheCity_V1-ulqoma.xtf-5  |
   29 |      28 | City_V1.Constructions | 7dc3c035-b281-412f-9ba3-c69481054974 | TheCity_V1-beszel.xtf-29 |
   40 |      28 | City_V1.Nature        | 6cc059e9-0182-4c9f-9208-28be3c172471 | TheCity_V1-beszel.xtf-29 |

 t_id | t_basket |              t_ili_tid               |        aname        |                                                                                                                         ageometry
------+----------+--------------------------------------+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   19 |        5 | 7bcc0efd-1d81-400a-8dfb-1f17f4e72287 | Main Route          | 01020000200808000006000000AAF1D26D579744410AD7A350A9433341931804265897444177BE9FDA9C4333417368911D5A974441D9CEF7D397433341894160355B974441EC51B89E684333413BDF4F6D5B9744411F85EB315A43334114AE47C15B97444108AC1C3A37433341
   20 |        5 | 3eab5bd9-3dc8-4e73-81f1-b8d8cfaba748 | Tiny Route          | 010200002008080000070000003BDF4F6D5B9744411F85EB315A4333417B14AE87629744419A9999995C433341F853E3656A974441BC74931860433341931804F6699744417D3F355E6A43334146B6F3BD69974441DD2406C1814333418B6CE77B739744416ABC74B386433341986E12A3769744415A643BBF88433341
   21 |        5 | b5c3d22c-974f-49c9-b361-d85dbdc4000b | Park Way            | 01020000200808000003000000F853E3656A974441BC749318604333415C8FC2F56C974441448B6CC74143334152B81E756D9744414260E5D03B433341
   22 |        5 | d954d3c4-ec24-44cd-af2d-d7f3af781a18 | Mullholland Drive   | 01020000200808000003000000AE47E12A43974441D9CEF73374433341B6F3FD944B974441BE9F1A4F674333413BDF4F6D5B9744411F85EB315A433341
   37 |       29 | 451cfaee-299f-4b72-bcc2-6b6a097ee0d2 | Rue des Fleurs      | 01020000200808000004000000C74B3739399744410E2DB23D4A433341AE47E12A43974441D9CEF73374433341F6285C3F529744415839B408A643334146B6F3CD589744412DB29D2FAA433341
   38 |       29 | d6ed2502-7161-4e04-8589-3cd6c84a51e0 | Rue de la Musique   | 0102000020080800000600000046B6F3CD589744412DB29D2FAA4333415EBA49CC5F974441D578E906AD4333413108AC0C5E974441B81E85EB98433341DBF97EAA67974441B81E85CB994333412731087C72974441250681D590433341B4C876EE78974441FA7E6A7C4F433341
   39 |       29 | 1f47c793-326a-47ba-b076-8ae9f25b2990 | Rue de neuf Soleils | 01020000200808000007000000C74B3739399744410E2DB23D4A43334152B81EB54A9744415C8FC2754A4333412B8716094B974441A4703DCA364333410AD7A3004D974441DBF97E0A3543334114AE47C15B97444108AC1C3A37433341DF4F8D5774974441508D974E46433341B4C876EE78974441FA7E6A7C4F433341

 t_id | t_basket |              t_ili_tid               |        aname         |                                                                                                                                                                                             ageometry
------+----------+--------------------------------------+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   24 |       23 | dbe968d7-e41d-4c14-9560-c2161bea76db | UlQoma Park          | 01030000200808000001000000060000003BDF4F6D5B9744411F85EB315A4333417B14AE87629744419A9999995C433341F853E3656A974441BC749318604333415C8FC2F56C974441448B6CC74143334114AE47C15B97444108AC1C3A374333413BDF4F6D5B9744411F85EB315A433341
   25 |       23 | 574eed9f-4cef-4747-8cbb-5e8519898626 | Big Green            | 010300002008080000010000000A000000273108BC4F9744415C8FC2F58F433341508D97BE55974441986E12C39B433341931804265897444177BE9FDA9C4333417368911D5A974441D9CEF7D39743334179E926E15A9744416ABC74D3764333416666666656974441B81E852B76433341E7FBA92156974441D9CEF7935E433341B6F3FD944B974441BE9F1A4F67433341AC1C5AA447974441BC7493586D433341273108BC4F9744415C8FC2F58F433341
   26 |       23 | d92d5cde-7ef3-48e8-b6cc-e370a5cba64d | Selmas Park          | 010300002008080000010000000B0000005839B4885B974441D34D62D04E4333413BDF4F6D5B9744411F85EB315A433341B6F3FD944B974441BE9F1A4F6743334152B81EB54A9744415C8FC2754A4333412B8716094B974441A4703DCA364333410AD7A3004D974441DBF97E0A3543334114AE47C15B97444108AC1C3A374333416F1283B05B97444139B4C8363E433341D34D62E04D9744415839B4E83C433341D34D62E04D974441CDCCCC2C4E4333415839B4885B974441D34D62D04E433341
   41 |       40 | 3445b04b-a4ed-4a03-bb09-c9e52134cad6 | Parque de la Musique | 01030000200808000001000000090000003108AC0C5E974441B81E85EB984333417368911D5A974441D9CEF7D397433341894160355B974441EC51B89E68433341931804F6699744417D3F355E6A43334146B6F3BD69974441DD2406C1814333418B6CE77B739744416ABC74B3864333412731087C72974441250681D590433341DBF97EAA67974441B81E85CB994333413108AC0C5E974441B81E85EB98433341
   42 |       40 | d7e73464-f27e-4d2d-848c-66735f3fe5af | Parque des Fleurs    | 0103000020080800000100000005000000C74B3739399744410E2DB23D4A43334152B81EB54A9744415C8FC2754A433341B6F3FD944B974441BE9F1A4F67433341AE47E12A43974441D9CEF73374433341C74B3739399744410E2DB23D4A433341
(5 rows)

```

## Dataset Selector
