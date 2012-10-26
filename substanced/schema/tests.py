import unittest
from pyramid import testing
import colander

class TestSchema(unittest.TestCase):
    def _getTargetClass(self):
        from . import Schema
        return Schema

    def _makeOne(self):
        return self._getTargetClass()()

    def test_validate_failure(self):
        from colander import Invalid
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertRaises(Invalid, inst2.deserialize, {'_csrf_token_':'wrong'})

    def test_validate_missing(self):
        from colander import Invalid
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertRaises(Invalid, inst2.deserialize, {})

    def test_validate_success(self):
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertEqual(inst2.deserialize({'_csrf_token_':'csrf_token'}),{})

class TestRemoveCSRFMapping(unittest.TestCase):
    def _makeOne(self):
        from . import RemoveCSRFMapping
        return RemoveCSRFMapping()

    def test_deserialize_colander_null(self):
        inst = self._makeOne()
        node = object()
        result = inst.deserialize(node, colander.null)
        self.assertEqual(result, colander.null)

    def test_deserialize_real_mapping(self):
        inst = self._makeOne()
        node = colander.SchemaNode(colander.Mapping())
        a = colander.SchemaNode(colander.String(), name='a')
        node.add(a)
        result = inst.deserialize(node, {'_csrf_token_':'token', 'a':'1'})
        self.assertEqual(result, {'a':'1'})

class TestNameSchemaNode(unittest.TestCase):
    def _makeOne(self, **kw):
        from . import NameSchemaNode
        return NameSchemaNode(**kw)

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _makeBindings(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        return dict(request=request, context=context)

    def test_it_invalid_len(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value): pass
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        node.max_len = 1
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_invalid_check_name(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value):
            self.assertEqual(value, 'abc')
            raise ValueError('abc')
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_valid(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value): pass
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)

    def test_it_editing_True_invalid(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value):
            raise ValueError('foo')
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        node = self._makeOne(editing=True)
        node.bindings = bindings
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_editing_True_valid(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value): pass
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        node = self._makeOne(editing=True)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)

    def test_it_editing_is_callable(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value): pass
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        def editing(context, request):
            self.assertEqual(context, bindings['context'])
            self.assertEqual(request, bindings['request'])
            return True
        node = self._makeOne(editing=editing)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)


class DummySession(dict):
    def get_csrf_token(self):
        return 'csrf_token'

class DummyRequest(testing.DummyRequest):
    def __init__(self, *arg, **kw):
        testing.DummyRequest.__init__(self, *arg, **kw)
        self.session = DummySession()
    

class DummyContent(object):
    def __init__(self, result):
        self.result = result
