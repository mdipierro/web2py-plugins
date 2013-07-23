"""
gchecky.model module describes the mapping between Google Checkout API (GC API)
XML messages (GC API XML Schema) and data classes.

This module uses L{gchecky.gxml} to automate much of the work so that
the actual logic is not cluttered with machinery.

The module code is simple and self-documenting. Please read the source code for
simple description of the data-structures. Note that it tries to follow exactly
the official GC API XML Schema.

All the comments for the GC API are at U{Google Chackout API documentation
<http://code.google.com/apis/checkout/developer/>}. Please consult it for any
questions about GC API functioning.

@author: etarassov
@version: $Revision: 129 $
@contact: gchecky at gmail
"""

import gxml
from data import CountryCode, PresentOrNot

def test_document(doc, xml_text=None):
    """
    Method used in doctests: ensures that a document is properly serialized.
    """

    def normalize_xml(xml_text):
        """
        Normalize the xml text to canonical form, so that two xml text chunks
        could be compared directly as strings.
        """
        # If xml misses header, then add it.
        if len(xml_text) < 2 or xml_text[0:2] != "<?":
            xml_text = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml_text
        from xml.dom.minidom import parseString
        doc = parseString(xml_text)

        text = doc.toprettyxml('')
        # To avoid formatting problems we just strip all the line returns and
        # spaces (while it breaks XML into a text string it still makes
        # this form a 'canonical' one).
        return text.replace('\n', '').replace(' ', '')

    expected_xml = ((xml_text is not None) and normalize_xml(xml_text)) or None
    obtained_xml = normalize_xml(doc.toxml(pretty='  '))

    if expected_xml is not None and expected_xml != obtained_xml:
        print "Expected:\n\n%s\n\nGot:\n\n%s\n" % (xml_text, doc.toxml('  '))

    doc2 = gxml.Document.fromxml(doc.toxml())
    if not (doc == doc2):
        print '''
              Failed to correctly interpret the generated XML for this document:
              Original:
              %s
              Parsed:
              %s
              ''' % (doc.toxml(pretty=True), doc2.toxml())

def test_node(node, xml_text=None):
    """
    Method used in doctests. Ensure that a node is properly serialized.
    """
    class Dummy(gxml.Document):
        tag_name='dummy'
        data=gxml.Complex('node', node.__class__, required=True)
    if xml_text is not None:
        xml_text = xml_text.replace('<', '  <')
        # TODO ...just ugly (below)
        xml_text = "<dummy xmlns='http://checkout.google.com/schema/2'>%s</dummy>" % (xml_text,)
    test_document(Dummy(data=node), xml_text)

CURRENCIES = ('USD', 'GBP')

class price_t(gxml.Node):
    value    = gxml.Double('', default=0)
    currency = gxml.String('@currency', values=CURRENCIES)

DISPLAY_DISPOSITION = ('OPTIMISTIC', 'PESSIMISTIC')
class digital_content_t(gxml.Node):
    description    = gxml.Html('description', max_length=1024, required=False)
    email_delivery = gxml.Boolean('email-delivery', required=False)
    key            = gxml.String('key', required=False)
    url            = gxml.String('url', required=False)
    display_disposition = gxml.String('display-disposition', required=False,
                                      values=DISPLAY_DISPOSITION)

class item_weight_t(gxml.Node):
    value = gxml.Double('@value') # , negative=False
    unit  = gxml.String('@unit', values=('LB',))

class item_t(gxml.Node):
    """
    >>> test_node(item_t(name='Peter', description='The Great', unit_price=price_t(value=1, currency='GBP'), quantity=1, merchant_item_id='custom_merchant_item_id',
    ...                  merchant_private_item_data=['some', {'private':'data', 'to':['test','the'],'thing':None}, '!! Numbers: ', None, False, True, [11, 12., [13.4]]])
    ...          )
    >>> test_node(item_t(name='Name with empty description', description='', unit_price=price_t(value=1, currency='GBP'), quantity=1))
    """
    name                = gxml.String('item-name')
    description         = gxml.String('item-description')
    unit_price          = gxml.Complex('unit-price', price_t)
    quantity            = gxml.Decimal('quantity')
    item_weight         = gxml.Complex('item-weight', item_weight_t, required=False)
    merchant_item_id    = gxml.String('merchant-item-id', required=False)
    tax_table_selector  = gxml.String('tax-table-selector', required=False)
    digital_content     = gxml.Complex('digital-content', digital_content_t, required=False)
    merchant_private_item_data = gxml.Any('merchant-private-item-data',
                                          save_node_and_xml=True,
                                          required=False)

class postal_area_t(gxml.Node):
    """
    >>> test_node(postal_area_t(country_code = 'VU'),
    ... '''
    ... <node><country-code>VU</country-code></node>
    ... '''
    ... )
    """
    country_code        = CountryCode('country-code')
    postal_code_pattern = gxml.String('postal-code-pattern', required=False)

