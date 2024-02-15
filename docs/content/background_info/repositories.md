## What is a Geodata Repository?

In Model Baker, implemented INTERLIS models can be found automatically via the web. These repositories are, in addition to the federal repository, also a large number of cantonal repositories. Thus, the models of the entire Swiss Geodata Catalog, which are available in INTERLIS format, are available to us in Model Baker.


## Structure

http://models.interlis.ch serves as entry point. The file `ilimodels.xml` is the index over all the models that can be found on the same server.
Other repositories/servers can be linked in `ilisites.xml`. With this a network of repositories are provided were models can be found.
### ilimodels.xml
The file data are based on the INTERLIS model `IliRepository09`. It contains objects of the class `ModelMetadata` where a model name and a file path is defined. Those files are on the same sever/repository.

```
<IliRepository09.RepositoryIndex.ModelMetadata TID="004398">
    <Name>Wildruhezonen_LV95_V2_1</Name>
    <SchemaLanguage>ili2_3</SchemaLanguage>
    <File>BAFU/Wildruhezonen_V2_1.ili</File>
    <Version>2020-04-21</Version>
    <publishingDate>2020-04-21</publishingDate>
    <dependsOnModel>
        [...]
        <IliRepository09.ModelName_>
            <value>Wildruhezonen_Codelisten_V2_1</value>
        </IliRepository09.ModelName_>
    </dependsOnModel>
    <precursorVersion>2020-01-23</precursorVersion>
    <Tags>195.1,195.2</Tags>
    <Issuer>https://models.geo.admin.ch/BAFU/</Issuer>
    <technicalContact>mailto:gis@bafu.admin.ch</technicalContact>
    <furtherInformation>https://www.bafu.admin.ch/geodatenmodelle</furtherInformation>
    <md5>fe4b13eee175fb7eaf558534cdf2b7a8</md5>
</IliRepository09.RepositoryIndex.ModelMetadata>
```

### ilisites.xml
The file data are based on the INTERLIS model `IliSite09`. It contains objects of the class `SiteMetadata` where a path to another repository is defined.

```
http://models.interlis.ch/ilisite.xml
|- http://models.geo.admin.ch/ilisite.xml
|- http://models.geo.kgk-cgc.ch/ilisite.xml
   |- http://models.geo.ai.ch/ilisite.xml
   |- http://models.geo.ai.ch/ilisite.xml
   |- https://models.geo.ar.ch/ilisite.xml
   |- http://models.geo.be.ch/ilisite.xml
   |- http://models.geo.bl.ch/ilisite.xml
   |- ...
|- https://repositorio.proadmintierra.info/ilisite.xml
```
