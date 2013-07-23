from base64 import b64encode
import gxml
import model as gmodel

class ProcessingException(Exception):
    def __init__(self, message, where=''):
        self.where = where
        return Exception.__init__(self, message)

def html_escape(html):
    """
    A simple helper that escapes '<', '>' and '&' to make sure the text
    is safe to be output directly into html text flow.
    @param html A (unicode or not) string to be escaped from html.

    >>> safe_str = 'Is''n it a text \"with\": some  fancy characters ;-)?!'
    >>> html_escape(safe_str) == safe_str
    True
    >>> html_escape('Omg&, <this> is not &a safe string <to> &htmlize >_<!')
    'Omg&amp;, &lt;this&gt; is not &amp;a safe string &lt;to&gt; &amp;htmlize &gt;_&lt;!'
    """
    if not isinstance(html, basestring):
        # Nore: html should be a string already, so don't bother applying
        # the correct encoding - use the system defaults.
        html = unicode(html)
    return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class html_order(object):
    """
    TODO:
    """
    cart = None
    signature = None
    url = None
    button = None
    xml = None
    def html(self):
        """
        Return the html form containing two required hidden fields
        and the submit button in the form of Google Checkout button image.
        """
        return """
               <form method="post" action="%s">
                   <input type="hidden" name="cart" value="%s" />
                   <input type="hidden" name="signature" value="%s" />
                   <input type="image" src="%s" alt="Google Checkout" /> 
               </form>
               """ % (html_escape(self.url), self.cart, self.signature, html_escape(self.button))

class ControllerLevel_1(object):
    __MERCHANT_BUTTON  = 'MERCHANT_BUTTON'
    __CLIENT_POST_CART = 'CLIENT_POST_CART'
    __SERVER_POST_CART = 'SERVER_POST_CART'
    __ORDER_PROCESSING = 'ORDER_PROCESSING'
    __CLIENT_DONATION  = 'CLIENT_DONATION'
    __SERVER_DONATION  = 'SERVER_DONATION'
    __DONATION_BUTTON  = 'DONATION_BUTTON'
    __SANDBOX_URLS  = {__MERCHANT_BUTTON: 'https://sandbox.google.com/checkout/buttons/checkout.gif?merchant_id=%s&w=160&h=43&style=white&variant=text',
                       __CLIENT_POST_CART:'https://sandbox.google.com/checkout/api/checkout/v2/checkout/Merchant/%s',
                       __SERVER_POST_CART:'https://sandbox.google.com/checkout/api/checkout/v2/merchantCheckout/Merchant/%s',
                       __ORDER_PROCESSING:'https://sandbox.google.com/checkout/api/checkout/v2/request/Merchant/%s',
                       __CLIENT_DONATION: 'https://sandbox.google.com/checkout/api/checkout/v2/checkout/Donations/%s',
                       __SERVER_DONATION: 'https://sandbox.google.com/checkout/api/checkout/v2/merchantCheckout/Donations/%s',
                       __DONATION_BUTTON: 'https://sandbox.google.com/checkout/buttons/donation.gif?merchant_id=%s&w=160&h=43&style=white&variant=text',
                      }
    __PRODUCTION_URLS={__MERCHANT_BUTTON: 'https://checkout.google.com/buttons/checkout.gif?merchant_id=%s&w=160&h=43&style=white&variant=text',
                       __CLIENT_POST_CART:'https://checkout.google.com/api/checkout/v2/checkout/Merchant/%s',
                       __SERVER_POST_CART:'https://checkout.google.com/api/checkout/v2/merchantCheckout/Merchant/%s',
                       __ORDER_PROCESSING:'https://checkout.google.com/api/checkout/v2/request/Merchant/%s',
                       __CLIENT_DONATION: 'https://checkout.google.com/api/checkout/v2/checkout/Donations/%s',
                       __SERVER_DONATION: 'https://checkout.google.com/api/checkout/v2/merchantCheckout/Donations/%s',
                       __DONATION_BUTTON: 'https://checkout.google.com/buttons/donation.gif?merchant_id=%s&w=160&h=43&style=white&variant=text',
                      }
    # Specify all the needed information such as merchant account credentials:
    #   - sandbox or production
    #   - google vendor ID
    #   - google merchant key
    def __init__(self, vendor_id, merchant_key, is_sandbox=True, currency='USD'):
        self.vendor_id = vendor_id
        self.merchant_key = merchant_key
        self.is_sandbox = is_sandbox
        self.currency = currency

    def _get_url(self, tag, diagnose):
        urls = (self.is_sandbox and self.__SANDBOX_URLS
                              ) or self.__PRODUCTION_URLS
        if urls.has_key(tag):
            url = urls[tag]
            if diagnose:
                url += '/diagnose'
            return url
        raise Exception('Unknown url tag "' + tag + '"')

    def get_client_post_cart_url(self, diagnose):
        return self._get_url(self.__CLIENT_POST_CART, diagnose) % (self.vendor_id,)

    def get_server_post_cart_url(self, diagnose):
        return self._get_url(self.__SERVER_POST_CART, diagnose) % (self.vendor_id,)

    def get_checkout_button_url(self, diagnose):
        return self._get_url(self.__MERCHANT_BUTTON, diagnose) % (self.vendor_id,)
    get_cart_post_button = get_checkout_button_url

    def get_order_processing_url(self, diagnose):
        return self._get_url(self.__ORDER_PROCESSING, diagnose) % (self.vendor_id,)

    def get_client_donation_url(self, diagnose):
        return self._get_url(self.__CLIENT_DONATION, diagnose) % (self.vendor_id,)

    def get_server_donation_url(self, diagnose):
        return self._get_url(self.__SERVER_DONATION, diagnose) % (self.vendor_id,)

    def get_donation_button_url(self, diagnose):
        return self._get_url(self.__DONATION_BUTTON, diagnose) % (self.vendor_id,)

    def create_HMAC_SHA_signature(self, xml_text):
        import hmac, sha
        return hmac.new(self.merchant_key, xml_text, sha).digest()

    # Specify order_id to track the order
    # The order_id will be send back to us by google with order verification
    def prepare_order(self, order, order_id=None, diagnose=False):
        cart = order.toxml()

        cart64 = b64encode(cart)
        signature64 = b64encode(self.create_HMAC_SHA_signature(cart))
        html = html_order()
        html.cart = cart64
        html.signature = signature64
        html.url = self.get_client_post_cart_url(diagnose)
        html.button = self.get_checkout_button_url(diagnose)
        html.xml = cart
        return html

    def prepare_donation(self, order, order_id=None, diagnose=False):
        html = self.prepare_order(order, order_id, diagnose)
        html.url = self.get_client_donation_url(diagnose)
        html.button = self.get_donation_button_url(diagnose)
        return html

