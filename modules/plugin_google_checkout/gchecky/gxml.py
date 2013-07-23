"""
Gchecky.gxml module provides an abstraction layer when dealing with Google
Checkout API services (GC API). It translates XML messages into human-friendly python
structures and vice versa.

In practice it means that when you have recieved
a notification message from GC API, and you want to understand what's in that
XML message, you simply pass it to gchecky and it parses (and automatically
validates it for you) the XML text into python objects - instances of the class
corresponding to the message type. Then that object is passed to your hook
method along with extracted google order_id.

For example when an <order-state-change /> XML message is send to you by GC API
gchecky will call on_order_state_change passing it an instance of
C{gchecky.gxml.order_state_change_t} along with google order_id.

This is very convenient since you don't have to manipulate xml text, or xml DOM
tree, neither do you have to validate the recieved message - it is already done
by gchecky.

See L{gchecky.controller} module for information on how to provide hooks
to the controller or customize it. 

@cvar GOOGLE_CHECKOUT_API_XML_SCHEMA: the google checkout API messages xml
    schema location (more correctly it is the XML namesoace identificator for
    elements of the XML messages for google checkout API services).

@author: etarassov
@version: $Revision: 126 $
@contact: gchecky at gmail
"""

GOOGLE_CHECKOUT_API_XML_SCHEMA = 'http://checkout.google.com/schema/2'

from tools import encoder, decoder
from datetime import datetime