class tax_area_t(gxml.Node):
    world_area   = PresentOrNot('world-area', required=False)
    postal_area  = gxml.Complex('postal-area', postal_area_t, required=False)
    us_state        = gxml.String('us-state-area/state', required=False)
    us_zip_pattern  = gxml.String('us-zip-area/zip-pattern', required=False) # regex: [a-zA-Z0-9_]+\*? Note the optional asterisk
    us_country_area = gxml.String('us-country-area/country-area', values=('CONTINENTAL_48', 'FULL_50_STATES', 'ALL'), required=False) # enum('CONTINENTAL_48', 'FULL_50_STATES', 'ALL')

class areas_t(gxml.Node):
    """
    Represents a list of regions.

    >>> test_node(
    ...   areas_t(
    ...     states = ['LA', 'NY'],
    ...     country_areas = ['ALL', 'CONTINENTAL_48']
    ...   )
    ... ,
    ... '''
    ... <node>
    ... <us-state-area>
    ...   <state>LA</state>
    ... </us-state-area>
    ... <us-state-area>
    ...   <state>NY</state>
    ... </us-state-area>
    ... <us-country-area>
    ...   <country-area>ALL</country-area>
    ... </us-country-area>
    ... <us-country-area>
    ...   <country-area>CONTINENTAL_48</country-area>
    ... </us-country-area>
    ... </node>
    ... '''
    ... )
    """
    states        = gxml.List('', gxml.String('us-state-area/state'), required=False)
    zip_patterns  = gxml.List('', gxml.String('us-zip-area/zip-pattern'), required=False) # regex: [a-zA-Z0-9_]+\*? Note the optional asterisk
    country_areas = gxml.List('', gxml.String('us-country-area/country-area'), values=('CONTINENTAL_48', 'FULL_50_STATES', 'ALL'), required=False) # enum('CONTINENTAL_48', 'FULL_50_STATES', 'ALL')

class allowed_areas_t(areas_t):
    postal_areas  = gxml.List('', gxml.Complex('postal-area', postal_area_t), required=False)
    world_area   = PresentOrNot('world-area', required=False)

class excluded_areas_t(areas_t):
    postal_areas  = gxml.List('', gxml.Complex('postal-area', postal_area_t), required=False)

class tax_rule_t(gxml.Node):
    rate     = gxml.Double('rate', default=0.)
    tax_area = gxml.Complex('tax-area', tax_area_t, required=False)
    tax_areas = gxml.List('tax-areas', gxml.Complex('', tax_area_t), required=False)

class default_tax_rule_t(tax_rule_t):
    shipping_taxed = gxml.Boolean('shipping-taxed', required=False)

class alternate_tax_rule_t(tax_rule_t):
    pass

class default_tax_table_t(gxml.Node):
    tax_rules = gxml.List('tax-rules', gxml.Complex('default-tax-rule', default_tax_rule_t))

class alternate_tax_table_t(gxml.Node):
    name                = gxml.String('@name')
    standalone          = gxml.Boolean('@standalone')
    alternate_tax_rules = gxml.List('alternate-tax-rules', gxml.Complex('alternate-tax-rule', alternate_tax_rule_t))

class tax_tables_t(gxml.Node):
    merchant_calculated = gxml.Boolean('@merchant-calculated', default=False)
    default             = gxml.Complex('default-tax-table', default_tax_table_t)
    alternates          = gxml.List('alternate-tax-tables', gxml.Complex('alternate-tax-table', alternate_tax_table_t), required=False)

class merchant_calculations_t(gxml.Node):
    merchant_calculations_url = gxml.Url('merchant-calculations-url')
    accept_merchant_coupons   = gxml.Boolean('accept-merchant-coupons', required=False)
    accept_gift_certificates  = gxml.Boolean('accept-gift-certificates', required=False)

class shipping_option_t(gxml.Node):
    """
    Represents information about shipping costs.

    >>> test_node(
    ...   shipping_option_t(
    ...       name = 'Testing',
    ...         price = price_t(
    ...             currency = 'GBP',
    ...             value = 9.99,
    ...             ),
    ...         allowed_areas = allowed_areas_t(
    ...             world_area = True,
    ...             ),
    ...         excluded_areas = excluded_areas_t(
    ...             postal_areas = [postal_area_t(
    ...                 country_code = 'US',
    ...                 )],
    ...             ),
    ...         )
    ... , '''
    ... <node name='Testing'>
    ...   <price currency='GBP'>9.990</price>
    ...   <shipping-restrictions>
    ...     <allowed-areas>
    ...       <world-area/>
    ...     </allowed-areas>
    ...     <excluded-areas>
    ...       <postal-area>
    ...         <country-code>US</country-code>
    ...       </postal-area>
    ...     </excluded-areas>
    ...   </shipping-restrictions>
    ... </node>
    ... ''')
    """
    name = gxml.String('@name') # Attribute, len <= 255, not-empty
    price = gxml.Complex('price', price_t)
    allowed_areas  = gxml.Complex('shipping-restrictions/allowed-areas', allowed_areas_t, required=False)
    excluded_areas = gxml.Complex('shipping-restrictions/excluded-areas', excluded_areas_t, required=False)

class address_filters_t(gxml.Node):
    allowed_areas   = gxml.Complex('allowed-areas', allowed_areas_t, required=False)
    excluded_areas  = gxml.Complex('excluded-areas', excluded_areas_t, required=False)
    allow_us_po_box = gxml.Boolean('allow-us-po-box', required=False)

