# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
                              (C) 2016 by OPENGIS.ch
    email                :    gcarrillo@linuxmail.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import re

from projectgenerator.libqgsprojectgen.dataobjects.relations import Relation

class DomainRelationGenerator:
    """TODO: remove when ili2db issue #19 is solved"""

    def __init__(self, db_connector, inheritance):
        self._db_connector = db_connector
        self.inheritance = inheritance
        self.debug = False

    def get_domain_relations_info(self, layers):
        domains = [layer.name for layer in layers if layer.is_domain]
        if self.debug:
            print("domains:", domains)
        if not domains:
            return []

        layer_map = dict()
        for layer in layers:
            if layer.name not in layer_map.keys():
                layer_map[layer.name] = list()
            layer_map[layer.name].append(layer)

        domainili_domaindb_mapping = self._get_iliname_dbname_mapping(
            domains)
        domains_ili_pg = dict()
        for record in domainili_domaindb_mapping:
            domains_ili_pg[record['iliname']] = record['sqlname']
        if self.debug:
            print("domains_ili_pg:", domains_ili_pg)

        model_records = self._get_models()
        models = dict()
        models_info = dict()
        extended_classes = dict()
        for record in model_records:
            models[record['modelname'].split("{")[0]] = record['content']

        bags_of_enum_info = dict()
        for k, v in models.items():
            parsed = self.parse_model(v, list(domains_ili_pg.keys()))
            models_info.update(parsed[0])
            extended_classes.update(parsed[1])
            bags_of_enum_info.update(parsed[2])

        if self.debug:
            print("Classes with domain attrs:", len(models_info))
            print("BAGS OF ENUM", len(bags_of_enum_info), bags_of_enum_info)

        # Map class ili name with its correspondent pg name
        # Take into account classes with domain attrs and those that extend other classes,
        # because parent classes might have domain attrs that will be
        # transfered to children
        class_records = self._get_classili_classdb_mapping(
            models_info, extended_classes)
        classes_ili_pg = dict()
        for record in class_records:
            classes_ili_pg[record['iliname']] = record['sqlname']
        if self.debug:
            print("classes_ili_pg:", classes_ili_pg)

        # Now deal with extended classes
        models_info_with_ext = {}
        for iliclass in models_info:
            models_info_with_ext[iliclass] = self.get_ext_dom_attrs(iliclass, models_info, extended_classes,
                                                                    self.inheritance)
        for iliclass in extended_classes:
            if iliclass not in models_info_with_ext:
                # Take into account classes which only inherit attrs with domains, but don't have their own nor EXTEND attrs
                # Only relevant for smart2Inheritance, since for
                # smart1Inheritance this will return an empty dict {}
                models_info_with_ext[iliclass] = self.get_ext_dom_attrs(iliclass, models_info, extended_classes,
                                                                        self.inheritance)

        # Map attr ili name and owner (pg class name) with its correspondent
        # attr pg name
        attr_records = self._get_attrili_attrdb_mapping(models_info_with_ext)
        attrs_ili_pg_owner = dict()
        for record in attr_records:
            if record['owner'] in attrs_ili_pg_owner:
                attrs_ili_pg_owner[record['owner']].update(
                    {record['iliname']: record['sqlname']})
            else:
                attrs_ili_pg_owner[record['owner']] = {
                    record['iliname']: record['sqlname']}
        if self.debug:
            print("attrs_ili_pg_owner:", attrs_ili_pg_owner)

        # Create relations
        relations = list()
        attrs_ili = [k for v in attrs_ili_pg_owner.values() for k in v]
        for iliclass, dict_attr_domain in models_info_with_ext.items():
            for iliattr, ilidomain in dict_attr_domain.items():
                if iliclass in classes_ili_pg and ilidomain in domains_ili_pg and iliattr in attrs_ili:
                    if classes_ili_pg[iliclass] in layer_map.keys() and domains_ili_pg[ilidomain] in layer_map.keys() and \
                            classes_ili_pg[iliclass] in attrs_ili_pg_owner:
                        if iliattr in attrs_ili_pg_owner[classes_ili_pg[iliclass]]:
                            for referencing_layer in layer_map[classes_ili_pg[iliclass]]:
                                for referenced_layer in layer_map[domains_ili_pg[ilidomain]]:
                                    # Might be that due to ORM mapping, a class is not
                                    # in mapped_layers
                                    relation = Relation()
                                    relation.referencing_layer = referencing_layer
                                    relation.referenced_layer = referenced_layer
                                    relation.referencing_field = attrs_ili_pg_owner[
                                        classes_ili_pg[iliclass]][iliattr]
                                    relation.referenced_field = self._db_connector.iliCodeName
                                    relation.name = "{}_{}_{}_{}".format(classes_ili_pg[iliclass],
                                                                         attrs_ili_pg_owner[
                                                                             classes_ili_pg[iliclass]][iliattr],
                                                                         domains_ili_pg[
                                                                             ilidomain],
                                                                         self._db_connector.iliCodeName)

                                    if self.debug:
                                        print("Relation:", relation.name)
                                    relations.append(relation)

        if self.debug:
            print("final_models_info:", models_info_with_ext)
        if self.debug:
            print("extended_classes:", extended_classes)
        if self.debug:
            print("Num of Relations:", len(relations))


        # BAG OF ENUM handling
        # bags_info = {iliclass: {iliattribute: [cardinalities=[1, *], ilistructure}}
        # structures_ili_pg = {ilistructure: dbstructure}
        # structure_domain_attr = {dbstructure: [iliname, sqlname]}
        # return {layer_name: [dbattribute, cardinality, dbdomain]}

        structures = [layer.name for layer in layers if layer.is_structure]
        if self.debug:
            print("Structures:", structures)

        structureili_structuredb_mapping = self._get_iliname_dbname_mapping(
            structures)
        structures_ili_pg = dict()
        for record in structureili_structuredb_mapping:
            structures_ili_pg[record['iliname']] = record['sqlname']
        if self.debug:
            print("structures_ili_pg:", structures_ili_pg)

        owners = list()
        for class_name, bag_of_enum_info in bags_of_enum_info.items():
            for attribute, cardinality_structure in bag_of_enum_info.items():
                owners.append(structures_ili_pg[cardinality_structure[1]])

        if self.debug:
            print("OWNERS:",owners)
        structure_domain_attr_ili_sql = self._get_attrili_attrdb_mapping_by_owner(owners)
        structure_domain_attr = dict()
        for record in structure_domain_attr_ili_sql:
            structure_domain_attr[record['owner']] = [
                record['iliname'],
                record['sqlname']
            ]

        # Get the domain (extracted by the parser) corresponding to the structure
        bags_of_enum = dict()
        for class_name, bag_of_enum_info in bags_of_enum_info.items():
            for attribute, cardinality_structure in bag_of_enum_info.items():
                cardinality, structure = cardinality_structure
                if structure in models_info_with_ext:
                    structure_attribute = structure_domain_attr[structures_ili_pg[structure]][0] # iliname
                    if structure_attribute in models_info_with_ext[structure]:
                        ilidomain = models_info_with_ext[structure][structure_attribute] # ilidomain
                        if structure in classes_ili_pg and ilidomain in domains_ili_pg and structure_attribute in attrs_ili:
                            if classes_ili_pg[structure] in layer_map.keys() and domains_ili_pg[ilidomain] in layer_map.keys() and \
                                classes_ili_pg[structure] in attrs_ili_pg_owner:
                                #bags_of_enum[]
                                print("BAG OF ENUM!!!", classes_ili_pg[class_name], attribute, cardinality, domains_ili_pg[ilidomain])

        return relations

    def parse_model(self, model_content, domains):
        re_comment = re.compile(r'\s*/\*')  # /* comment
        re_end_comment = re.compile(r'\s*\*/')  # comment */
        re_oneline_comment = re.compile(r'\s*/\*.*\*/')  # /* comment */
        re_inline_comment = re.compile(r'^\s*!!(?!@)')  # !! comment

        # MODEL Catastro_COL_ES_V_2_0_20170331 (es)
        re_model = re.compile(r'\s*MODEL\s*([\w\d_-]+).*')
        # TOPIC Catastro_Registro [=]
        re_topic = re.compile(r'\s*TOPIC\s*([\w\d_-]+).*')
        re_structure = re.compile(r'\s*STRUCTURE\s*([\w\d_-]+)\s*\=.*') # STRUCTURE StructureName =
        re_class = re.compile(
            r'\s*CLASS\s*([\w\d_-]+)\s*[\(ABSTRACT\)]*\s*[EXTENDS]*\s*([\w\d_-]*).*')  # CLASS ClassName (ABSTRACT) [EXTENDS] [BaseClassName] [=]
        re_class_extends = re.compile(
            r'\s*EXTENDS\s*([\w\d_\-\.]+)\s*\=.*')  # EXTENDS BaseClassName =
        re_inline_enum_start = re.compile(
            r'\s*([\w\d_-]+)\s*:\s*[MANDATORY]*\s*\(.*')
        re_inline_enum_end = re.compile(r'\s*\);.*')
        re_inline_enum_oneline = re.compile(
            r'\s*([\w\d_-]+)\s*:\s*[MANDATORY]*\s*\(.*\);.*')
        # Typ: BAG {1..*} OF EI_Punkt_Typ;
        re_bag_of = re.compile(r'\s*([\w\d_-]+)\s*:\s*BAG\s*\{(.*)\}\s*OF\s*([\w\d_-]+);.*')
        re_mapping_array = re.compile(r'\s*!!@ili2db.mapping=ARRAY.*')
        re_end_structure = None  # END StructureName;
        re_end_class = None  # END ClassName;
        re_end_topic = None  # END TopicName;
        re_end_model = None  # END ModelName;

        currently_inside_comment = False
        current_line_bag_of_enum = False
        current_model = ''
        current_structure = ''
        current_topic = ''
        current_class = ''
        within_inline_enum = False
        attributes = dict()
        models_info = dict()
        extended_classes = dict()
        bags_of_enum = dict()
        bClassJustFound = False  # Flag to search for EXTENDS classes
        local_names = dict()

        for line in model_content.splitlines():

            if not currently_inside_comment:
                result = re_comment.search(line)
                if result:
                    result = re_oneline_comment.search(line)
                    if not result:
                        currently_inside_comment = True

                    continue
            else:
                result = re_end_comment.search(line)
                if result:
                    currently_inside_comment = False

                continue # Whether comment ends or not, we are done in this line

            if re_inline_comment.search(line):
                continue # Inline comment at the start of the line

            if not current_model:
                result = re_model.search(line)
                if result:
                    current_model = result.group(1)
                    re_end_model = re.compile(
                        r'.*END\s*{}\..*'.format(current_model))  # END TopicName;
                    if self.debug:
                        print("\nMODEL encontrado", current_model)

            else:  # There is a current_model

                if not current_topic:
                    result = re_topic.search(line)
                    if result:
                        current_topic = result.group(1)
                        if self.debug:
                            print("TOPIC encontrada", current_topic)
                        re_end_topic = re.compile(
                            r'\s*END\s*{};.*'.format(current_topic))  # END TopicName;

                        if self.debug:
                            print("Call to extract_local_names_from_domains: {} | {} | {}".format(
                                domains,
                                current_model,
                                current_topic
                            ))
                        local_names = self.extract_local_names_from_domains(
                            domains, current_model, current_topic)
                        domains_with_local = [name for name_list in local_names.values() for name in
                                              name_list] + domains
                        if self.debug:
                            print("domains_with_local:", domains_with_local)
                        continue
                else:  # There is a current_topic

                    if not current_structure:
                        result = re_structure.search(line)
                        if result:
                            current_structure = result.group(1)
                            if self.debug:
                                print("Structure encontrada", current_structure)
                            attributes = dict()
                            re_end_structure = re.compile(
                                r'\s*END\s*{};.*'.format(current_structure))  # END StructureName;
                            continue
                    else:
                        attribute = {res.group(1): d for d in domains_with_local for res in
                                     [re.search(r'\s*([\w\d_-]+).*:.*\s{};.*'.format(d), line)] if res}

                        if attribute:
                            if self.debug:
                                print("MATCH (STRUCTURE):", attribute)
                            old_key = list(attribute.keys())[0]  # Not qualified name
                            new_key = "{}.{}.{}.{}".format(current_model, current_topic, current_structure,
                                                           old_key)  # Fully qualified name
                            attr_value = list(attribute.values())[0]
                            if attr_value not in domains:  # Match was vs. local name, find its corresponding qualified name
                                for k, v in local_names.items():
                                    if attr_value in v:
                                        attribute[old_key] = k
                                        break
                            attribute[new_key] = attribute.pop(old_key)
                            attributes.update(attribute)
                            continue

                        result = re_end_structure.search(line)
                        if result:
                            if attributes:
                                models_info.update(
                                    {'{}.{}.{}'.format(current_model, current_topic, current_structure): attributes})
                            if self.debug:
                                print("END Structure encontrada", current_structure)
                            current_structure = ''
                            continue

                    if not current_class:  # Go for classes
                        result = re_class.search(line)
                        if result:
                            current_class = result.group(1)
                            if self.debug:
                                print("Class encontrada", current_class)
                            attributes = dict()
                            re_end_class = re.compile(
                                r'\s*END\s*{};.*'.format(current_class))  # END ClassName;
                            bClassJustFound = True

                            # Possible EXTENDS
                            if len(result.groups()) > 1 and result.group(2):
                                extended_classes["{}.{}.{}".format(current_model, current_topic,
                                                                   current_class)] = self.make_full_qualified(
                                    result.group(2), 'class', current_model, current_topic)
                                if self.debug:
                                    print("EXTENDS->",
                                          self.make_full_qualified(result.group(2), 'class', current_model,
                                                                   current_topic))

                            continue
                    else:  # There is a current_class, go for attributes
                        if bClassJustFound:  # Search for extended classes
                            bClassJustFound = False
                            result = re_class_extends.search(line)
                            if result:
                                extended_classes["{}.{}.{}".format(current_model, current_topic,
                                                                   current_class)] = self.make_full_qualified(
                                    result.group(1), 'class', current_model, current_topic)
                                if self.debug:
                                    print("EXTENDS->",
                                          self.make_full_qualified(result.group(1), 'class', current_model,
                                                                   current_topic))
                                continue

                        # Look for BAG {} OF ENUM lines
                        if not current_line_bag_of_enum:
                            result = re_mapping_array.search(line)
                            if result:
                                current_line_bag_of_enum = True
                                continue
                        else:
                            current_line_bag_of_enum = False
                            result = re_bag_of.search(line)
                            if result:
                                attr_name = '{}.{}.{}.{}'.format(current_model, current_topic, current_class, result.group(1))
                                structure_name = result.group(3)
                                if not '.' in structure_name:
                                    structure_name = '{}.{}.{}'.format(current_model, current_topic, structure_name)

                                class_name = '{}.{}.{}'.format(current_model, current_topic, current_class)
                                if not class_name in bags_of_enum:
                                    bags_of_enum[class_name] = {attr_name: [result.group(2), structure_name]}
                                else:
                                    bags_of_enum[class_name][attr_name] = [result.group(2), structure_name]
                                continue

                        # Go for attributes
                        attribute = {res.group(1): d for d in domains_with_local for res in
                                     [re.search(r'\s*([\w\d_-]+).*:.*\s{};.*'.format(d), line)] if res}

                        if attribute:
                            if self.debug:
                                print("MATCH:", attribute)
                            old_key = list(attribute.keys())[
                                0]  # Not qualified name
                            new_key = "{}.{}.{}.{}".format(current_model, current_topic, current_class,
                                                           old_key)  # Fully qualified name
                            attr_value = list(attribute.values())[0]
                            if attr_value not in domains:  # Match was vs. local name, find its corresponding qualified name
                                for k, v in local_names.items():
                                    if attr_value in v:
                                        attribute[old_key] = k
                                        break
                            attribute[new_key] = attribute.pop(old_key)
                            attributes.update(attribute)
                            continue

                        if within_inline_enum:
                            result = re_inline_enum_end.search(line)
                            if result:
                                within_inline_enum = False
                                continue

                        # Look for inline ENUM definitions
                        result = re_inline_enum_start.search(line)
                        if result:
                            # result.group(1) is the attribute name
                            if self.debug:
                                print("INLINE ENUM:", "{}.{}".format(current_class, result.group(1)))
                            name = '{}.{}.{}.{}'.format(current_model, current_topic, current_class, result.group(1))
                            # Attribute and domain name match for inline ENUMs
                            attributes[name] = name

                            # Check if the whole ENUM is defined in one line
                            result = re_inline_enum_oneline.search(line)
                            if not result:
                                within_inline_enum = True

                            continue

                        result = re_end_class.search(line)
                        if result:
                            if attributes:
                                models_info.update(
                                    {'{}.{}.{}'.format(current_model, current_topic, current_class): attributes})
                            if self.debug:
                                print("END Class encontrada", current_class)
                            current_class = ''
                            continue

                    result = re_end_topic.search(line)
                    if result:
                        current_topic = ''

                result = re_end_model.search(line)
                if result:
                    if self.debug:
                        print("END model encontrado", current_model, "\n")
                    current_model = ''

        return [models_info, extended_classes, bags_of_enum]

    def extract_local_names_from_domains(self, domains, current_model, current_topic):
        """
        ili files may contain fully qualified domains assigned to attributes, but if
        domains are local (domain or topic-wise), domains might be assigned only
        with its name. This function builds local names (with no model and topic
        name, or without model name) for each domain name in 'domains' input. For
        instance: from a domain name "MODEL.TOPIC.DOMAIN", this function returns
        {MODEL: [DOMAIN, TOPIC.DOMAIN]} Order is relevant, since later matches in a
        search will overwrite previous ones (better to preserve more-qualified
        matches).
        """
        local_names = dict()
        for domain in domains:
            local_names_list = list()
            if domain.startswith('{}.'.format(current_model)) or \
               domain.startswith('{}.{}.'.format(current_model, current_topic)) or \
               domain.startswith('INTERLIS'):
                array = domain.split(".")
                if len(array) > 0:
                    local_names_list.append(array[-1])
                if len(array) > 1:
                    local_names_list.append(
                        '{}.{}'.format(array[-2], array[-1]))
                if local_names_list:
                    local_names[domain] = local_names_list
        return local_names

    def make_full_qualified(self, name, level, current_model, current_topic, current_class=None):
        parents = [current_model, current_topic, current_class]
        len_parents = len(parents)
        name_parts = name.split(".")
        # 3 levels (even 2, but not handling that case yet)
        if level == 'class':
            name_parts = parents[0:len_parents - len(name_parts)] + name_parts

        return ".".join(name_parts)

    def get_ext_dom_attrs(self, iliclass, models_info, extended_classes, inheritance):
        if inheritance == 'smart1':
            # Use smart 2 first to get domain attributes from parents (we
            # really need them) and only then use smart 1
            tmp_models_info = models_info
            if iliclass in tmp_models_info:
                tmp_models_info[iliclass].update(self.get_ext_dom_attrs_smart2(
                    iliclass, models_info, extended_classes))
            else:
                tmp_models_info[iliclass] = self.get_ext_dom_attrs_smart2(
                    iliclass, models_info, extended_classes)
            return self.get_ext_dom_attrs_smart1(iliclass, tmp_models_info, extended_classes)
        elif inheritance == 'smart2':
            return self.get_ext_dom_attrs_smart2(iliclass, models_info, extended_classes)
        else:  # No smart inheritance?
            return {}

    def get_ext_dom_attrs_smart1(self, iliclass, models_info, extended_classes):
        """
        Returns a dict for input iliclass with its original attr:domain pairs
        plus all attr:domain pairs from children classes
        """
        children_domain_attrS = dict()
        if iliclass in extended_classes.values():  # Does current class have children?
            for child, parent in extended_classes.items():  # Top-bottom, we might find several children
                if parent == iliclass:
                    children_domain_attrS.update(
                        self.get_ext_dom_attrs_smart1(child, models_info, extended_classes))  # Recursion
                    # In the last line, if two children share an atributte that
                    # is not in parent, the latest class visited will overwrite
                    # previously visited classes
        else:
            return models_info[iliclass] if iliclass in models_info else {}
        all_attrs = models_info[iliclass] if iliclass in models_info else {}

        for children_domain_attr, domain in children_domain_attrS.items():
            # smart1Inheritance: Pass child class attributes to parents, but
            # don't overwrite extended attrs
            if children_domain_attr not in all_attrs:
                all_attrs[children_domain_attr] = domain
        return all_attrs

    def get_ext_dom_attrs_smart2(self, iliclass, models_info, extended_classes):
        """
        Returns a dict for input iliclass with its original attr:domain pairs
        plus all inherited attr:domain pairs
        """
        if iliclass in extended_classes:  # Does current class have parents?
            parents_domain_attrS = self.get_ext_dom_attrs_smart2(extended_classes[iliclass], models_info,
                                                                 extended_classes)  # Recursion
        else:
            return models_info[iliclass] if iliclass in models_info else {}
        all_attrs = models_info[iliclass] if iliclass in models_info else {}

        unqualified_attrs = {k.split(".")[-1]: k for k in all_attrs.keys()}

        for parents_domain_attr, domain in parents_domain_attrS.items():
            # smart2Inheritance: Pass parent attributes to child if they are missing.
            # If they exist, overwrite keys (i.e., parent_domain_attr:
            # child_domain)
            parents_unqualified_attr = parents_domain_attr.split(".")[-1]

            if parents_unqualified_attr not in unqualified_attrs:
                all_attrs[parents_domain_attr] = domain
            else:  # Extended, use parent's attribute name with child domain name
                if unqualified_attrs[parents_unqualified_attr] in all_attrs:
                    tmpDomain = all_attrs[
                        unqualified_attrs[parents_unqualified_attr]]
                    del all_attrs[unqualified_attrs[parents_unqualified_attr]]
                    all_attrs[parents_domain_attr] = tmpDomain

        return all_attrs

    def _get_iliname_dbname_mapping(self, sqlnames):
        return self._db_connector.get_iliname_dbname_mapping(sqlnames)

    def _get_models(self):
        return self._db_connector.get_models()

    def _get_classili_classdb_mapping(self, models_info, extended_classes):
        return self._db_connector.get_classili_classdb_mapping(models_info, extended_classes)

    def _get_attrili_attrdb_mapping(self, models_info_with_ext):
        return self._db_connector.get_attrili_attrdb_mapping(models_info_with_ext)

    def _get_attrili_attrdb_mapping_by_owner(self, owners):
        return self._db_connector.get_attrili_attrdb_mapping_by_owner(owners)