class Field(object):
    """Holds all the meta-information about mapping the current field value into/from
    the xml DOM tree.
    
    An instance of the class specifies the exact path to the DOM
    node/subnode/attribute that contains the field value. It also holds other
    field traits such as:
      @ivar required: required or optional
      @ivar empty: weither the field value could be empty (an empty XML tag)
      @ivar values: the list of acceptable values
      @ivar default: the default value for the field
      @ivar path: the path to the xml DOM node/attribute to store the field data
      @ivar save_node_and_xml: a boolean that specifies if the original xml
                  and DOM element should be saved. Handly for fields that could
                  contain arbitrary data such as 'merchant-private-data' and
                  'merchant-private-item-data'.
                  The original xml text is saved into <field>_xml.
                  The corresponding DOM node is stored into <field>_dom.
    """
    path     = ''
    required = True
    empty    = False
    default  = None
    values   = None
    save_node_and_xml = False

    @classmethod
    def deconstruct_path(cls, path):
        """Deconstruct a path string into pieces suitable for xml DOM processing.
            @param path: a string in the form of /chunk1/chunk2/.../chunk_n/@attribute.
                It denotes a DOM node or an attibute which holds this fields value.
                This corresponds to an hierarchy of type::
                  chunk1
                   \- chunk2
                      ...
                       \- chunk_n
                           \- @attribute
                Where chunk_n are DOM nodes and @attribute is a DOM attribute.
        
                Chunks and @attribute are optional.
                
                An empty string denotes the current DOM node.
            @return: C{(chunks, attribute)} - a list of chunks and attribute
            value (or None).
            @see: L{reconstruct_path}"""
        chunks = [chunk for chunk in path.split('/') if len(chunk)]
        attribute = None
        if chunks and chunks[-1][:1] == '@':
            attribute = chunks.pop()[1:]
        import re
        xml_name = re.compile(r'^[a-zA-Z\_][a-zA-Z0-9\-\_]*$') # to be fixed
        assert attribute is None or xml_name.match(attribute)
        assert 0 == len([True for chunk in chunks
                         if xml_name.match(chunk) is None])
        return chunks, attribute

    @classmethod
    def reconstruct_path(cls, chunks, attribute):
        """Reconstruct the path back into the original form using the deconstructed form.
           A class method.

            @param chunks: a list of DOM sub-nodes.
            @param attribute: a DOM attribute.
            @return: a string path denoting the DOM node/attribute which should contain
                the field value.
            @see: L{deconstruct_path}"""
        return '%s%s%s' % ('/'.join(chunks),
                           attribute and '@' or '',
                           attribute or '')

    def __init__(self, path, **kwargs):
        """Specify initial parameters for this field instance. The list of
        actual parameters depends on the subclass.
        @param path: The path determines the DOM node/attribute to be used
        to store/retrieve the field data value. It will be directly passed to
        L{deconstruct_path}."""
        for pname, pvalue in kwargs.items():
            setattr(self, pname, pvalue)
        if path is None:
            raise Exception('Path is a required parameter')
        self.path = path
        self.path_nodes, self.path_attribute = Field.deconstruct_path(path)

    def get_initial_value(self):
        if self.required:
            if self.default is not None:
                return self.default
            elif self.values and len(self.values) > 0:
                return self.values[0]
        return None

    def save(self, node, data):
        """Save the field data value into the DOM node. The value is stored
        accordingly to the field path which could be the DOM node itself or
        its subnodes (which will be automatically created), or (a sub)node
        attribute.
        @param node: The DOM node which (or subnodes of which) will contain
            the field data value.
        @param data: The data value for the field to be stored.
        """
        str = self.data2str(data)
        if self.path_attribute is not None:
            node.setAttribute(self.path_attribute, str)
        else:
            if str is not None:
                node.appendChild(node.ownerDocument.createTextNode(str))

    def load(self, node):
        """Load the field data from the xml DOM node. The value is retrieved
        accordingly to the field path and  other traits.
          @param node: The xml NODE that (or subnodes or attribute of which)
          contains the field data value.
          @see L{save}, L{__init__}"""
        if self.path_attribute is not None:
            if not node.hasAttribute(self.path_attribute):
                return None
            str = node.getAttribute(self.path_attribute)
        else:
            if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
                str = node.data
            else:
                str = ''.join([el.data for el in node.childNodes
                               if (el.nodeType == node.TEXT_NODE
                                   or el.nodeType == node.CDATA_SECTION_NODE)])
        return self.str2data(str)

    def validate(self, data):
        """
        Validate data according to this fields parameters.

        @return True if data is ok, otherwise return a string (!) describing
                why the data is invalid.

        Note that this method returns either True or an error string, not False!

        The Field class considers any data as valid and returns True.
        """
        return True

    def data2str(self, data):
        """Override this method in subclasses"""
        raise Exception('Abstract method of %s' % self.__class__)

    def str2data(self, str):
        """Override this method in subclasses"""
        raise Exception('Abstract method of %s' % self.__class__)

    def create_node_for_path(self, parent, reuse_nodes=True):
        """Create (if needed) a XML DOM node that will hold this field data.
        @param parent: The parent node that should hold this fields data.
        @param reuse_nodes: Reuse the existing required node if it is already present.
        @return: Return the XML DOM node to hold this field's data. The node
          created as a subnode (or an attribute, or a grand-node, etc.) of
          parent.
        """
        for nname in self.path_nodes:
            # Should we reuse an existing node?
            if reuse_nodes:
                nodes = parent.getElementsByTagName(nname)
                if nodes.length == 1:
                    parent = nodes[0]
                    continue
            node = parent.ownerDocument.createElement(nname)
            parent.appendChild(node)
            parent = node
        return parent

    def get_nodes_for_path(self, parent):
        """Retrieve all the nodes that hold data supposed to be assigned to this
        field. If this field path matches a subnode (or a 'grand' subnode, or
        an atribute, etc) of the 'parent' node, then it is included in
        the returned list.
        @param parent: The node to scan for this field data occurences.
        @return: The list of nodes that corresponds to this field."""
        elements = [parent]
        for nname in self.path_nodes:
            els = []
            for el in elements:
                children = el.childNodes
                for i in range(0, children.length):
                    item = children.item(i)
                    if item.nodeType == item.ELEMENT_NODE:
                        if item.tagName == nname:
                            els.append(item)
            elements = els
        return elements

    def get_one_node_for_path(self, parent):
        """Same as 'get_nodes_path' but checks that there is exactly one result
        and returns it."""
        els = self.get_nodes_for_path(parent)
        if len(els) != 1:
            raise Exception('Multiple nodes where exactly one is expected %s' % (self.path_nodes,))
        return els[0]

    def get_any_node_for_path(self, parent):
        """Same as 'get_nodes_path' but checks that there is no more than one
        result and returns it, or None if the list is empty."""
        els = self.get_nodes_for_path(parent)
        if len(els) > 1:
            raise Exception('Multiple nodes where at most one is expected %s' % (self.path_nodes,))
        if len(els) == 0:
            return None
        return els[0]

    def _traits(self):
        """Return the string representing the field traits.
        @see: L{__repr__}"""
        str = ':PATH(%s)' % (Field.reconstruct_path(self.path_nodes,
                                                    self.path_attribute),)
        str += ':%s' % (self.required and 'REQ' or 'OPT',)
        if self.empty:
            str += ':EMPTY'
        if self.default:
            str += ':DEF(%s)' % (self.default,)
        if self.values:
            str += ':VALS("%s")' % ('","'.join(self.values),)
        return str

    def __repr__(self):
        """Used in documentation. This method is called from subclasses
        __repr__ method to generate a human-readable description of the current
        field instance.
        """
        return '%s%s' % (self.__class__.__name__,
                         self._traits())