class flat_rate_shipping_t(shipping_option_t):
    pass
class merchant_calculated_shipping_t(shipping_option_t):
    address_filters = gxml.Complex('address-filters',
                                   address_filters_t, required=False)

# TODO: Add some special type of validation to:
# shipping_company and shipping_type fields. See:
# http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Tag_Reference.html#tag_shipping-type
class carrier_calculated_shipping_option_t(gxml.Node):
    price = gxml.Complex('price', price_t)
    shipping_company = gxml.String('shipping-company', values=('FedEx', 'UPS', 'USPS'))
    carrier_pickup = gxml.String('carrier-pickup', values=('REGULAR_PICKUP',
                                                           'SPECIAL_PICKUP',
                                                           'DROP_OFF'),
                                                   default='DROP_OFF',
                                                   required=False)
    shipping_type = gxml.String('shipping-type')
    additional_fixed_charge = gxml.Complex('additional-fixed-charge', price_t, required=False)
    additional_variable_charge_percent = gxml.Double('additional-variable-charge-percent', required=False)

class measure_t(gxml.Node):
    unit  = gxml.String('@unit', values=('IN',), default='IN')
    value = gxml.Decimal('@value')

class ship_from_t(gxml.Node):
    id           = gxml.String('id')
    city         = gxml.String('city')
    region       = gxml.String('region', empty=True)
    postal_code  = gxml.Zip('postal-code')
    country_code = CountryCode('country-code')

class shipping_package_t(gxml.Node):
    delivery_address_category = gxml.String('delivery-address-category',
                                            values=('RESIDENTIAL',
                                                    'COMMERCIAL'), required=False)
    height = gxml.Complex('height', measure_t)
    length = gxml.Complex('length', measure_t)
    ship_from = gxml.Complex('ship-from', ship_from_t)
    width  = gxml.Complex('width', measure_t)

class carrier_calculated_shipping_t(gxml.Node):
    carrier_calculated_shipping_options = gxml.List('carrier-calculated-shipping-options',
                                                    gxml.Complex('carrier-calculated-shipping-option',
                                                                 carrier_calculated_shipping_option_t))
    shipping_packages                   = gxml.List('shipping-packages',
                                                    gxml.Complex('shipping-package',
                                                                 shipping_package_t))

class pickup_t(gxml.Node):
    name = gxml.String('@name')
    price = gxml.Complex('price', price_t)

class shipping_methods_t(gxml.Node):
    carrier_calculated_shippings  = gxml.List('', gxml.Complex('carrier-calculated-shipping', carrier_calculated_shipping_t), required=False) # list of carrier_calculated_shipping_t
    flat_rate_shippings           = gxml.List('', gxml.Complex('flat-rate-shipping', flat_rate_shipping_t), required=False) # list of flat_rate_shipping_t
    merchant_calculated_shippings = gxml.List('', gxml.Complex('merchant-calculated-shipping', merchant_calculated_shipping_t), required=False) # list of merchant_calculated_shipping_t
    pickups                       = gxml.List('', gxml.Complex('pickup', pickup_t), required=False) # list of pickup_t

URL_PARAMETER_TYPES=(
    'buyer-id', # A Google-assigned value that uniquely identifies a customer email address.
    'order-id', # A Google-assigned value that uniquely identifies an order. This value is displayed in the Merchant Center for each order. If you have implemented the Notification API, you will also see this value in all Google Checkout notifications.
    'order-subtotal', # The total cost for all of the items in the order including coupons and discounts but excluding taxes and shipping charges.
    'order-subtotal-plus-tax', # The total cost for all of the items in the order, including taxes, coupons and discounts, but excluding shipping charges.
    'order-subtotal-plus-shipping', # The total cost for all of the items in the order, including shipping charges, coupons and discounts, but excluding taxes.
    'order-total', # The total cost for all of the items in the order, including taxes, shipping charges, coupons and discounts.
    'tax-amount', # The total amount of taxes charged for an order.
    'shipping-amount', # The shipping cost associated with an order.
    'coupon-amount', # The total amount of all coupons factored into the order total.
    'billing-city', # The city associated with the order's billing address.
    'billing-region', # The U.S. state associated with the order's billing address.
    'billing-postal-code', # The five-digit U.S. zip code associated with the order's billing address.
    'billing-country-code', # The two-letter ISO 3166 country code associated with the order's billing address.
    'shipping-city', # The city associated with the order's shipping address.
    'shipping-region', # The U.S. state associated with the order's shipping address.
    'shipping-postal-code', # The five-digit U.S. zip code associated with the order's shipping address.
    'shipping-country-code', # The two-letter ISO 3166 country code associated with the order's shipping address.',
)

class url_parameter_t(gxml.Node):
    name = gxml.String('@name')
    type = gxml.String('@type', values=URL_PARAMETER_TYPES)

class parameterized_url_t(gxml.Node):
    url        = gxml.Url('@url', required=True)
    parameters = gxml.List('parameters', gxml.Complex('url-parameter', url_parameter_t), required=True)


