<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" minScale="1e+08" version="3.19.0-Master" readOnly="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal durationField="" fixedDuration="0" mode="0" startExpression="" durationUnit="min" startField="" accumulate="0" endField="" enabled="0" endExpression="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>"nbident"</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend type="default-vector"/>
  <referencedLayers>
    <relation id="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey" referencingLayer="Parzellenidentifikation_cd9ebcfe_0ea0_4b39_964b_d1de0051e228" referencedLayer="Belasteter_Standort__Geo_Lage_Polygon__c79ae4df_f15d_44ee_9cf0_2df45095f88f" providerKey="postgres" name="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey" layerId="Belasteter_Standort__Geo_Lage_Polygon__c79ae4df_f15d_44ee_9cf0_2df45095f88f" strength="Association" layerName="Belasteter_Standort (Geo_Lage_Polygon)" dataSource="dbname='bakery' host=localhost user='postgres' key='t_id' srid=2056 type=MultiPolygon checkPrimaryKeyUnicity='1' table=&quot;usabilityhub_opengisch_010&quot;.&quot;belasteter_standort&quot; (geo_lage_polygon)">
      <fieldRef referencedField="t_id" referencingField="belasteter_standort_parzellenverweis"/>
    </relation>
    <relation id="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" referencingLayer="Parzellenidentifikation_cd9ebcfe_0ea0_4b39_964b_d1de0051e228" referencedLayer="Belasteter_Standort__Geo_Lage_Punkt__16dede49_cf0e_4af1_9ab0_cf39d75d168f" providerKey="postgres" name="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey" layerId="Belasteter_Standort__Geo_Lage_Punkt__16dede49_cf0e_4af1_9ab0_cf39d75d168f" strength="Association" layerName="Belasteter_Standort (Geo_Lage_Punkt)" dataSource="dbname='bakery' host=localhost user='postgres' key='t_id' srid=2056 type=Point checkPrimaryKeyUnicity='1' table=&quot;usabilityhub_opengisch_010&quot;.&quot;belasteter_standort&quot; (geo_lage_punkt)">
      <fieldRef referencedField="t_id" referencingField="belasteter_standort_parzellenverweis"/>
    </relation>
  </referencedLayers>
  <fieldConfiguration>
    <field name="t_id" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_seq" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nbident" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="parzellennummer" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="belasteter_standort_parzellenverweis" configurationFlags="None">
      <editWidget type="RelationReference">
        <config>
          <Option type="Map">
            <Option type="bool" value="true" name="AllowAddFeatures"/>
            <Option type="bool" value="true" name="AllowNULL"/>
            <Option type="bool" value="false" name="MapIdentification"/>
            <Option type="bool" value="true" name="OrderByValue"/>
            <Option type="bool" value="false" name="ReadOnly"/>
            <Option type="QString" value="dbname='bakery' host=localhost user='postgres' key='t_id' srid=2056 type=Point checkPrimaryKeyUnicity='1' table=&quot;usabilityhub_opengisch_010&quot;.&quot;belasteter_standort&quot; (geo_lage_punkt)" name="ReferencedLayerDataSource"/>
            <Option type="QString" value="Belasteter_Standort__Geo_Lage_Punkt__16dede49_cf0e_4af1_9ab0_cf39d75d168f" name="ReferencedLayerId"/>
            <Option type="QString" value="Belasteter_Standort (Geo_Lage_Punkt)" name="ReferencedLayerName"/>
            <Option type="QString" value="postgres" name="ReferencedLayerProviderKey"/>
            <Option type="QString" value="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" name="Relation"/>
            <Option type="bool" value="false" name="ShowForm"/>
            <Option type="bool" value="false" name="ShowOpenFormButton"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="t_id" index="0" name=""/>
    <alias field="t_seq" index="1" name=""/>
    <alias field="nbident" index="2" name="NBIdent"/>
    <alias field="parzellennummer" index="3" name="Parzellennummer"/>
    <alias field="belasteter_standort_parzellenverweis" index="4" name="Parzellenverweis"/>
  </aliases>
  <defaults>
    <default expression="" field="t_id" applyOnUpdate="0"/>
    <default expression="" field="t_seq" applyOnUpdate="0"/>
    <default expression="" field="nbident" applyOnUpdate="0"/>
    <default expression="" field="parzellennummer" applyOnUpdate="0"/>
    <default expression="" field="belasteter_standort_parzellenverweis" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="t_id" constraints="3" unique_strength="1" exp_strength="0" notnull_strength="1"/>
    <constraint field="t_seq" constraints="0" unique_strength="0" exp_strength="0" notnull_strength="0"/>
    <constraint field="nbident" constraints="1" unique_strength="0" exp_strength="0" notnull_strength="1"/>
    <constraint field="parzellennummer" constraints="1" unique_strength="0" exp_strength="0" notnull_strength="1"/>
    <constraint field="belasteter_standort_parzellenverweis" constraints="0" unique_strength="0" exp_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="t_id" exp="" desc=""/>
    <constraint field="t_seq" exp="" desc=""/>
    <constraint field="nbident" exp="" desc=""/>
    <constraint field="parzellennummer" exp="" desc=""/>
    <constraint field="belasteter_standort_parzellenverweis" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column width="-1" type="field" name="t_id" hidden="0"/>
      <column width="-1" type="field" name="t_seq" hidden="0"/>
      <column width="-1" type="field" name="nbident" hidden="0"/>
      <column width="-1" type="field" name="parzellennummer" hidden="0"/>
      <column width="-1" type="field" name="belasteter_standort_parzellenverweis" hidden="0"/>
      <column width="-1" type="actions" hidden="1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>tablayout</editorlayout>
  <attributeEditorForm>
    <attributeEditorContainer visibilityExpression="" visibilityExpressionEnabled="0" name="General" showLabel="1" columnCount="1" groupBox="0">
      <attributeEditorField index="4" name="belasteter_standort_parzellenverweis" showLabel="1"/>
      <attributeEditorField index="2" name="nbident" showLabel="1"/>
      <attributeEditorField index="3" name="parzellennummer" showLabel="1"/>
    </attributeEditorContainer>
  </attributeEditorForm>
  <editable>
    <field name="belasteter_standort_parzellenverweis" editable="1"/>
    <field name="nbident" editable="1"/>
    <field name="parzellennummer" editable="1"/>
    <field name="t_id" editable="1"/>
    <field name="t_seq" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="belasteter_standort_parzellenverweis"/>
    <field labelOnTop="0" name="nbident"/>
    <field labelOnTop="0" name="parzellennummer"/>
    <field labelOnTop="0" name="t_id"/>
    <field labelOnTop="0" name="t_seq"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="belasteter_standort_parzellenverweis"/>
    <field reuseLastValue="0" name="nbident"/>
    <field reuseLastValue="0" name="parzellennummer"/>
    <field reuseLastValue="0" name="t_id"/>
    <field reuseLastValue="0" name="t_seq"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>nbident || ' - '  || "parzellennummer" </previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