class NodeManager(type):
    """The class keeps track of all the subclasses of C{Node} class.
    
    It retrieves a C{Node} fields and provides this information to the class.
    
    This class represents a hook on-Node-subclass-creation where 'creation'
    means the moment the class is first loaded. It allows dynamically do some
    stuff on class load. It could also be done statically but that way we avoid
    code and effort duplication, which is quite nice. :-)
    
    @cvar nodes: The dictionary C{class_name S{rarr} class} keeps all the Node
    subclasses.
    """
    nodes = {}
    def __new__(cls, name, bases, attrs):
        """Dynamically do some stuff on a Node subclass 'creation'.
        
        Specifically do the following:
          - create the class (via the standard type.__new__)
          - retrieve all the fields of the class (its own and inherited)
          - store the class reference in the L{nodes} dictionary
          - give the class itself the access to its field list
        """
        clazz = type.__new__(cls, name, bases, attrs)
        NodeManager.nodes[name] = clazz
        fields = {}
        for base in bases:
            if hasattr(base, 'fields'):
                fields.update(base.fields())
        for fname, field in attrs.items():
            if isinstance(field, Field):
                fields[fname] = field
        clazz.set_fields(fields)
        return clazz

class Node(object):
    """The base class for any class which represents data that could be mapped
    into XML DOM structure.
    
    This class provides some basic functionality and lets programmer avoid
    repetetive tasks by automating it.
    
    @cvar _fields: list of meta-Fields of this class.
    @see: NodeManager
    """
    __metaclass__ = NodeManager
    _fields = {}
    @classmethod
    def set_fields(cls, fields):
        """Method is called by L{NodeManager} to specify this class L{Field}s
        set."""
        cls._fields = fields

    @classmethod
    def fields(cls):
        """Return all fields of this class (and its bases)"""
        return cls._fields

    def __new__(cls, **kwargs):
        """Creates a new instance of the class and initializes fields to
        suitable values. Note that for every meta-C{Field} found in the class
        itself, the instance will have a field initialized to the default value
        specified in the meta-L{Field}, or one of the L{Field} allowed values,
        or C{None}."""
        instance = object.__new__(cls)
        for fname, field in cls.fields().items():
            setattr(instance, fname, field.get_initial_value())
        return instance

    def __init__(self, **kwargs):
        """Directly initialize the instance with
        values::
          price = price_t(value = 10, currency = 'USD')
        is equivalent to (and preferred over)::
          price = price_t()
          price.value = 10
          price.currency = 'USD'
        """
        for name, value in kwargs.items():
            setattr(self, name, value)

    def write(self, node):
        """Store the L{Node} into an xml DOM node."""
        for fname, field in self.fields().items():
            data = getattr(self, fname, None)
            if data is None:
                if field.required: raise Exception('Field <%s> is required, but data for it is None' % (fname,))
                continue
            if (data != '' or not field.empty) and field.validate(data) != True:
                raise Exception("Invalid data for <%s>: '%s'. Reason: %s" % (fname, data, field.validate(data))) 
            field.save(field.create_node_for_path(node), data)

    def read(self, node):
        """Load a L{Node} from an xml DOM node."""
        for fname, field in self.fields().items():
            try:
                fnode = field.get_any_node_for_path(node)

                if fnode is None:
                    data = None
                else:
                    data = field.load(fnode)

                if field.save_node_and_xml:
                    # Store the original DOM node
                    setattr(self, '%s_dom' % (fname,), fnode)
                    # Store the original XML text
                    xml_fragment = ''
                    if fnode is not None:
                        xml_fragment = fnode.toxml()
                    setattr(self, '%s_xml' % (fname,), xml_fragment)

                if data is None:
                    if field.required:
                        raise Exception('Field <%s> is required, but data for it is None' % (fname,))
                elif data == '':
                    if field.required and not field.empty:
                        raise Exception('Field <%s> can not be empty, but data for it is ""' % (fname,))
                else:
                    if field.validate(data) != True:
                        raise Exception("Invalid data for <%s>: '%s'. Reason: %s" % (fname, data, field.validate(data)))
                setattr(self, fname, data)
            except Exception, exc:
                raise Exception('%s\n%s' % ('While reading %s' % (fname,), exc))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False

        for field in self.fields():
            if not(hasattr(self, field) == hasattr(other, field)):
                return False
            if hasattr(self, field) and not(getattr(self, field) == getattr(other, field)):
                return False
        return True
    def __neq__(self, other):
        return not(self == other)