class rounding_policy_t(gxml.Node):
    mode = gxml.String('mode', choices=('UP',
                                        'DOWN',
                                        'CEILING',
                                        'FLOOR',
                                        'HALF_UP',
                                        'HALF_DOWN',
                                        'HALF_EVEN',
                                        'UNNECESSARY'))
    rule = gxml.String('rule', choices=('PER_LINE',
                                        'TOTAL'))

class checkout_flow_support_t(gxml.Node):
    """
    >>> test_node(
    ...   checkout_flow_support_t(
    ...     parameterized_urls = [
    ...         parameterized_url_t(
    ...             url='http://google.com/',
    ...             parameters=[url_parameter_t(name='a', type='buyer-id')]
    ...         ),
    ...         parameterized_url_t(
    ...             url='http://yahoo.com/',
    ...             parameters=[url_parameter_t(name='a', type='shipping-city'),
    ...                         url_parameter_t(name='b', type='tax-amount')]
    ...         ),
    ...         parameterized_url_t(
    ...             url='http://mozilla.com/',
    ...             parameters=[url_parameter_t(name='a', type='order-total'),
    ...                         url_parameter_t(name='b', type='shipping-region'),
    ...                         url_parameter_t(name='c', type='shipping-country-code')]
    ...         )
    ...     ],
    ...   )
    ... ,
    ... '''
    ... <node>
    ...   <parameterized-urls>
    ...     <parameterized-url url="http://google.com/">
    ...       <parameters>
    ...         <url-parameter name="a" type="buyer-id"/>
    ...       </parameters>
    ...     </parameterized-url>
    ...     <parameterized-url url="http://yahoo.com/">
    ...       <parameters>
    ...         <url-parameter name="a" type="shipping-city"/>
    ...         <url-parameter name="b" type="tax-amount"/>
    ...       </parameters>
    ...     </parameterized-url>
    ...     <parameterized-url url="http://mozilla.com/">
    ...       <parameters>
    ...         <url-parameter name="a" type="order-total"/>
    ...         <url-parameter name="b" type="shipping-region"/>
    ...         <url-parameter name="c" type="shipping-country-code"/>
    ...       </parameters>
    ...     </parameterized-url>
    ...   </parameterized-urls>
    ... </node>
    ... '''
    ... )
    """
    edit_cart_url              = gxml.Url('edit-cart-url', required=False)         # optional, URL
    continue_shopping_url      = gxml.Url('continue-shopping-url', required=False) # optional, URL
    tax_tables                 = gxml.Complex('tax-tables', tax_tables_t, required=False) # optional, tax_tables_t
    shipping_methods           = gxml.Complex('shipping-methods', shipping_methods_t, required=False) # optional, shipping_methods_t
    parameterized_urls         = gxml.List('parameterized-urls', gxml.Complex('parameterized-url', parameterized_url_t), required=False)
    merchant_calculations      = gxml.Complex('merchant-calculations', merchant_calculations_t, required=False) # optional, merchant_calculations_t
    request_buyer_phone_number = gxml.Boolean('request-buyer-phone-number', required=False) # optional, Boolean
    analytics_data             = gxml.String('analytics-data', required=False)
    platform_id                = gxml.Long('platform-id', required=False)
    rounding_policy            = gxml.Complex('rounding-policy', rounding_policy_t, required=False)

class shopping_cart_t(gxml.Node):
    expiration            = gxml.Timestamp('cart-expiration/good-until-date', required=False)
    items                 = gxml.List('items', gxml.Complex('item', item_t))
    merchant_private_data = gxml.Any('merchant-private-data',
                                     save_node_and_xml=True,
                                     required=False)

class hello_t(gxml.Document):
    """
    Represents a simple test that verifies that your server communicates
    properly with Google Checkout. The fourth step of
    the U{Getting Started with Google Checkout<http://code.google.com/apis/checkout/developer/index.html#integration_overview>}
    section of the Developer's Guide explains how to execute this test.

    >>> test_document(hello_t(),
    ...               "<hello xmlns='http://checkout.google.com/schema/2'/>"
    ... )
    """
    tag_name='hello'

class bye_t(gxml.Document):
    """
    Represents a response that indicates that Google correctly received
    a <hello> request.

    >>> test_document(
    ...     bye_t(serial_number="7315dacf-3a2e-80d5-aa36-8345cb54c143")
    ... ,
    ...     '''
    ...     <bye xmlns="http://checkout.google.com/schema/2"
    ...           serial-number="7315dacf-3a2e-80d5-aa36-8345cb54c143" />
    ...     '''
    ... )
    """
    tag_name = 'bye'
    serial_number = gxml.ID('@serial-number')

class checkout_shopping_cart_t(gxml.Document):
    tag_name = 'checkout-shopping-cart'
    shopping_cart                = gxml.Complex('shopping-cart', shopping_cart_t)
    checkout_flow_support        = gxml.Complex('checkout-flow-support/merchant-checkout-flow-support', checkout_flow_support_t)
    request_initial_auth_details = gxml.Boolean('order-processing-support/request-initial-auth-details', required=False)

class coupon_gift_adjustment_t(gxml.Node):
    code              = gxml.String('code')
    calculated_amount = gxml.Complex('calculated-amount', price_t, required=False)
    applied_amount    = gxml.Complex('applied-amount', price_t)
    message           = gxml.String('message', required=False)

