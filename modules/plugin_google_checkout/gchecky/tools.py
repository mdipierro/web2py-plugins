"""
The module provides two classes encoder and decoder that allow to
serialize and deserialize python-ish PODs into/from XML.
Note that data should be simple:
None, True, False, strings, lists, tupls, dicts
Anything other than this will trigger an error.

Also note that any circular references in the data will also trigger an error,
so please do not try to serialize something like:
>>> a = []
>>> a.append(a)
>>> a
[[...]]

Important notes:
- tuples are treated as lists and deserialized into lists.
- any empty list, tuple or dictionary is deserialized into None.

TODO: Expand the notes on how exactly the data values are serialized.

Some doctests:

>>> def test_enc_dec(data, return_res=False):
...   from xml.dom.minidom import parseString
...   doc = parseString('<?xml version="1.0"?><dummy/>')
...   encoder().serialize(data, doc.documentElement)
...   xml = doc.toprettyxml('  ')
...   data2 = decoder().deserialize(doc.documentElement)
...   if data2 != data:
...       msg = '''--- Expected: ---
...                 %s
...                 --- Got: ---
...                 %s
...                 === Xml: ===
...                 %s
...       ''' % (data, data2, xml)
...       if return_res:
...          return data2
...       print msg

>>> test_enc_dec(None)
>>> test_enc_dec(True)
>>> test_enc_dec(False)
>>> test_enc_dec('string')
>>> test_enc_dec(u'string')
>>> test_enc_dec({'a':'b'})
>>> test_enc_dec([1,2])
>>> test_enc_dec(['1',2])
>>> test_enc_dec([1])
>>> test_enc_dec({'':'aa'})
>>> test_enc_dec(['_'])
>>> test_enc_dec(['aa',['bb','cc'],[None], None, ['_']])
>>> test_enc_dec([[False]])
>>> test_enc_dec([[False], None])
>>> test_enc_dec([False, True, [False], [[True]], [None]])
>>> test_enc_dec({'vasya':['aa', 'bb']})
>>> test_enc_dec({'name':['Peter', 'Mary'], 'age':[11, 15]})

To fix:
>>> test_enc_dec([], return_res=True) != None
False
>>> test_enc_dec({}, return_res=True) != None
False
"""

TRUE_LABEL = u'True'
FALSE_LABEL = u'False'

class decoder:
    def deserialize(self, node):
        """
        >>> from xml.dom.minidom import parseString
        >>> doc = parseString('<?xml version="1.0"?><merchant-private-data><I><want/>to</I><spend>a<month or="two"/>at<Maui/>!!</spend></merchant-private-data>')
        >>> decoder().deserialize(doc.documentElement)
        {u'I': {None: [u'to'], u'want': None}, u'spend': {None: [u'a', u'at', u'!!'], u'Maui': None, u'month': {u'or': u'two'}}}
        """
        data = self._decode_into_dict(node)
        return data

    def _reduce_list(self, l):
        if not isinstance(l, list):
            return l
        if len(l) == 0:
            return l
        if len(l) == 1:
            return l[0]
        if l[-1] is None:
            return l[:-1]
        return l

    def _reduce_diction(self, diction):
        # None value
        if len(diction) == 0:
            return None

        # Strings, booleans and None values
        if len(diction) == 1 and None in diction:
            if len(diction[None]) == 1:
                return diction[None][0]
            return diction[None]

        # Lists
        if len(diction) == 1 and '_' in diction:
            return self._reduce_list(diction['_'])

        data = {}
        for key in diction.keys():
            if key is None:
                data[None] = diction[None]
            else:
                data[decoder._decode_tag(key)] = self._reduce_list(diction[key])
            # elif data '_'
        diction = data
        return diction

    @classmethod
    def _decode_tag(clazz, tag):
        if len(tag) > 1 and tag[0:2] == '__':
            return tag[2:]
        return tag

    def _decode_into_dict(self, node):
        diction = {None:[]}
        for child in node.childNodes:
            if child.nodeType is child.TEXT_NODE or child.nodeType == child.CDATA_SECTION_NODE:
                diction[None].append(decoder._decode_string(child.data))
            elif node.nodeType is child.ELEMENT_NODE:
                data = self._decode_into_dict(child)
                self._add_to_dict(diction, child.tagName, data)
            else:
                #TODO !!
                pass
        for attr in node.attributes.keys():
            data = decoder._decode_string(node.attributes[attr].nodeValue)
            self._add_to_dict(diction, attr, data)
        if len(diction[None]) == 0:
            del diction[None]
        return self._reduce_diction(diction)

    def _add_to_dict(self, diction, key, data):
        if key not in diction:
            diction[key] = [data]
        else:
#            if not isinstance(diction[key], list):
#                diction[key] = [diction[key]]
            diction[key].append(data)

    @classmethod
    def _decode_string(clazz, str):
        """
        >>> decoder._decode_string(None)
        >>> decoder._decode_string('True')
        True
        >>> decoder._decode_string('False')
        False
        >>> decoder._decode_string('11')
        11
        >>> decoder._decode_string('12L')
        12L
        >>> decoder._decode_string('11.')
        11.0
        >>> decoder._decode_string('some')
        u'some'
        >>> decoder._decode_string('"some"')
        u'"some"'
        >>> decoder._decode_string('"some')
        u'"some'
        """
        if str is None:
            return None
        elif str == TRUE_LABEL:
            return True
        elif str == FALSE_LABEL:
            return False
        try:
            return int(str)
        except Exception:pass
        try:
            return long(str)
        except Exception:pass
        try:
            return float(str)
        except Exception:pass
        str = unicode(str)
        if str[0] == '"' and str[-1] == '"':
            original = (str.replace('\\"', '"'))[1:-1]
            if encoder._escape_string(original) == str:
                return original
        return unicode(str)

class encoder:
    def serialize(self, data, xml_node):
        self.__doc = xml_node.ownerDocument
        self.__markers = {}
        self._encode(data=data, node=xml_node)

    @classmethod
    def _encode_tag(clazz, tag):
        return '__' + tag

    def _create_element(self, tag):
        # TODO Account for wierd characters
        return self.__doc.createElement(tag)

    def _create_text(self, value):
        return self.__doc.createTextNode(value)

    @classmethod
    def _escape_string(clazz, str):
        if str.find('"') < 0:
            if str != TRUE_LABEL and str != FALSE_LABEL:
                try: int(str)
                except:
                    try: long(str)
                    except:
                        try: float(str)
                        except:
                            # Great - the string won't be confused with int, long,
                            # float or boolean - just spit it out then.
                            return str
        # Ok, do the safe escaping of the string value
        return '"' + str.replace('"', '\\"') + '"'

    def _encode(self, data, node):
        """
        @param node Is either a string or an XML node. If its a string then
                    a node with such a name should be created, otherwise
                    the existing xml node should be populated.
        """
        if isinstance(data, (list, tuple)):
            self.__mark(data)
            children = []
            if isinstance(node, basestring):
                tag = encoder._encode_tag(node)
                parent = None
            else:
                tag = '_'
                parent = node

            l = list(data)
            if len(l) >= 1:
                l.append(None)
            for d in l:
                child = self._create_element(tag)
                if parent is not None:
                    parent.appendChild(child)
                self._encode(d, child)
                children.append(child)

            return children
        else:
            if isinstance(node, basestring):
                parent = self._create_element(encoder._encode_tag(node))
            else:
                parent = node

            if isinstance(data, dict):
                self.__mark(data)
                for key in data.keys():
                    children = self._encode(data[key], key)
                    if isinstance(children, list):
                        for child in children:
                            parent.appendChild(child)
                    else:
                        parent.appendChild(children)
                self.__unmark(data)
            else:
                if isinstance(data, basestring):
                    child = self._create_text(encoder._escape_string(unicode(data)))
                elif data is None:
                    child = None
                elif isinstance(data, (int, long, float)):
                    child = self._create_text(unicode(data))
                elif data is True:
                    child = self._create_text(TRUE_LABEL)
                elif data is False:
                    child = self._create_text(FALSE_LABEL)
                else:
                    raise ValueError('Serialisation of "%s" is not supported.' % (data.__class__,))

                if child is not None:
                    parent.appendChild(child)
            return [parent]

    def __mark(self, obj):
        if id(obj) in self.__markers:
            raise ValueError('gchecky.encoder can\'t handle cyclic references.')
        self.__markers[id(obj)] = obj

    def __unmark(self, obj):
        del self.__markers[id(obj)]

if __name__ == "__main__":
    def run_doctests():
        import doctest
        doctest.testmod()
    run_doctests()