class DocumentManager(NodeManager):
    """Keeps track of all the L{Document} subclasses. Similar to L{NodeManager}
    automates tasks needed to be donefor every L{Document} subclass.

    The main purpose is to keep the list of all the classes and theirs
    correspongin xml tag names so that when an XML message is recieved it could
    be possible automatically determine the right L{Document} subclass
    the message corresponds to (and parse the message using the found
    document-class).

    @cvar documents: The dictionary of all the documents."""
    documents = {}

    def __new__(cls, name, bases, attrs):
        """Do some stuff for every created Document subclass.""" 
        clazz = NodeManager.__new__(cls, name, bases, attrs)
        DocumentManager.register_class(clazz, clazz.tag_name)
        return clazz

    @classmethod
    def register_class(self, clazz, tag_name):
        """Register the L{Document} subclass."""
        if tag_name is None:
            raise Exception('Document %s has to have tag_name attribute' % (clazz,))
        self.documents[tag_name] = clazz

    @classmethod
    def get_class(self, tag_name):
        """@return: the class by its xml tag name or raises an exception if
        no class was found for the tag name."""
        if not DocumentManager.documents.has_key(tag_name):
            raise Exception('There are no Document with tag_name(%s)' % (tag_name,))
        return self.documents[tag_name]

class Document(Node):
    """A L{Node} which could be stored as a standalone xml document.
    Every L{Document} subclass has its own xml tag_name so that it could be
    automatically stored into/loaded from an XML document.

    @ivar tag_name: The document's unique xml tag name."""
    __metaclass__ = DocumentManager
    tag_name = 'unknown'

    def toxml(self, pretty=False):
        """@return: A string for the XML document representing the Document
        instance."""
        from xml.dom.minidom import getDOMImplementation
        dom_impl = getDOMImplementation()

        tag_name = self.__class__.tag_name
        doc      = dom_impl.createDocument(GOOGLE_CHECKOUT_API_XML_SCHEMA,
                                           tag_name,
                                           None)

        # TODO Fix this namespace problem that xml.dom.minidom has -- it does
        #      render the default namespace declaration for the newly created
        #      (not parsed) document. As a workaround we parse a dummy text
        #      with the wanted NS declaration and then fill it up with data.
        from xml.dom.minidom import parseString
        dummy_xml = '<?xml version="1.0"?><%s xmlns="%s"/>' % (tag_name,
                                                               GOOGLE_CHECKOUT_API_XML_SCHEMA)
        doc = parseString(dummy_xml)

        self.write(doc.documentElement)

        if pretty:
            return doc.toprettyxml((pretty is True and '  ') or pretty)
        return doc.toxml()

    def __str__(self):
        try:
            return self.toxml()
        except Exception:
            pass
        return self.__repr__()

    @classmethod
    def fromxml(self, text):
        """Read the text (as an XML document) into a Document (or subclass)
        instance.
        @return: A fresh-new instance of a Document (of the right subclas
        determined by the xml document tag name)."""
        from xml.dom.minidom import parseString
        doc = parseString(text)
        root = doc.documentElement
        clazz = DocumentManager.get_class(root.tagName)
        instance = clazz()
        instance.read(root)
        return instance