class merchant_codes_t(gxml.Node):
    gift_certificate_adjustment = gxml.List('', gxml.Complex('gift-certificate-adjustment', coupon_gift_adjustment_t))
    coupon_adjustment           = gxml.List('', gxml.Complex('coupon-adjustment', coupon_gift_adjustment_t))

class shipping_adjustment_t(gxml.Node):
    shipping_name = gxml.String('shipping-name')
    shipping_cost = gxml.Complex('shipping-cost', price_t)

class carrier_calculated_shipping_adjustment_t(gxml.Node):
    shipping_name = gxml.String('shipping-name')
    shipping_cost = gxml.Complex('shipping-cost', price_t)

# Two classes below represent the single 'shipping' tag, which content
# depends on the context the XML Node is present.
# http://code.google.com/apis/checkout/developer/index.html#tag_shipping
class shipping_in_order_adjustment_t(gxml.Node):
    carrier_calculated_shipping_adjustment  = gxml.Complex('carrier-calculated-shipping-adjustment',
                                                           carrier_calculated_shipping_adjustment_t,
                                                           required=False)
    flat_rate_shipping_adjustment           = gxml.Complex('flat-rate-shipping-adjustment',
                                                           shipping_adjustment_t,
                                                           required=False)
    merchant_calculated_shipping_adjustment = gxml.Complex('merchant-calculated-shipping-adjustment',
                                                           shipping_adjustment_t,
                                                           required=False)
    pickup_shipping_adjustment              = gxml.Complex('pickup-shipping-adjustment',
                                                           shipping_adjustment_t,
                                                           required=False)
    methods                                 = gxml.List('', gxml.String('method/@name'))

class shipping_in_calculate_t(gxml.Node):
    methods                                 = gxml.List('', gxml.String('method/@name'))

class order_adjustment_t(gxml.Node):
    adjustment_total                = gxml.Complex('adjustment-total', price_t, required=False)
    merchant_calculation_successful = gxml.Boolean('merchant-calculation-successful', required=False)
    merchant_codes                  = gxml.Complex('merchant-codes', merchant_codes_t, required=False)
    shipping                        = gxml.Complex('shipping', shipping_in_order_adjustment_t, required=False)
    total_tax                       = gxml.Complex('total-tax', price_t, required=False)

class structured_name_t(gxml.Node):
    first_name = gxml.String('first-name')
    last_name  = gxml.String('last-name')

class address_t(gxml.Node):
    address1     = gxml.String('address1')
    address2     = gxml.String('address2', required=False)
    city         = gxml.String('city')
    company_name = gxml.String('company-name', required=False)
    contact_name = gxml.String('contact-name', required=False)
    country_code = gxml.String('country-code')
    email        = gxml.Email('email', required=False)
    fax          = gxml.Phone('fax', required=False, empty=True)
    phone        = gxml.Phone('phone', required=False, empty=True)
    postal_code  = gxml.Zip('postal-code')
    region       = gxml.String('region', empty=True)
    structured_name = gxml.Complex('structured-name',
                                   structured_name_t, required=False)

class buyer_billing_address_t(address_t):
    pass
class buyer_shipping_address_t(address_t):
    pass
class billing_address_t(address_t):
    # google docs do not say address_id is optional, but sandbox omits it.. :S bug?
    # address_id = gxml.ID('@address-id', required=False)
    pass

class buyer_marketing_preferences_t(gxml.Node):
    email_allowed = gxml.Boolean('email-allowed')
    def read(self, node):
        return gxml.Node.read(self, node)
class abstract_notification_t(gxml.Document):
    tag_name = '-notification'
    serial_number       = gxml.ID('@serial-number')
    google_order_number = gxml.ID('google-order-number')
    timestamp                   = gxml.Timestamp('timestamp')

class promotion_t(gxml.Node):
    description  = gxml.String('description', required=False, max_length=1024)
    id           = gxml.Long('id')
    name         = gxml.String('name')
    total_amount = gxml.Complex('total-amount', price_t)

FINANCIAL_ORDER_STATE=('REVIEWING', 'CHARGEABLE', 'CHARGING', 'CHARGED', 'PAYMENT_DECLINED', 'CANCELLED', 'CANCELLED_BY_GOOGLE')
FULFILLMENT_ORDER_STATE=('NEW', 'PROCESSING', 'DELIVERED', 'WILL_NOT_DELIVER')

class new_order_notification_t(abstract_notification_t):
    tag_name = 'new-order-notification'
    buyer_billing_address       = gxml.Complex('buyer-billing-address', buyer_billing_address_t)
    buyer_id                    = gxml.Long('buyer-id')
    buyer_marketing_preferences = gxml.Complex('buyer-marketing-preferences', buyer_marketing_preferences_t)
    buyer_shipping_address      = gxml.Complex('buyer-shipping-address', buyer_shipping_address_t)
    financial_order_state       = gxml.String('financial-order-state', values=FINANCIAL_ORDER_STATE)
    fulfillment_order_state     = gxml.String('fulfillment-order-state', values=FULFILLMENT_ORDER_STATE)
    order_adjustment            = gxml.Complex('order-adjustment', order_adjustment_t)
    order_total                 = gxml.Complex('order-total', price_t)
    shopping_cart               = gxml.Complex('shopping-cart', shopping_cart_t)
    promotions                  = gxml.List('promotions',
                                            gxml.Complex('promotion', promotion_t),
                                            required=False)

