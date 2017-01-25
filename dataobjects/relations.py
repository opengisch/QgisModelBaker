from qgis.core import QgsRelation


class Relation(object):
    def __init__(self):
        self.referencing_layer = None
        self.referenced_layer = None
        self.referencing_field = None
        self.referenced_field = None

    def dump(self):
        definition = dict()
        definition['referencingLayer'] = self.referencing_layer.id()
        definition['referencingField'] = self.referencing_field
        definition['referencedLayer'] = self.referenced_layer.id()
        definition['referencedField'] = self.referenced_field

        return definition

    def load(self, definition):
        self.referencing_layer = definition['referencingLayer']
        self.referencing_field = definition['referencingField']
        self.referenced_layer = definition['referencedLayer']
        self.referenced_field = definition['referencedField']

    def create(self):
        relation = QgsRelation()
        relation.setReferencingLayer()
        relation.setReferencedLayer()
        relation.addFieldPair( self.referencing_field, self.referenced_field)
        return relation