class List(Field):
    """The field describes a homogene list of values which could be stored
    as a set of XML nodes with the same tag names.
    
    An example - list of strings which should be stored as
    <messages> <message />* </messages>?::
      class ...:
          ...
          messages = gxml.List('/messages', gxml.String('/message'), required=False)

    @cvar list_item: a L{Field} instance describing this list items."""
    list_item = None

    # TODO required => default=[]
    def __init__(self, path, list_item, empty_is_none=True, **kwargs):
        """Initializes the List instance.
        @param path: L{Field.path}
        @param list_item: a meta-L{Field} instance describing the list items
        @param empty_is_none: If True then when loading data an empty list []
                              would be treated as None value. True by default.
        """ 
        Field.__init__(self, path, **kwargs)
        if self.path_attribute is not None:
            raise Exception('List type %s cannot be written into an attribute %s' % (self.__class__, self.path_attribute))
        if list_item is None or not isinstance(list_item, Field):
            raise Exception('List item (%s) has to be a Field instance' % (list_item,))
        self.list_item = list_item
        self.empty_is_none = empty_is_none

    def validate(self, data):
        """Checks that the data is a valid sequence."""
        from operator import isSequenceType
        if not isSequenceType(data):
            return "List data has to be a sequence."
        return True

    def save(self, node, data):
        """Store the data list in a DOM node.
        @param node: the xml DOM node to hold the list
        @param data: a list of items to be stored"""
        # node = self.list_item.create_node_for_path(node)
        for item_data in data:
            if item_data is None:
                if self.list_item.required: raise Exception('Required data is None')
                continue
            item_validity = self.list_item.validate(item_data)
            if item_validity != True:
                raise Exception("List contains an invalid value '%s': %s" % (item_data,
                                                                             item_validity))
            # reuse_nodes=False ensure that list items generate different nodes.
            inode = self.list_item.create_node_for_path(node, reuse_nodes=False)
            self.list_item.save(inode, item_data)

    def load(self, node):
        """Load the list from the xml DOM node.
        @param node: the xml DOM node containing the list.
        @return: a list of items."""
        data = []
        for inode in self.list_item.get_nodes_for_path(node):
            if inode is None:
                if self.list_item.required: raise Exception('Required data is None')
                data.append(None)
            else:
                idata = self.list_item.load(inode)
                item_validity = self.list_item.validate(idata)
                if item_validity != True:
                    raise Exception("List item can not have value '%s': %s" % (idata,
                                                                               item_validity)) 
                data.append(idata)
        if data == [] and (self.empty_is_none and not self.required):
            return None
        return data

    def __repr__(self):
        """Override L{Field.__repr__} for documentation purposes"""
        return 'List%s:[\n    %s\n]' % (self._traits(),
                                        self.list_item.__repr__())