class ControllerContext(object):
    """
    """
    # Indicates the direction: True => we call GC, False => GC calls us
    outgoing = True
    # The request XML text
    xml = None
    # The request message - one of the classes in gchecky.model module
    message = None
    # Indicates that the message being sent is diagnose message (implies outgoing=True).
    diagnose = False
    # Associated google order number
    order_id = None
    # A serial number assigned by google to this message
    serial = None
    # The response message - one of the classes in gchecky.model module
    response_message = None
    # The response XML text
    response_xml = None

    def __init__(self, outgoing = True):
        self.outgoing = outgoing

class GcheckyError(Exception):
    """
    Base class for exception that could be thrown by gchecky library.
    """
    def __init__(self, message, context, origin=None):
        """
        @param message String message describing the problem. Can't be empty.
        @param context An instance of gchecky.controller.ControllerContext
                       that describes the current request processing context.
                       Can't be None.
        @param origin The original exception that caused this exception
                      to be thrown if any. Could be None.
        """
        self.message = message
        self.context = context
        self.origin = origin
        self.traceback = None
        if origin is not None:
            from traceback import format_exc
            self.traceback = format_exc()

    def __unicode__(self):
        return self.message
    __str__ = __unicode__
    __repr__ = __unicode__

class DataError(GcheckyError):
    """
    An exception of this class occures whenever there is error in converting
    python data to/from xml.
    """
    pass

class HandlerError(GcheckyError):
    """
    An exception of this class occures whenever an exception is thrown
    from user defined handler.
    """
    pass

class SystemError(GcheckyError):
    """
    An exception of this class occures whenever there is a system error, such
    as network being unavailable or DB down.
    """
    pass

class LibraryError(GcheckyError):
    """
    An exception of this class occures whenever there is a bug encountered
    in gchecky library. It represents a bug which should be reported as an issue
    at U{Gchecky issue tracker <http://gchecky.googlecode.com/>}.
    """
    pass

