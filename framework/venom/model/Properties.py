# application imports
from query import PropertyQuery

# app engine imports
from google.appengine.api import search
from google.appengine.ext import ndb


__all__ = ['Property', 'String', 'Integer']
__all__ += ['QueryNotSupported', 'InvalidModelPropertyConnection', 'PropertyEnforcementFailed', 'InvalidPropertyInitialization']


class QueryNotSupported(Exception):
  pass

class InvalidModelPropertyConnection(Exception):
  pass

class PropertyEnforcementFailed(Exception):
  pass

class InvalidPropertyInitialization(Exception):
  pass


class Property(object):
  allowed_operators = frozenset()
  
  def __init__(self, required=False, default=None, choices=None):
    if required and default != None:
      raise InvalidPropertyInitialization('Property have a default value if required')
    
    self.required = required
    self.default = default
    self.choices = choices
    
    self._name = None
    
    self.is_queried = False
    self.search = False
    
  def _fix_up(self, name, instance):
    self._name = name
  
  def to_ndb_property(self):
    raise NotImplementedError()
  
  def to_search_field(self):
    raise NotImplementedError()
  
  def enforce(self, value):
    # required and default
    if not value:
      if self.required:
        raise PropertyEnforcementFailed('Value missing when required')
    
    # choices
    if self.choices != None:
      if value not in self.choices:
        raise PropertyEnforcementFailed('Value not in required choices')

  def __get__(self, instance, cls):
    if instance == None:
      # called on a class
      return self
    if not self._name in instance._values:
      return self.default
    return instance._values[self._name]

  def __set__(self, instance, value):
    self.enforce(value)
    instance._values[self._name] = value

  def __delete__(self,instance):
    raise AttributeError('Can\'t delete attribute')

  def __eq__(self, value):
    if not PropertyQuery.EQ in self.allowed_operators:
      raise QueryNotSupported('Property does not support == queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.EQ, value)
  
  def __ne__(self, value):
    if not PropertyQuery.NE in self.allowed_operators:
      raise QueryNotSupported('Property does not support != queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.NE, value)
  
  def __lt__(self, value):
    if not PropertyQuery.LT in self.allowed_operators:
      raise QueryNotSupported('Property does not support < queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.LT, value)
  
  def __le__(self, value):
    if not PropertyQuery.LE in self.allowed_operators:
      raise QueryNotSupported('Property does not support <= queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.LE, value)
  
  def __gt__(self, value):
    if not PropertyQuery.GT in self.allowed_operators:
      raise QueryNotSupported('Property does not support > queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.GT, value)
  
  def __ge__(self, value):
    if not PropertyQuery.GE in self.allowed_operators:
      raise QueryNotSupported('Property does not support >= queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.GE, value)
  
  def contains(self, value):
    if not PropertyQuery.IN in self.allowed_operators:
      raise QueryNotSupported('Property does not support IN queries')
    self.is_queried = True
    self._on_query()
    return PropertyQuery(self, PropertyQuery.IN, value)
  
  def _on_query(self):
    pass
  
  def __repr__(self):
    classname = self.__class__.__name__
    return '{}(value={}, default={}, required={}, choices={})'.format(classname, self._value, self.default, self.required, self.choices)
  

class String(Property):
  allowed_operators = frozenset((
    PropertyQuery.EQ,
    PropertyQuery.NE,
    PropertyQuery.IN
  ))
  
  def __init__(self, required=False, default=None, min=None, max=500, characters=None, choices=None):
    self.max = max
    self.min = min
    self.characters = characters
    super(String, self).__init__(required=required, default=default, choices=choices)
  
  def _on_query(self):
    if self.max == None or self.max > 500:
      self.search = True
  
  def to_ndb_property(self):
    indexed = self.is_queried and not self.search
    return ndb.StringProperty(indexed=indexed, name=self._name)
  
  def to_search_field(self):
    return search.TextField
  
  def enforce(self, value):
    super(String, self).enforce(value)
    if value == None: return value
    
    # type str
    if not isinstance(value, str) and not isinstance(value, unicode):
      raise PropertyEnforcementFailed('StringProperty must be of type str')

    # min
    if self.min != None and len(value) < self.min:
      raise PropertyEnforcementFailed('StringProperty value less than minimum character length')

    # max
    if self.max != None and len(value) > self.max:
      raise PropertyEnforcementFailed('StringProperty value greater than maximum character length')

    # characters
    if self.characters != None and len(set(value) - set(self.characters)) > 0:
      raise PropertyEnforcementFailed('StringProperty value contains characters not permitted from "{}"'.format(self.characters))


class Integer(Property):
  allowed_operators = frozenset((
    PropertyQuery.EQ,
    PropertyQuery.LT,
    PropertyQuery.LE,
    PropertyQuery.GT,
    PropertyQuery.GE,
    PropertyQuery.NE
  ))
  
  def __init__(self, required=False, default=None, min=None, max=None, choices=None):
    self.min = min
    self.max = max
    super(Integer, self).__init__(required=required, default=default, choices=choices)
  
  def to_ndb_property(self):
    indexed = self.is_queried and not self.search
    return ndb.IntegerProperty(indexed=indexed, name=self._name)
  
  def to_search_field(self):
    return search.NumberField
  
  def __get__(self, instance, cls):
    if instance == None:
      # called on a class
      return self
    if not self._name in instance._values:
      return int(self.default)
    return int(instance._values[self._name])
  
  def __set__(self, instance, value):
    self.enforce(value)
    instance._values[self._name] = int(value)
  
  def enforce(self, value):
    super(Integer, self).enforce(value)
    if value == None: return value
    
    # type str
    if not isinstance(value, int) and not isinstance(value, long):
      raise PropertyEnforcementFailed('Integer must be of type int or long')

    # min
    if self.min != None and len(value) < self.min:
      raise PropertyEnforcementFailed('Integer value less than minimum character length')

    # max
    if self.max != None and len(value) > self.max:
      raise PropertyEnforcementFailed('Integer value greater than maximum character length')