class Complex(Field):
    """Represents a field which is not a simple POD but a complex data
    structure.
    An example - a price in USD::
        price = gxml.Complex('/unit-price', gxml.price_t)
    @cvar clazz: The class meta-L{Field} instance describing this field data.
    """
    clazz = None

    def __init__(self, path, clazz, **kwargs):
        """Initialize the Complex instance.
        @param path: L{Field.path}
        @param clazz: a Node subclass descibing the field data values."""
        if not issubclass(clazz, Node):
            raise Exception('Complex type %s has to inherit from Node' % (clazz,)) 
        Field.__init__(self, path, clazz=clazz, **kwargs)
        if self.path_attribute is not None:
            raise Exception('Complex type %s cannot be written into an attribute %s' % (self.__class__, self.path_attribute))

    def validate(self, data):
        """Checks if the data is an instance of the L{clazz}."""
        if not isinstance(data, self.clazz):
            return "Data(%s) is not of class %s" % (data, self.clazz)
        return True

    def save(self, node, data):
        """Store the data as a complex structure."""
        data.write(node)

    def load(self, node):
        """Load the complex data from an xml DOM node."""
        instance = self.clazz()
        instance.read(node)
        return instance

    def __repr__(self):
        """Override L{Field.__repr__} for documentation purposes."""
        return 'Node%s:{ %s }' % (self._traits(), self.clazz.__name__)

class String(Field):
    """
    A field representing a string value.
    """
    def __init__(self, path, max_length=None, empty=True, **kwargs):
        return super(String, self).__init__(path,
                                            max_length=max_length,
                                            empty=empty,
                                            **kwargs)
    def data2str(self, data):
        return str(data)
    def str2data(self, text):
        return text
    def validate(self, data):
        if (self.max_length != None) and len(str(data)) >= self.max_length:
            return "The string is too long (max_length=%d)." % (self.max_length,)
        return True

def apply_parent_validation(clazz, error_prefix=None):
    """
    Decorator to automatically invoke parent class validation before applying
    custom validation rules. Usage::

        class Child(Parent):
            @apply_parent_validation(Child, error_prefix="From Child: ")
            def validate(data):
                # I can assume now that the parent validation method succeeded.
                # ...
    """
    def decorator(func):
        def inner(self, data):
            base_validation = clazz.validate(self, data)
            if base_validation != True:
                if error_prefix is not None:
                    return error_prefix + base_validation
                return base_validation
            return func(self, data)
        return inner
    return decorator

class Pattern(String):
    """A string matching a pattern.
    @ivar pattern: a regular expression to which a value has to confirm."""
    pattern = None
    def __init__(self, path, pattern, **kwargs):
        """
        Initizlizes a Pattern field.
        @param path: L{Field.path}
        @param pattern: a regular expression describing the format of the data
        """
        return super(Pattern, self).__init__(path=path, pattern=pattern, **kwargs)

    @apply_parent_validation(String)
    def validate(self, data):
        """Checks if the pattern matches the data."""
        if self.pattern.match(data) is None:
            return "Does not matches the defined pattern"
        return True

class Decimal(Field):
    default=0
    def data2str(self, data):
        return '%d' % data
    def str2data(self, text):
        return int(text)

class Double(Field):
    """Floating point value"""
    def __init__(self, path, precision=3, **kwargs):
        """
        @param precision: Precision of the value
        """
        return super(Double, self).__init__(path=path, precision=precision, **kwargs)
    def data2str(self, data):
        return ('%%.%df' % (self.precision,)) % (data,)
    def str2data(self, text):
        return float(text)

