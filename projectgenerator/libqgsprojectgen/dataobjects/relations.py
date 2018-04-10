from qgis.core import QgsRelation


class Relation(object):

    def __init__(self):
        self.referencing_layer = None
        self.referenced_layer = None
        self.referencing_field = None
        self.referenced_field = None
        self.name = None
        self.qgis_relation = None
        self._id = None

    def dump(self):
        definition = dict()
        definition['referencingLayer'] = self.referencing_layer
        definition['referencingField'] = self.referencing_field
        definition['referencedLayer'] = self.referenced_layer
        definition['referencedField'] = self.referenced_field

        return definition

    def load(self, definition):
        self.referencing_layer = definition['referencingLayer']
        self.referencing_field = definition['referencingField']
        self.referenced_layer = definition['referencedLayer']
        self.referenced_field = definition['referencedField']

    def create(self, qgis_project):
        relation = QgsRelation()
        project_ids = qgis_project.relationManager().relations().keys()
        base_id = self.name
        suffix = 0
        self._id = base_id
        while self._id in project_ids:
            self._id = '{}{}'.format(base_id, suffix)
        relation.setId(self._id)
        relation.setName(self.name)
        relation.setReferencingLayer(self.referencing_layer.create().id())
        relation.setReferencedLayer(self.referenced_layer.create().id())
        relation.addFieldPair(self.referencing_field, self.referenced_field)
        self.qgis_relation = relation
        return relation

    @property
    def id(self):
        return self._id
