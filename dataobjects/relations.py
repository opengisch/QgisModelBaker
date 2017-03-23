from qgis.core import QgsRelation


class Relation(object):
    def __init__(self):
        self.referencing_layer = None
        self.referenced_layer = None
        self.referencing_field = None
        self.referenced_field = None
        self.name = None

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

    def create(self, layers):
        print('Creating relation')
        relation = QgsRelation()
        if not self.name:
            self.name = "{}_{}".format(self.referencing_layer, self.referencing_field)
        relation.setId(self.name)
        relation.setName(self.name)

        found = 0
        for layer in layers:
            if layer.inner_id == self.referencing_layer:
                relation.setReferencingLayer(layer.id())
                found += 1
            if layer.inner_id == self.referenced_layer:
                relation.setReferencedLayer(layer.id())
                found += 1
            if found == 2:
                break

        relation.addFieldPair( self.referencing_field, self.referenced_field)
        return relation
