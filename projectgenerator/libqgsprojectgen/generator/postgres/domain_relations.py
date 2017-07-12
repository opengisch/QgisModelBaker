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

class DomainRelation(Relation):
    pass

    @classmethod
    def find_domain_relations(cls, domains, conn, schema):

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        domain_names = "'" + "','".join(domains) + "'"
        cur.execute("""SELECT iliname, sqlname
                        FROM {schema}.t_ili2db_classname
                        WHERE sqlname IN ({domain_names})
                    """.format(schema=schema, domain_names=domain_names))

        relations = list()
        domains_ili_pg = dict()

        for record in cur:
            domains_ili_pg[record['iliname']] = record['sqlname']


        # Get MODELS
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        domain_names = "'" + "','".join(domains) + "'"
        cur.execute("""SELECT modelname, content
                       FROM {schema}.t_ili2db_model)
                    """.format(schema=schema, domain_names=domain_names))
        models = dict()
        models_info = dict()
        for record in cur:
            models[record['modelname'].split("{")[0]] = record['content']
        for k,v in models.items():
            models_info.update(self.parse_model(v, domains))


            #relation = Relation()
            #relation.referencing_layer = mapped_layers[record['referencing_table_name']]
            #relation.referenced_layer = mapped_layers[record['referenced_table_name']]
            #relation.referencing_field = record['referencing_column_name']
            #relation.referenced_field = record['referenced_column_name']
            #relation.name = record['constraint_name']

            #relations.append(relation)

        return relations


    def parse_model(self, model_content, domains):
        re_model = re.compile('\s*MODEL\s*([\w\d_-]+)\s.*') # MODEL Catastro_COL_ES_V_2_0_20170331 (es)
        re_topic = re.compile('\s*TOPIC\s*([\w\d_-]+)\s.*') # TOPIC Catastro_Registro [=]
        re_class = re.compile('\s*CLASS\s*([\w\d_-]+)\s.*') # CLASS ClassName [=]
        re_end_class = None  # END ClassName;
        re_end_topic = None # END TopicName;

        current_model = ''
        current_topic = ''
        current_class = ''
        attributes = dict()
        models_info = dict()
        for line in model_content:
            if not current_model:
                result = re_model.search(line)
                if result:
                    current_model = result.group(1)
            else: # The is a current_model
                if not current_topic:
                  result = re_topic.search(line)
                  if result:
                      current_topic = result.group(1)
                      re_end_topic = re.compile('\s*END\s*{}\s*;\s.*'.format(current_topic)) # END TopicName;
                      continue
                else: # There is a current_topic
                    if not current_class: # Go for classes
                        result = re_class.search(line)
                        if result:
                            current_class = result.group(1)
                            attributes = dict()
                            re_end_class = re.compile('\s*END\s*{}\s*;\s.*'.format(current_class))  # END ClassName;
                            continue
                    else: # There is a current_class, go for attributes
                        local_names = extract_local_names_from_domains(domains, current_model, current_topic)
                        domains_with_local = [name for name_list in local_names.values() for name in name_list] + domains
                        attribute = {res.group(1):d for d in domains_with_local for res in [re.search('\s*([\w\d_-]+).*:.*\s{}.*'.format(d),line)] if res}

                        if attribute:
                            attr_value = list(attribute.values())[0]
                            if attr_value not in domains: # Match was vs. local name, find its corresponding qualified name
                                for k,v in local_names.items():
                                    if attr_value in v:
                                        attribute[list(attribute.keys())[0]] = k
                                        break
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