class Boolean(Field):
    values = (True, False)
    def data2str(self, data):
        return (data and 'true') or 'false'
    def str2data(self, text):
        if text == 'true':
            return True
        if text == 'false':
            return False
        return 'invalid'

class Long(Field):
    default=0
    def data2str(self, data):
        return '%d' % (data,)
    def str2data(self, text):
        return long(text)

class Integer(Long):
    pass

class Url(Pattern):
    """
    Note: a 'http://localhost/' does not considered to be a valid url.
    So any other alias name that you migght use in your local network
    (and defined in your /etc/hosts file) could possibly be considered
    invalid.

    >>> u = Url('dummy')
    >>> u.validate('http://google.com')
    True
    >>> u.validate('https://google.com')
    True
    >>> u.validate('http://google.com/')
    True
    >>> u.validate('http://google.com/some')
    True
    >>> u.validate('http://google.com/some/more')
    True
    >>> u.validate('http://google.com/even///more/')
    True
    >>> u.validate('http://google.com/url/?with=some&args')
    True
    >>> u.validate('http://google.com/empty/args/?')
    True
    >>> u.validate('http://google.com/some/;-)?a+b=c&&=11')
    True
    >>> u.validate('http:/google.com') != True
    True
    >>> u.validate('mailto://google.com') != True
    True
    >>> u.validate('http://.google.com') != True
    True
    >>> u.validate('http://google..com') != True
    True
    >>> u.validate('http://;-).google.com') != True
    True
    >>> u.validate('https://sandbox.google.com/checkout/view/buy?o=shoppingcart&shoppingcart=515556794648982')
    True
    >>> u.validate('http://127.0.0.1:8000/digital/order/continue/')
    True
    """
    def __init__(self, path, **kwargs):
        import re
        # Regular expression divided into chunks:
        protocol  = r'((http(s?)|ftp)\:\/\/|~/|/)?'
        user_pass = r'([\w]+:\w+@)?'
        domain    = r'(([a-zA-Z]{1}([\w\-]+\.)+([\w]{2,5}))|(([0-9]+\.){3}[0-9]+))'
        port      = r'(:[\d]{1,5})?'
        file    = r'(/[\w\.\+-;\(\)]*)*'
        params    = r'(\?.*)?'
        pattern = re.compile('^' + protocol + user_pass + domain + port + file + params + '$')
        Pattern.__init__(self, path, pattern=pattern, **kwargs)

    @apply_parent_validation(Pattern, error_prefix="Url: ")
    def validate(self, data):
        return True

