from helper import smart_assert, BasicTestCase
import venom

from google.appengine.ext import ndb


class ModelTest(BasicTestCase):
  def test_modelattribute_fixup(self):
    """
    ' Tests that a venom.Model subclass correctly assigns
    ' references on all ModelAttribute instances on that subclass
    ' to the parent model.
    '
    ' EXAMPLE
    '
    ' class Test(venom.Model):
    '   foo = venom.Properties.Property()
    '   bar = venom.Properties.Property()
    ' 
    ' This should set _name, _model, _entity on 'bar' and 'foo'
    ' (_entity only when instantiated)
    """
    
    class Test(venom.Model):
      foo = venom.Properties.Property()
      bar = venom.Properties.Property()
    
    smart_assert('foo', Test.foo._name).equals('[fail] prop._name == prop_name')
    smart_assert('bar', Test.bar._name).equals('[fail] prop._name == prop_name')
    smart_assert(Test, Test.foo._model).equals('[fail] prop._model == parent_model')
    smart_assert(Test, Test.bar._model).equals('[fail] prop._model == parent_model')
    
    test = Test()
    
    smart_assert(test, Test.foo._entity).equals('[fail] prop._entity == parent_entity')
    smart_assert(test, Test.bar._entity).equals('[fail] prop._entity == parent_entity')
  
  def test_property_setter_getter(self):
    class Test(venom.Model):
      foo = venom.Properties.Property()
      bar = venom.Properties.Property()
    
    test = Test()
    test.foo = 123
    assert test.foo == 123
    test.bar = 456
    test.foo = 789
    assert test.bar == 456
    assert test.foo == 789
  
  def test_populate_vs_from_stored(self):
    class TestProp(venom.Properties.Property):
      def _set_stored_value(self, entity, value):
        super(TestProp, self)._set_stored_value(entity, value // 2)
  
      def _get_stored_value(self, entity):
        return super(TestProp, self)._get_stored_value(entity) * 2
    
    class Test(venom.Model):
      foo = TestProp()
      bar = TestProp()
    
    test = Test(foo=123, bar=456)
    assert test.foo == 123
    assert test.bar == 456
    
    test = Test()
    test.populate(foo=123, bar=456)
    assert test.foo == 123
    assert test.bar == 456
    
    test = Test()
    test._populate_from_stored(foo=10, bar=26)
    assert test.foo == 5
    assert test.bar == 13
  
  def test_saving_data(self):
    class TestProp(venom.Properties.Property):
      allowed_operators = venom.Properties.PropertyComparison.allowed_operators
      
      def _to_storage(self, value):
        return value * 2
  
      def _from_storage(self, value):
        return value // 2
      
      def to_datastore_property(self):
        return ndb.IntegerProperty
      
      def query_uses_datastore(self, operator, value):
        return True
    
    class Test(venom.Model):
      foo = TestProp()
      bar = TestProp()
      
      foo10 = venom.Query(foo == 10)
      foo34 = venom.Query(foo == 34)
    
    test = Test()
    test.foo = 10
    test.bar = 24
    test.put()
    
    entities = test.hybrid_model.query_by_datastore()
    assert len(entities) == 1
    
    entity = entities[0]
    assert entity.foo == 20
    assert entity.bar == 48
    
    entities = Test.foo10()
    assert len(entities) == 1
    
    entity = entities[0]
    assert entity.foo == 10
    assert entity.bar == 24
    
    entity.foo = 34
    entity.put()
    
    entities = Test.foo10()
    assert len(entities) == 0
    
    entities = Test.foo34()
    assert len(entities) == 1
    
    entity = entities[0]
    assert entity.foo == 34
    assert entity.bar == 24

  def test_schema(self):
    # TODO test schema
    raise Exception('TODO')