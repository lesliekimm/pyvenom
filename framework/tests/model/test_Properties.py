from helper import smart_assert, BasicTestCase
import venom


class BasePropertyTest(BasicTestCase):
  def test_invalid_comparison(self):
    prop = venom.Properties.Property()
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop == 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop < 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop <= 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop > 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop >= 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop != 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop.contains(1)
    
    class TestProp(venom.Properties.Property):
      allowed_operators = frozenset([
        venom.Properties.PropertyComparison.EQ,
        venom.Properties.PropertyComparison.NE
      ])
      
      def query_uses_datastore(self, operator, value):
        return operator == venom.Properties.PropertyComparison.EQ
      
      def to_search_field(self, operator, value):
        return 'search'
  
      def to_datastore_property(self, operator, value):
        return 'datastore'
    
    prop = TestProp()
    with smart_assert.raises() as context:
      prop == 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop < 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop <= 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop > 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop >= 1
    with smart_assert.raises() as context:
      prop != 1
    with smart_assert.raises(venom.Properties.InvalidPropertyComparison) as context:
      prop.contains(1)
  
  def test_comparisons_method(self):
    class TestProp(venom.Properties.Property):
      allowed_operators = venom.Properties.PropertyComparison.allowed_operators
      
      def query_uses_datastore(self, operator, value):
        return operator == venom.Properties.PropertyComparison.EQ
      
      def to_search_field(self, operator, value):
        return 'search'
  
      def to_datastore_property(self, operator, value):
        return 'datastore'
    
    prop = TestProp()
    with smart_assert.raises() as context:
      prop == 1
    
    assert prop.search == False
    assert prop.datastore == True
    assert prop.compared == True
    assert prop.search_fields == set()
    assert prop.datastore_properties == set(['datastore'])
    
    prop < 4
    
    assert prop.search == True
    assert prop.datastore == True
    assert prop.compared == True
    assert prop.search_fields == set(['search'])
    assert prop.datastore_properties == set(['datastore'])
  
  def test_base_validatation(self):
    class TestProp(venom.Properties.Property):
      pass
    
    prop = TestProp(required=True)
    with smart_assert.raises() as context:
      prop.validate(123)
    with smart_assert.raises(venom.Properties.PropertyValidationFailed) as context:
      prop.validate(None)
    
    prop = TestProp(required=False)
    with smart_assert.raises() as context:
      prop.validate(123)
      prop.validate(None)
  
  def test_set_value_vs_stored_value(self):
    class TestProp(venom.Properties.Property):
      def _set_stored_value(self, entity, value):
        super(TestProp, self)._set_stored_value(entity, value // 2)
  
      def _get_stored_value(self, entity):
        return super(TestProp, self)._get_stored_value(entity) * 2
    
    class ModelStub(object):
      pass
    entity = ModelStub()
    
    prop = TestProp()
    prop._connect(entity=entity)
    prop._set_value(entity, 123)
    assert prop._get_value(entity) == 123
    assert prop._get_stored_value(entity) == 246
    prop._set_stored_value(entity, 468)
    assert prop._get_value(entity) == 234
    assert prop._get_stored_value(entity) == 468