class checkout_redirect_t(gxml.Document):
    """
    Try doctests:
    >>> a = checkout_redirect_t(serial_number='blabla12345',
    ...                         redirect_url='http://www.somewhere.com')
    >>> b = gxml.Document.fromxml(a.toxml())
    >>> a == b
    True
    """
    tag_name = 'checkout-redirect'
    serial_number = gxml.ID('@serial-number')
    redirect_url  = gxml.Url('redirect-url')

class notification_acknowledgment_t(gxml.Document):
    tag_name      = 'notification-acknowledgment'
    serial_number = gxml.ID('@serial-number')

class order_state_change_notification_t(abstract_notification_t):
    tag_name = 'order-state-change-notification'
    new_fulfillment_order_state      = gxml.String('new-fulfillment-order-state', values=FINANCIAL_ORDER_STATE)
    new_financial_order_state        = gxml.String('new-financial-order-state', values=FULFILLMENT_ORDER_STATE)
    previous_financial_order_state   = gxml.String('previous-financial-order-state', values=FINANCIAL_ORDER_STATE)
    previous_fulfillment_order_state = gxml.String('previous-fulfillment-order-state', values=FULFILLMENT_ORDER_STATE)
    reason                           = gxml.String('reason', required=False)

AVS_VALUES=('Y', 'P', 'A', 'N', 'U')
CVN_VALUES=('M', 'N', 'U', 'E')

class risk_information_t(gxml.Node):
    avs_response            = gxml.String('avs-response', values=AVS_VALUES)
    billing_address         = gxml.Complex('billing-address', billing_address_t)
    buyer_account_age       = gxml.Integer('buyer-account-age')
    cvn_response            = gxml.String('cvn-response', values=CVN_VALUES)
    eligible_for_protection = gxml.Boolean('eligible-for-protection')
    ip_address              = gxml.IP('ip-address')
    partial_cc_number       = gxml.String('partial-cc-number') # partial CC Number

class risk_information_notification_t(abstract_notification_t):
    tag_name = 'risk-information-notification'
    risk_information = gxml.Complex('risk-information', risk_information_t)

class abstract_order_t(gxml.Document):
    tag_name='-order'
    google_order_number = gxml.ID('@google-order-number')

class charge_order_t(abstract_order_t):
    tag_name = 'charge-order'
    amount = gxml.Complex('amount', price_t, required=False)

class refund_order_t(abstract_order_t):
    tag_name = 'refund-order'
    amount  = gxml.Complex('amount', price_t, required=False)
    comment = gxml.String('comment', max_length=140, required=False)
    reason  = gxml.String('reason', max_length=140)

class cancel_order_t(abstract_order_t):
    """
    Represents an order that should be canceled. A <cancel-order> command
    sets the financial-order-state and the fulfillment-order-state to canceled.

    >>> test_document(
    ...     cancel_order_t(google_order_number = "841171949013218",
    ...                    comment = 'Buyer found a better deal.',
    ...                    reason = 'Buyer cancelled the order.'
    ...     )
    ... ,
    ...     '''
    ...     <cancel-order xmlns="http://checkout.google.com/schema/2" google-order-number="841171949013218">
    ...       <comment>Buyer found a better deal.</comment>
    ...       <reason>Buyer cancelled the order.</reason>
    ...     </cancel-order>
    ...     '''
    ... )
    """
    tag_name = 'cancel-order'
    comment = gxml.String('comment', max_length=140, required=False)
    reason  = gxml.String('reason', max_length=140)

class authorize_order_t(abstract_order_t):
    tag_name = 'authorize-order'

class process_order_t(abstract_order_t):
    tag_name = 'process-order'

class add_merchant_order_number_t(abstract_order_t):
    tag_name = 'add-merchant-order-number'
    merchant_order_number = gxml.String('merchant-order-number')

CARRIER_VALUES=('DHL', 'FedEx', 'UPS', 'USPS', 'Other')

class tracking_data_t(gxml.Node):
    carrier         = gxml.String('carrier', values=CARRIER_VALUES)
    tracking_number = gxml.String('tracking-number')

class deliver_order_t(abstract_order_t):
    tag_name='deliver-order'
    tracking_data = gxml.Complex('tracking-data', tracking_data_t, required=False)
    send_email    = gxml.Boolean('send-email', required=False)

class add_tracking_data_t(abstract_order_t):
    """
    Represents a tag containing a request to add a shipper's tracking number
    to an order.

    >>> test_document(
    ...     add_tracking_data_t(
    ...         google_order_number = '841171949013218',
    ...         tracking_data = tracking_data_t(
    ...             carrier = 'UPS',
    ...             tracking_number = 'Z9842W69871281267'
    ...         )
    ...     )
    ... ,
    ...     '''
    ...     <add-tracking-data xmlns="http://checkout.google.com/schema/2"
    ...                        google-order-number="841171949013218">
    ...       <tracking-data>
    ...         <tracking-number>Z9842W69871281267</tracking-number>
    ...         <carrier>UPS</carrier>
    ...       </tracking-data>
    ...     </add-tracking-data>
    ...     '''
    ... )
    """
    tag_name='add-tracking-data'
    tracking_data = gxml.Complex('tracking-data', tracking_data_t)