class Email(Pattern):
    def __init__(self, path, **kwargs):
        import re
        pattern = re.compile(r'^[a-zA-Z0-9\.\_\%\-\+]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        Pattern.__init__(self, path, pattern=pattern, **kwargs)

    @apply_parent_validation(Pattern, error_prefix="Email: ")
    def validate(self, data):
        return True

class Html(String):
    pass

class LanguageCode(Pattern):
    def __init__(self, path):
        return super(LanguageCode, self).__init__(path=path, pattern='^en_US$')

class Phone(Pattern):
    def __init__(self, path, **kwargs):
        import re
        pattern = re.compile(r'^[0-9\+\-\(\)\ ]+$')
        Pattern.__init__(self, path, pattern=pattern, **kwargs)

    @apply_parent_validation(Pattern, error_prefix="Phone: ")
    def validate(self, data):
        return True

class Zip(Pattern):
    """
    Represents a zip code.

    >>> zip = Zip('dummy')
    >>> zip.validate('94043')
    True
    >>> zip.validate('abCD123')
    True
    >>> zip.validate('123*') != True
    True
    >>> zip.validate('E6 1EX')
    True

    >>> zip_pattern = Zip('dummy', complete=False)
    >>> zip_pattern.validate('SW*')
    True
    """
    def __init__(self, path, complete=True, **kwargs):
        import re
        if complete:
            pattern = re.compile(r'^[0-9a-zA-Z- ]+$')
        else:
            pattern = re.compile(r'^[0-9a-zA-Z- \*]+$')
        Pattern.__init__(self, path, pattern=pattern, **kwargs)

    @apply_parent_validation(Pattern, error_prefix="Zip: ")
    def validate(self, data):
        return True

class IP(Pattern):
    """
    Represents an IP address.

    Currently only IPv4 addresses in decimal notation are accepted.

    >>> ip = IP('dummy')
    >>> ip.validate('127.0.0.1')
    True
    >>> ip.validate('10.0.0.1')
    True
    >>> ip.validate('255.17.101.199')
    True
    >>> ip.validate('1.1.1.1')
    True
    >>> ip.validate('1.2.3') != True
    True
    >>> ip.validate('1.2.3.4.5') != True
    True
    >>> ip.validate('1.2.3.256') != True
    True
    >>> ip.validate('1.2.3.-1') != True
    True
    >>> ip.validate('1.2..3') != True
    True
    >>> ip.validate('.1.2.3.4') != True
    True
    >>> ip.validate('1.2.3.4.') != True
    True
    >>> ip.validate('1.2.3.-') != True
    True
    >>> ip.validate('01.2.3.4') != True
    True
    >>> ip.validate('1.02.3.4') != True
    True
    """
    def __init__(self, path, **kwargs):
        import re
        num_pattern = r'(0|([1-9][0-9]?)|(1[0-9]{2})|(2((5[0-5])|([0-4][0-9]))))'
        pattern = re.compile(r'^%s\.%s\.%s\.%s$' % (num_pattern,num_pattern,num_pattern,num_pattern))
        Pattern.__init__(self, path, pattern=pattern, **kwargs)

    @apply_parent_validation(Pattern, error_prefix="IP address: ")
    def validate(self, data):
        return True

# TODO
class ID(String):
    empty = False

    @apply_parent_validation(String, error_prefix="ID: ")
    def validate(self, data):
        if len(data) == 0:
            return "ID has to be non-empty"
        return True

class Any(Field):
    """Any text value. This field is tricky. Since any data could be stored in
    the field we can't handle all the cases.
    The class uses xml.marshal.generic to convert python-ic simple data
    structures into xml. By simple we mean any POD. Note that a class derived
    from object requires the marshaller to be extended that's why this field
    does not accept instance of such classes.
    When reading XML we consider node XML text as if it was previously
    generated by a xml marshaller facility (xml.marshal.generic.dumps).
    If it fails then we consider the data as if it was produced by some other
    external source and return False indicating that user Controller should
    parse the XML data itself. In such case field value is False.
    To access the original XML input two class member variables are populated:
    - <field>_xml contains the original XML text
    - <field>_dom contains the corresponding XML DOM node
    """
    def __init__(self, *args, **kwargs):
        obj = super(Any, self).__init__(*args, **kwargs)
        if self.path_attribute is not None:
            raise ValueError('gxml.Any field cannot be bound to an attribute!')
        return obj

    def save(self, node, data):
        return encoder().serialize(data, node)

    def load(self, node):
        return decoder().deserialize(node)

    def validate(self, data):
        # Always return True, since any data is allowed
        return True

#class DateTime(Field):
#    from datetime import datetime
#    def validate(self, data):
#        return isinstance(data, datetime)
#    def data2str(self, data):
#        pass


class Timestamp(Field):
    def validate(self, data):
        if not isinstance(data, datetime):
            return "Timestamp has to be an instance of datetime.datetime"
        return True
    def data2str(self, data):
        return data.isoformat()
    def str2data(self, text):
        y,m,d=text[0:10].split('-')
        H,M,S=text[11:19].split(':')
        return datetime(int(y),int(m),int(d),int(H),int(M),int(S))

if __name__ == "__main__":
    def run_doctests():
        import doctest
        doctest.testmod()
    run_doctests()
