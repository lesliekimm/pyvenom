# package imports
from ..internal.hybrid_model import HybridModel
from ..internal.index_yaml import update_index_yaml
from attribute import ModelAttribute
from Properties import Property
from query import Query


__all__ = ['Model', 'Model']


class MetaModel(type):
  def __init__(cls, name, bases, classdict):
    super(MetaModel, cls).__init__(name, bases, classdict)
    cls._init_class()
    update_index_yaml([cls])


class PropertySchema(object):
  def __init__(self, property, datastore=False, search=False, indexed_datastore=False):
    self.property = property
    self.datastore = datastore
    self.search = search
    self.indexed_datastore = indexed_datastore
  
  def __eq__(self, value):
    return (
      self.property.__equals__(value.property) and
      self.search == value.search and
      self.datastore == value.datastore and
      self.indexed_datastore == value.indexed_datastore
    )
  
  def __repr__(self):
    return 'PropertySchema({}, datastore={}, search={}, indexed_datastore={})'.format(
      self.property,
      self.datastore,
      self.search,
      self.indexed_datastore
    )


class ModelSchema(dict):
  def __init__(self, model, properties, queries):
    schema = self._build_schema(properties, queries)
    self._model = model
    super(ModelSchema, self).__init__(schema)
  
  def __eq__(self, value):
    if set(self.keys()) != set(value.keys()):
      return False
    for key, prop_schema in self.items():
      value_prop_schema = value[key]
      if not prop_schema == value_prop_schema:
        return False
    return True
  
  def _build_schema(self, properties, queries):
    schema = {
      name: PropertySchema(prop, datastore=True)
      for name, prop in properties.items()
    }
    
    for _, query in queries.items():
      comparisons = query.get_property_comparisons()
      uses_datastore = query.uses_datastore()
      for comparison in comparisons:
        prop_name = comparison.property._name
        if uses_datastore:
          schema[prop_name].indexed_datastore = True
        else:
          schema[prop_name].search = True
    
    return schema
  
  def to_table(self):
    template = '{:>13} | {!s:>9} | {!s:>7} | {!s:>10}\n'
    doc = template.format('Property Name', 'Datastore', 'Indexed', 'Search API')
    doc += template.format('-------------', '---------', '-------', '----------')
    for name, property_schema in self.items():
      doc += template.format(
        name,
        property_schema.datastore,
        property_schema.indexed_datastore,
        property_schema.search
      )
    return doc[:-1]


class Model(object):
  __metaclass__ = MetaModel
  
  # attributes updates by metaclass
  kind = None
  hybrid_model = None
  
  @classmethod
  def _init_class(cls):
    from Properties import Property
    cls.kind = cls.__name__
    cls.hybrid_model = type(cls.kind, (HybridModel,), {})
    cls._properties = ModelAttribute.connect(cls, kind=Property)
    cls._queries = ModelAttribute.connect(cls, kind=Query)
    cls._schema = ModelSchema(cls, cls._properties, cls._queries)
  
  def __init__(self, **kwargs):
    super(Model, self).__init__()
    self.hybrid_entity = self.hybrid_model()
    self.key = None
    self._connect_properties()
    self._connect_queries()
    self.populate(**kwargs)
  
  def _connect_properties(self):
    for _, prop in self._properties.items():
      prop._connect(entity=self)
  
  def _connect_queries(self):
    for _, query in self._queries.items():
      query._connect(entity=self)
  
  @classmethod
  def _execute_datastore_query(cls, query):
    return cls._execute_query(cls.hybrid_model.query_by_datastore(query))
  
  @classmethod
  def _execute_search_query(cls, query):
    return cls._execute_query(cls.hybrid_model.query_by_search(query))
  
  @classmethod
  def _execute_query(cls, results):
    entities = map(cls._entity_to_model, results)
    return entities
  
  @classmethod
  def _entity_to_model(cls, hybrid_entity):
    ndb_entity = hybrid_entity.entity
    properties = {name: prop._get_value(ndb_entity) for name, prop in ndb_entity._properties.items()}
    entity = cls()
    entity._populate_from_stored(**properties)
    entity.hybrid_entity = hybrid_entity
    entity.key = entity.hybrid_entity.document_id
    return entity
  
  def populate(self, **kwargs):
    for key, value in kwargs.items():
      if key in self._properties:
        setattr(self, key, value)
  
  def _populate_from_stored(self, **kwargs):
    for key, value in kwargs.items():
      if key in self._properties:
        prop = self._properties[key]
        prop._set_stored_value(self, value)
  
  def _set_key(self, key):
    document_id = key.pairs()[0][1]
    self.key = document_id
    self.hybrid_entity.key = key
    self.hybrid_entity.document_id = document_id
  
  def __json__(self):
    json = {
      key: prop._get_value(self)
      for key, prop in self._properties.items()
    }
    json['key'] = self.key
    return json
  
  def save(self):
    for key, prop_schema in self._schema.items():
      prop = prop_schema.property
      value = prop._get_stored_value(self)
      if prop_schema.search and value != None:
        field = prop.to_search_field()
        self.hybrid_entity.set(key, value, field)
      property = prop.to_datastore_property()
      self.hybrid_entity.set(key, value, property)
    self.hybrid_entity.put()
    self.key = self.hybrid_entity.document_id
    return self
  
  @classmethod
  def get(cls, document_id):
    entity = cls.hybrid_model.get(document_id=document_id)
    return cls._entity_to_model(entity)
  
  @classmethod
  def get_multi(cls, document_ids):
    hybrid_entities = cls.hybrid_model.get_multi(document_ids=document_ids)
    entities = map(cls._entity_to_model, hybrid_entities)
    return entities