class send_buyer_message_t(abstract_order_t):
    tag_name='send-buyer-message'
    send_email = gxml.Boolean('send-email', required=False)
    message    = gxml.String('message')

class archive_order_t(abstract_order_t):
    """
    Represents a request to archive a particular order. You would archive
    an order to remove it from your Merchant Center Inbox, indicating that
    the order has been delivered.

    >>> test_document(archive_order_t(google_order_number = '841171949013218'),
    ...     '''<archive-order xmlns="http://checkout.google.com/schema/2"
    ...                       google-order-number="841171949013218" />'''
    ... )
    """
    tag_name='archive-order'

class unarchive_order_t(abstract_order_t):
    tag_name='unarchive-order'

class charge_amount_notification_t(abstract_notification_t):
    """
    Represents information about a successful charge for an order.

    >>> from datetime import datetime
    >>> import iso8601
    >>> test_document(
    ...     charge_amount_notification_t(
    ...         serial_number='95d44287-12b1-4722-bc56-cfaa73f4c0d1',
    ...         google_order_number = '841171949013218',
    ...         timestamp = iso8601.parse_date('2006-03-18T18:25:31.593Z'),
    ...         latest_charge_amount = price_t(currency='USD', value=2226.06),
    ...         total_charge_amount = price_t(currency='USD', value=2226.06)
    ...     )
    ... ,
    ...     '''
    ...     <charge-amount-notification xmlns="http://checkout.google.com/schema/2" serial-number="95d44287-12b1-4722-bc56-cfaa73f4c0d1">
    ...       <latest-charge-amount currency="USD">2226.060</latest-charge-amount>
    ...       <google-order-number>841171949013218</google-order-number>
    ...       <total-charge-amount currency="USD">2226.060</total-charge-amount>
    ...       <timestamp>2006-03-18T18:25:31.593000+00:00</timestamp>
    ...     </charge-amount-notification>
    ...     '''
    ... )
    """
    tag_name='charge-amount-notification'
    latest_charge_amount = gxml.Complex('latest-charge-amount',
                                        price_t)
    latest_promotion_charge_amount = gxml.Complex('latest-promotion-charge-amount',
                                                  price_t, required=False)
    total_charge_amount  = gxml.Complex('total-charge-amount', price_t)

class refund_amount_notification_t(abstract_notification_t):
    tag_name='refund-amount-notification'
    latest_refund_amount = gxml.Complex('latest-refund-amount', price_t)
    latest_promotion_refund_amount = gxml.Complex('latest-promotion-refund-amount',
                                                  price_t, required=False)
    total_refund_amount  = gxml.Complex('total-refund-amount', price_t)

class chargeback_amount_notification_t(abstract_notification_t):
    tag_name='chargeback-amount-notification'
    latest_chargeback_amount = gxml.Complex('latest-chargeback-amount', price_t)
    latest_promotion_chargeback_amount = gxml.Complex('latest-promotion-chargeback-amount',
                                                      price_t, required=False)
    total_chargeback_amount  = gxml.Complex('total-chargeback-amount', price_t)

class authorization_amount_notification_t(abstract_notification_t):
    tag_name='authorization-amount-notification'
    authorization_amount          = gxml.Complex('authorization-amount', price_t)
    authorization_expiration_date = gxml.Timestamp('authorization-expiration-date')
    avs_response                  = gxml.String('avs-response', values=AVS_VALUES)
    cvn_response                  = gxml.String('cvn-response', values=CVN_VALUES)

class anonymous_address_t(gxml.Node):
    id           = gxml.String('@id')
    city         = gxml.String('city')
    region       = gxml.String('region', empty=True)
    postal_code  = gxml.Zip('postal-code')
    country_code = gxml.String('country-code')

class merchant_code_string_t(gxml.Node):
    code = gxml.String('@code')

class calculate_t(gxml.Node):
    addresses             = gxml.List('addresses',
                                      gxml.Complex('anonymous-address', anonymous_address_t),
                                      required=False)
    merchant_code_strings = gxml.Complex('merchant-code-strings/merchant-code-string',
                                         merchant_code_string_t,
                                         required=False)
    shipping              = gxml.Complex('shipping', shipping_in_calculate_t, required=False)
    tax                   = gxml.Boolean('tax')

class merchant_calculation_callback_t(gxml.Document):
    tag_name = 'merchant-calculation-callback'
    serial_number    = gxml.ID('@serial-number')
    buyer_id         = gxml.Long('buyer-id', required=False)
    buyer_language   = gxml.LanguageCode('buyer-language')
    calculate        = gxml.Complex('calculate', calculate_t)
    shopping_cart    = gxml.Complex('shopping-cart', shopping_cart_t)