class ControllerLevel_2(ControllerLevel_1):
    def on_xml_sending(self, context):
        """
        This hook is called just before sending xml to GC.

        @param context.xml  The xml message to be sent to GC.
        @param context.url  The exact URL the message is about to be sent.
        @return     Should return nothing, because the return value is ignored.
        """
        pass

    def on_xml_sent(self, context):
        """
        This hook is called right after sending xml to GC.

        @param context.xml  The xml message to be sent to GC.
        @param context.url  The exact URL the message is about to be sent.
        @param context.response_xml The reply xml of GC.
        @return Should return nothing, because the return value is ignored.
        """
        pass

    def on_message_sending(self, context):
        """
        This hook is called just before sending xml to GC.

        @param context.xml  The xml message to be sent to GC.
        @param context.url  The exact URL the message is about to be sent.
        @return     Should return nothing, because the return value is ignored.
        """
        pass

    def on_message_sent(self, context):
        """
        This hook is called right after sending xml to GC.

        @param context.xml The message to be sent to GC (an instance of one
                   of gchecky.model classes).
        @param context.response_xml The reply message of GC.
        @return Should return nothing, because the return value is ignored.
        """
        pass

    def on_xml_receiving(self, context):
        """
        This hook is called just before processing the received xml from GC.

        @param context.xml  The xml message received from GC.
        @return     Should return nothing, because the return value is ignored.
        """
        pass

    def on_xml_received(self, context):
        """
        This hook is called right after processing xml from GC.

        @param context.xml  The xml message received from GC.
        @param context.response_xml The reply xml to GC.
        @return Should return nothing, because the return value is ignored.
        """
        pass

    def on_message_receiving(self, context):
        """
        This hook is called just before processing the received message from GC.

        @param context.message The message received from GC.
        @return     Should return nothing, because the return value is ignored.
        """
        pass

    def on_message_received(self, context):
        """
        This hook is called right after processing message from GC.

        @param context.message The message received from GC.
        @param context.response_message The reply object to GC (either ok_t or error_t).
        @return Should return nothing, because the return value is ignored.
        """
        pass

    def on_retrieve_order(self, order_id, context=None):
        """
        This hook is called from message processing code just before calling
        the corresponding message handler.
        The idea is to allow user code to load order in one place and then
        receive the loaded object as parameter in message handler.
        This method should not throw if order is not found - instead it should
        return None.

        @param order_id The google order number corresponding to the message
                received.
        @return The order object that will be passed to message handlers.
        """
        pass

    def handle_new_order(self, message, order_id, context, order=None):
        """
        Google sends a new order notification when a buyer places an order
        through Google Checkout. Before shipping the items in an order,
        you should wait until you have also received the risk information
        notification for that order as well as the order state change
        notification informing you that the order's financial state
        has been updated to 'CHARGEABLE'.
        """
        pass

    def handle_order_state_change(self, message, order_id, context, order=None):
        pass

    def handle_authorization_amount(self, message, order_id, context, order=None):
        pass

    def handle_risk_information(self, message, order_id, context, order=None):
        """
        Google Checkout sends a risk information notification to provide
        financial information
        that helps you to ensure that an order is not fraudulent.
        """
        pass

    def handle_charge_amount(self, message, order_id, context, order=None):
        pass

    def handle_refund_amount(self, message, order_id, context, order=None):
        pass

    def handle_chargeback_amount(self, message, order_id, context, order=None):
        pass

    def handle_notification(self, message, order_id, context, order=None):
        """
        This handler is called when a message received from GC and when the more
        specific message handler was not found or returned None (which means
        it was not able to process the message).

        @param message The message from GC to be processed.
        @param order_id The google order number for which message is sent.
        @param order The object loaded by on_retrieve_order(order_id) or None.
        @return If message was processed successfully then return gmodel.ok_t().
                If an error occured when proessing, then the method should
                return any other value (not-None).
                If the message is of unknown type or can't be processed by
                this handler then return None.
        """
        # By default return None because we don' handle anything
        pass

    def on_exception(self, exception, context):
        """
        By default simply rethrow the exception ignoring context.
        Could be used for loggin all the processing errors.
        @param exception The exception that was caught, of (sub)type GcheckyError.
        @param context The request context where the exception occured.
        """
        raise exception

    def __call_handler(self, handler_name, context, *args, **kwargs):
        if hasattr(self, handler_name):
            try:
                handler = getattr(self, handler_name)
                return handler(context=context, *args, **kwargs)
            except Exception, e:
                error = "Exception in user handler '%s': %s" % (handler_name, e)
                raise HandlerError(message=error,
                                   context=context,
                                   origin=e)
        error="Unknown user handler: '%s'" % (handler_name,)
        raise HandlerError(message=error, context=context)

    def _send_xml(self, msg, context, diagnose):
        """
        The helper method that submits an xml message to GC.
        """
        context.diagnose = diagnose
        url = self.get_order_processing_url(diagnose)
        context.url = url
        headers={'Authorization':
         'Basic %s'%(b64encode('%s:%s' % (self.vendor_id,self.merchant_key)),),
         'Content-Type':' application/xml; charset=UTF-8',
         'Accept':' application/xml; charset=UTF-8'}
        ### assume this is working on Google App Engine
        try:
            from google.appengine.api import urlfetch
            self.__call_handler('on_xml_sending', context=context)
            response=urlfetch.fetch(url,msg,urlfetch.POST,headers)
            self.__call_handler('on_xml_sent', context=context)
            if response.status_code==200: return response.content
            else: raise urlfetch.Error()
        except urlfetch.Error(), e:
            raise SystemError(message='Error in urlfetch.fetch',context=context,origin=e)
        except ImportError: pass
        ### if not continue using urllib2
        import urllib2
        req = urllib2.Request(url=url, data=msg)
        for item in headers.items():req.add_header(*item)
        try:
            self.__call_handler('on_xml_sending', context=context)
            response = urllib2.urlopen(req).read()
            self.__call_handler('on_xml_sent', context=context)
            return response
        except urllib2.HTTPError, e:
            error = e.fp.read()
            raise SystemError(message='Error in urllib2.urlopen: %s' % (error,),context=context,origin=e)

    def send_message(self, message, context=None, diagnose=False):
        if context is None:
            context = ControllerContext(outgoing=True)
        context.message = message
        context.diagnose = diagnose

        if isinstance(message, gmodel.abstract_order_t):
            context.order_id = message.google_order_number

        try:
            try:
                self.__call_handler('on_message_sending', context=context)
                message_xml = message.toxml()
                context.xml = message_xml
            except Exception, e:
                error = "Error converting message to xml: '%s'" % (unicode(e), )
                raise DataError(message=error, context=context, origin=e)
            response_xml = self._send_xml(message_xml, context=context, diagnose=diagnose)
            context.response_xml = response_xml
    
            response = self.__process_message_result(response_xml, context=context)
            context.response_message = response
    
            self.__call_handler('on_message_sent', context=context)
            return response
        except GcheckyError, e:
            return self.on_exception(exception=e, context=context)

    def __process_message_result(self, response_xml, context):
        try:
            doc = gxml.Document.fromxml(response_xml)
        except Exception, e:
            error = "Error converting message to xml: '%s'" % (unicode(e), )
            raise LibraryError(message=error, context=context, origin=e)

        if context.diagnose:
            # It has to be a 'diagnosis' response, otherwise... omg!.. panic!...
            if doc.__class__ != gmodel.diagnosis_t:
                error = "The response has to be of type diagnosis_t, not '%s'" % (doc.__class__,)
                raise LibraryError(message=error,
                                   context=context)
            return doc

        # If the response is 'ok' or 'bye' just return, because its good
        if doc.__class__ == gmodel.request_received_t:
            return doc

        if doc.__class__ == gmodel.bye_t:
            return doc

        # It's not 'ok' so it has to be 'error', otherwise it's an error
        if doc.__class__ != gmodel.error_t:
            error = "Unknown response type (expected error_t): '%s'" % (doc.__class__,)
            raise LibraryError(message=error, context=context)

        # 'error' - process it by throwing an exception with error/warning text
        msg = 'Error message from GCheckout API:\n%s' % (doc.error_message, )
        if doc.warning_messages:
            tmp = ''
            for warning in doc.warning_messages:
                tmp += '\n%s' % (warning,)
            msg += ('Additional warnings:%s' % (tmp,))
        raise DataError(message=msg, context=context)

    def hello(self):
        context = ControllerContext()
        doc = self.send_message(gmodel.hello_t(), context)
        if isinstance(doc, gxml.Document) and (doc.__class__ != gmodel.bye_t):
            error = "Expected <bye/> but got %s" % (doc.__class__,)
            raise LibraryError(message=error, context=context, origin=e)

    def archive_order(self, order_id):
        self.send_message(
            gmodel.archive_order_t(google_order_number=order_id))

    def unarchive_order(self, order_id):
        self.send_message(
            gmodel.unarchive_order_t(google_order_number=order_id))

    def send_buyer_message(self, order_id, message):
        self.send_message(gmodel.send_buyer_message_t(
            google_order_number = order_id,
            message = message,
            send_email = True
            ))

    def add_merchant_order_number(self, order_id, merchant_order_number):
        self.send_message(gmodel.add_merchant_order_number_t(
            google_order_number = order_id,
            merchant_order_number = merchant_order_number
            ))

    def add_tracking_data(self, order_id, carrier, tracking_number):
        self.send_message(gmodel.add_tracking_data_t(
            google_order_number = order_id,
            tracking_data = gmodel.tracking_data_t(carrier         = carrier,
                                                   tracking_number = tracking_number)
            ))

    def charge_order(self, order_id, amount):
        self.send_message(gmodel.charge_order_t(
            google_order_number = order_id,
            amount = gmodel.price_t(value = amount, currency = self.currency)
            ))

    def refund_order(self, order_id, amount, reason, comment=None):
        self.send_message(gmodel.refund_order_t(
            google_order_number = order_id,
            amount = gmodel.price_t(value = amount, currency = self.currency),
            reason = reason,
            comment = comment or None
            ))

    def authorize_order(self, order_id):
        self.send_message(gmodel.authorize_order_t(
            google_order_number = order_id
        ))

    def cancel_order(self, order_id, reason, comment=None):
        self.send_message(gmodel.cancel_order_t(
            google_order_number = order_id,
            reason = reason,
            comment = comment or None
            ))

    def process_order(self, order_id):
        self.send_message(gmodel.process_order_t(
            google_order_number = order_id
            ))

    def deliver_order(self, order_id,
                      carrier = None, tracking_number = None,
                      send_email = None):
        tracking = None
        if carrier or tracking_number:
            tracking = gmodel.tracking_data_t(carrier         = carrier,
                                              tracking_number = tracking_number)
        self.send_message(gmodel.deliver_order_t(
            google_order_number = order_id,
            tracking_data = tracking,
            send_email = send_email or None
            ))

    # This method gets a string and returns a string
    def receive_xml(self, input_xml, context=None):
        if context is None:
            context = ControllerContext(outgoing=False)
        context.xml = input_xml
        try:
            self.__call_handler('on_xml_receiving', context=context)
            try:
                input = gxml.Document.fromxml(input_xml)
                context.message = input
            except Exception, e:
                error = 'Error reading XML: %s' % (e,)
                raise DataError(message=error, context=context, origin=e)
    
            result = self.receive_message(message=input,
                                          order_id=input.google_order_number,
                                          context=context)
            context.response_message = result
    
            try:
                response_xml = result.toxml()
                context.response_xml = response_xml
            except Exception, e:
                error = 'Error reading XML: %s' % (e,)
                raise DataError(message=error, context=context, origin=e)
            self.__call_handler('on_xml_received', context=context)
            return response_xml
        except GcheckyError, e:
            return self.on_exception(exception=e, context=context)

    # A dictionary of document handler names. Comes handy in receive_message.
    __MESSAGE_HANDLERS = {
        gmodel.new_order_notification_t:            'handle_new_order',
        gmodel.order_state_change_notification_t:   'handle_order_state_change',
        gmodel.authorization_amount_notification_t: 'handle_authorization_amount',
        gmodel.risk_information_notification_t:     'handle_risk_information',
        gmodel.charge_amount_notification_t:        'handle_charge_amount',
        gmodel.refund_amount_notification_t:        'handle_refund_amount',
        gmodel.chargeback_amount_notification_t:    'handle_chargeback_amount',
        }

    def receive_message(self, message, order_id, context):
        context.order_id = order_id
        self.__call_handler('on_message_receiving', context=context)
        # retreive order instance from DB given the google order number
        order = self.__call_handler('on_retrieve_order', context=context, order_id=order_id)

        # handler = None
        result = None
        if self.__MESSAGE_HANDLERS.has_key(message.__class__):
            handler_name = self.__MESSAGE_HANDLERS[message.__class__]
            result = self.__call_handler(handler_name,
                                         message=message,
                                         order_id=order_id,
                                         context=context,
                                         order=order)

        if result is None:
            result = self.__call_handler('handle_notification',
                                         message=message,
                                         order_id=order_id,
                                         context=context,
                                         order=order)

        error = None
        if result is None:
            error = "Notification '%s' was not handled" % (message.__class__,)
        elif not (result.__class__ is gmodel.ok_t):
            try:
                error = unicode(result)
            except Exception, e:
                error = "Invalid value returned by handler '%s': %s" % (handler_name,
                                                                        e)
                raise HandlerError(message=error, context=context, origin=e)

        if error is not None:
            result = gmodel.error_t(serial_number = 'error',
                                    error_message=error)
        else:
            # TODO: Remove this after testing
            assert result.__class__ is gmodel.ok_t

        self.__call_handler('on_message_received', context=context)
        return result

# Just an alias with a shorter name.
Controller = ControllerLevel_2

if __name__ == "__main__":
    def run_doctests():
        import doctest
        doctest.testmod()
    run_doctests()
