# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 12/07/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo
        email                : gcarrillo@linuxmail.org
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
import psycopg2

from projectgenerator.libqgsprojectgen.dataobjects.relations import Relation

class DomainRelation(Relation):
    def __init__(self):
        pass

    def find_domain_relations(self, layers, conn, schema):
        domains = [layer.table_name for layer in layers if layer.is_domain]
        print("domains:",domains)
        if not domains:
            return []

        mapped_layers = {layer.table_name : layer for layer in layers}

        # Map domain ili name with its correspondent pg name
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        domain_names = "'" + "','".join(domains) + "'"
        cur.execute("""SELECT iliname, sqlname
                        FROM {schema}.t_ili2db_classname
                        WHERE sqlname IN ({domain_names})
                    """.format(schema=schema, domain_names=domain_names))
        domains_ili_pg = dict()
        for record in cur:
            domains_ili_pg[record['iliname']] = record['sqlname']
        print("domains_ili_pg:",domains_ili_pg)

        # Get MODELS
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""SELECT modelname, content
                       FROM {schema}.t_ili2db_model
                    """.format(schema=schema))
        models = dict()
        models_info = dict()
        for record in cur:
            models[record['modelname'].split("{")[0]] = record['content']
        # TODO To get info from base classes we might need to discover a dependency tree right here
        print("models:",models)
        for k,v in models.items():
            models_info.update(self.parse_model(v, domains))
        print("Classes with domain attrs:",len(models_info))

        # Map class ili name with its correspondent pg name
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        class_names = "'" + "','".join(list(models_info.keys())) + "'"
        cur.execute("""SELECT *
                       FROM {schema}.t_ili2db_classname
                       WHERE iliname IN ({class_names})
                    """.format(schema=schema, class_names=class_names))
        classes_ili_pg = dict()
        for record in cur:
            classes_ili_pg[record['iliname']] = record['sqlname']
        print("classes_ili_pg:",classes_ili_pg)

        # Map attr ili name with its correspondent pg name
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        all_attrs = list()
        for c, dict_attr_domain in models_info.items():
            all_attrs.extend(list[dict_attr_domain.keys()])
        attr_names = "'" + "','".join(all_attrs) + "'"
        cur.execute("""SELECT iliname, sqlname
                       FROM {schema}.t_ili2db_attrname
                       WHERE iliname IN ({attr_names})
                    """.format(schema=schema, attr_names=attr_names))
        attrs_ili_pg = dict()
        for record in cur:
            attrs_ili_pg[record['iliname']] = record['sqlname']
        print("attrs_ili_pg:",attrs_ili_pg)

        # Create relations
        relations = list()
        for iliclass, dict_attr_domain in models_info.items():
            for iliattr, ilidomain in dict_attr_domain:
                if iliclass in classes_ili_pg and ilidomain in domains_ili_pg and iliattr in attrs_ili_pg:
                    relation = Relation()
                    relation.referencing_layer = mapped_layers[classes_ili_pg[iliclass]]
                    relation.referenced_layer = mapped_layers[classes_ili_pg[ilidomain]]
                    relation.referencing_field = attrs_ili_pg[iliattr]
                    relation.referenced_field = 'itfcode'
                    #relation.name = record['constraint_name']

                    relations.append(relation)

        print("final_models_info:",models_info)
        print("Num of Relations:",len(relations))
        return relations

    def parse_model(self, model_content, domains):
        re_model = re.compile('\s*MODEL\s*([\w\d_-]+).*') # MODEL Catastro_COL_ES_V_2_0_20170331 (es)
        re_topic = re.compile('\s*TOPIC\s*([\w\d_-]+).*') # TOPIC Catastro_Registro [=]
        re_class = re.compile('\s*CLASS\s*([\w\d_-]+).*') # CLASS ClassName [=]
        re_end_class = None  # END ClassName;
        re_end_topic = None # END TopicName;
        re_end_model = None # END ModelName;

        current_model = ''
        current_topic = ''
        current_class = ''
        attributes = dict()
        models_info = dict()
        for line in model_content.splitlines():
            if not current_model:
                result = re_model.search(line)
                if result:
                    current_model = result.group(1)
                    re_end_model = re.compile('\s*END\s*{}\..*'.format(current_model)) # END TopicName; # FIX
            else: # The is a current_model
                if not current_topic:
                  result = re_topic.search(line)
                  if result:
                      current_topic = result.group(1)
                      re_end_topic = re.compile('\s*END\s*{}\s*;.*'.format(current_topic)) # END TopicName;

                      local_names = self.extract_local_names_from_domains(domains, current_model, current_topic)
                      domains_with_local = [name for name_list in local_names.values() for name in name_list] + domains

                      continue
                else: # There is a current_topic
                    if not current_class: # Go for classes
                        result = re_class.search(line)
                        if result:
                            current_class = result.group(1)
                            attributes = dict()
                            re_end_class = re.compile('\s*END\s*{}*;.*'.format(current_class))  # END ClassName;
                            continue
                    else: # There is a current_class, go for attributes
                        attribute = {res.group(1):d for d in domains_with_local for res in [re.search('\s*([\w\d_-]+).*:.*\s{};'.format(d),line)] if res}

                        if attribute:
                            old_key = list(attribute.keys())[0] # Not qualified name
                            new_key = "{}.{}.{}.{}".format(current_model, current_topic, current_class, old_key) # Fully qualified name
                            attr_value = list(attribute.values())[0]
                            if attr_value not in domains: # Match was vs. local name, find its corresponding qualified name
                                for k,v in local_names.items():
                                    if attr_value in v:
                                        attribute[old_key] = k
                                        break
                            attribute[new_key] = attribute.pop(old_key)
                            attributes.update(attribute)
                            continue

                        result = re_end_class.search(line)
                        if result:
                            if attributes:
                                models_info.update({'{}.{}.{}'.format(current_model,current_topic,current_class) : attributes})
                            current_class = ''
                            continue

                    result = re_end_topic.search(line)
                    if result:
                        current_topic = ''

                result = re_end_model.search(line)
                if result:
                    current_model = ''

        return models_info

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
            if domain.startswith('{}.'.format(current_model)) or domain.startswith('{}.{}.'.format(current_model, current_topic)):
                array = domain.split(".")
                if len(array) > 0:
                    local_names_list.append(array[-1])
                if len(array) > 1:
                    local_names_list.append('{}.{}'.format(array[-2], array[-1]))
                if local_names_list:
                    local_names[domain] = local_names_list
        return local_names


# TODO
# Not yet supported:
#   Classes that don't belong to a topic but directly to the model
#   Classes that extend other classes don't get base class attributes