class discount_result_t(gxml.Node):
    valid             = gxml.Boolean('valid')
    calculated_amount = gxml.Complex('calculated-amount', price_t)
    code              = gxml.String('code')
    message           = gxml.String('message', max_length=255)

class merchant_code_results_t(gxml.Node):
    coupon_result           = gxml.List('', gxml.Complex('coupon-result', discount_result_t))
    gift_certificate_result = gxml.List('', gxml.Complex('gift-certificate-result', discount_result_t))

class result_t(gxml.Node):
    shipping_name         = gxml.String('@shipping-name')
    address_id            = gxml.String('@address-id')
    total_tax             = gxml.Complex('total-tax', price_t, required=False)
    shipping_rate         = gxml.Complex('shipping-rate', price_t, required=False)
    shippable             = gxml.Boolean('shippable', required=False)
    merchant_code_results = gxml.Complex('merchant-code-results',
                                         merchant_code_results_t,
                                         required=False)

class merchant_calculation_results_t(gxml.Document):
    tag_name = 'merchant-calculation-results'
    results = gxml.List('results', gxml.Complex('result', result_t))

class request_received_t(gxml.Document):
    tag_name = 'request-received'
    serial_number = gxml.ID('@serial-number')

# This is custom message type which is only suitable for returning to google
# the 'Ok' response.
class ok_t(gxml.Document):
    tag_name = 'ok'

class error_t(gxml.Document):
    """
    Represents a response containing information about an invalid API request.
    The information is intended to help you debug the problem causing the error.

    >>> test_document(
    ...     error_t(serial_number = '3c394432-8270-411b-9239-98c2c499f87f',
    ...             error_message='Bad username and/or password for API Access.',
    ...             warning_messages = ['IP address is suspicious.',
    ...                                 'MAC address is shadowed.']
    ...     )
    ... ,
    ... '''
    ... <error xmlns="http://checkout.google.com/schema/2" serial-number="3c394432-8270-411b-9239-98c2c499f87f">
    ...   <error-message>Bad username and/or password for API Access.</error-message>
    ...   <warning-messages>
    ...     <string>IP address is suspicious.</string>
    ...     <string>MAC address is shadowed.</string>
    ...   </warning-messages>
    ... </error>
    ... '''
    ... )
    """
    tag_name = 'error'
    serial_number    = gxml.ID('@serial-number')
    error_message    = gxml.String('error-message')
    warning_messages = gxml.List('warning-messages',
                                 gxml.String('string'),
                                 required=False)

class diagnosis_t(gxml.Document):
    """
    Represents a diagnostic response to an API request. The diagnostic
    response contains the parsed XML in your request as well as any warnings
    generated by your request.
    Please see the U{Validating XML Messages to Google Checkout
    <http://code.google.com/apis/checkout/developer/index.html#validating_xml_messages>}
    section for more information about diagnostic requests and responses.
    """
    tag_name      = 'diagnosis'
    input_xml     = gxml.Any('input-xml')
    warnings      = gxml.List('warnings',
                              gxml.String('string'),
                              required=False)
    serial_number = gxml.ID('@serial-number')

class demo_failure_t(gxml.Document):
    """
    >>> test_document(
    ...     demo_failure_t(message='Demo Failure Message')
    ... ,
    ...     '''<demo-failure xmlns="http://checkout.google.com/schema/2"
    ...                      message="Demo Failure Message" />'''
    ... )
    """
    tag_name = 'demo-failure'
    message = gxml.String('@message', max_length=25)

class item_id_t(gxml.Node):
    merchant_item_id = gxml.String('merchant-item-id')

class backorder_items_t(abstract_order_t):
    tag_name   = 'backorder-items'
    item_ids   = gxml.List('item-ids', gxml.Complex('item-id', item_id_t))
    send_email = gxml.Boolean('send-email', required=False)

class cancel_items_t(abstract_order_t):
    tag_name = 'cancel-items'
    reason = gxml.String('comment')
    comment = gxml.String('comment')
    item_ids   = gxml.List('item-ids', gxml.Complex('item-id', item_id_t))
    send_email = gxml.Boolean('send-email', required=False)

class reset_items_shipping_information_t(abstract_order_t):
    tag_name   = 'reset-items-shipping-information'
    item_ids   = gxml.List('item-ids', gxml.Complex('item-id', item_id_t))
    send_email = gxml.Boolean('send-email', required=False)

class return_items_t(abstract_order_t):
    tag_name   = 'return-items'
    item_ids   = gxml.List('item-ids', gxml.Complex('item-id', item_id_t))
    send_email = gxml.Boolean('send-email', required=False)

class item_shipping_information_t(gxml.Node):
    item_id = gxml.Complex('item-id', item_id_t)
    tracking_data_list = gxml.List('tracking-data-list',
                                   gxml.Complex('tracking-data', tracking_data_t))

class ship_items_t(abstract_order_t):
    tag_name   = 'ship-items'
    item_shipping_information_list = gxml.List('item-shipping-information-list',
                                               gxml.Complex('item-shipping-information',
                                                            item_shipping_information_t))
    send_email = gxml.Boolean('send-email')

if __name__ == "__main__":
    def run_doctests():
        import doctest
        doctest.testmod()
    run_doctests()
