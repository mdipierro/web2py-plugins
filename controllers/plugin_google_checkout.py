exec("""
import %(path)s.gchecky.model as gmodel
import %(path)s.gchecky.controller as gcontroller
""" % dict(path='applications.'+request.application+'.modules.plugin_google_checkout'))

class Level2Controller(gcontroller.Controller):
    """
    The custom Controller that inherits from gchecky.controller.Controller.
    It implements the required abstract methods.

    Basically it logs all the conversations between our server and GC, and
    also automatically charges new orders. Nothing fancy.
    """
    def __init__(self, automatically_charge=True, *args, **kwargs):
        """
        For the sake of the Demo we add a parameter automatically_charge
        that indicates whether or not the controller should send
        a charge command to google checkout.
        If in your Google Checkout account settings you choose
         "Automatically authorize and *charge* the buyer's credit card"
        then it would be an error to send a 'charge' command to google servers.
        """
        self.automatically_charge = automatically_charge
        return gcontroller.Controller.__init__(self, *args, **kwargs)


    def handle_new_order(self, message, order_id, order, context):
        """
        Create a new Order instance in the database if everything is ok.
        """
        # First verify the currency
        if message.order_total.currency != plugin_google_checkout.CURRENCY:
            raise Exception("Currency mismatch! %s != %s" % (
                             message.order_total.currency,
                             plugin_google_checkout.CURRENCY
                             ))
        # Check if the order already exist in the database
        if order is not None:
            raise Exception("Order with google_id('%s') already exists" % \
                                (order_id,))

        merchant_data = message.shopping_cart.merchant_private_data
        nature = 'unknown'

        # Good to create a fresh new order in DB
        if message.buyer_billing_address.contact_name is not None:
            owner_id = message.buyer_billing_address.contact_name
        elif message.buyer_billing_address.company_name is not None:
            owner_id = message.buyer_billing_address.company_name
        else:
            owner_id = message.buyer_id
        db.plugin_google_checkout_order.insert(
            user_id   = owner_id,
            nature    = nature,
            order_id  = order_id,  # this is the google_order_id (automatic)
            cart_xml  = message.toxml(),
            state     = message.fulfillment_order_state,
            payment   = message.financial_order_state,
            currency  = message.order_total.currency,
            total     = message.order_total.value)

        # parse cart items
        cart_id = str(item.merchant_private_item_data)
        db(db.plugin_google_checkout_purchase.cart_id==cart_id) \
            (db.plugin_google_checkout_purchase.ordered==False).update(
            orderd      = True,
            order_id    = order_id,
            item_xml    = 'TODO')
        return gmodel.ok_t()

    def handle_order_state_change(self, message, order_id, order, context):
        """
        React to the order state change.
        """
        assert order is not None
        (state, payment) = (order.state, order.payment)
        if message.new_fulfillment_order_state != \
                message.previous_financial_order_state:
            state = message.new_fulfillment_order_state
        if message.new_financial_order_state != \
                message.previous_financial_order_state:
            payment = message.new_financial_order_state
        order.update_record(state=state, payment=payment)

        if state == 'NEW':
            if payment == 'CHARGEABLE':
                if order.total > order.charges_pending:
                    if self.automatically_charge:
                        # Only send charge command if your account does not
                        # tell google to do it automatically.
                        amount = order.total - (order.charges + order.charges_pending)
                        order.update_record(charge_pending=order.charge_pending+amount)
                        self.charge_order(order_id, amount)
        return gmodel.ok_t()

    def handle_charge_amount(self, message, order_id, order, context):
        """
        GC has charged this order -- great! Save it.
        """
        assert order is not None

        charges = float(order.charges) + message.latest_charge_amount.value
        if charges != message.total_charge_amount.value:
            raise AssertionError, 'Total charged amount does not match!'
        order.update_record(charges=charges)
        if charges == order.total:
            if order.state == 'NEW':
                # process order
                order.update_record(state='PROCESSING')
                self.process_order(order_id)
                self.deliver_order(order.order_id,
                                   carrier=None,
                                   tracking_number=None,
                                   send_email=True)
                order.update_record(state='DEVIVERED')
        return gmodel.ok_t()

    def handle_chargeback_amount(self, message, order_id, order, context):
        """
        Hmm, what should this do?
        """
        pass

    def handle_notification(self, message, order_id, order, context):
        """
        Handle the rest of the messages.
        This Demostrates that it is not neccessary to override specific
        handlers -- everything could be done inside this one handler.
        """
        assert order is not None

        if message.__class__ == gmodel.authorization_amount_notification_t:
            order.authorized += message.authorization_amount.value

        elif message.__class__ == gmodel.risk_information_notification_t:
            # do nothing -- ignore the message (but process it)
            return gmodel.ok_t()

        elif message.__class__ == gmodel.refund_amount_notification_t:
            order.refunds += message.latest_refund_amount.value
            if order.refunds != message.total_refund_amount.value:
                raise AssertionError('Total refunded amount does not match!')

        elif message.__class__ == gmodel.chargeback_amount_notification_t:
            order.chargebacks += message.latest_chargeback_amount.value
            if order.chargebacks != message.total_chargeback_amount.value:
                raise AssertionError('Total chargeback amount does not match!')

        else:
            # unknown message - return None to indicate that we can't process it
            return None

        order.save()

        return gmodel.ok_t()

    def on_exception(self, context, exception):
        """
        Lets log any exception occured in gchecky. Also save the sxception
        type and a brief explanation.
        """
        try:
            raise exception
        except gcontroller.LibraryError, e:
            tag = 'gchecky'
            error = 'Gchecky bug'
        except gcontroller.SystemError, e:
            tag = 'system'
            error = 'System failure'
        except gcontroller.HandlerError, e:
            tag = 'handler'
            error = 'Error in user handler method'
        except gcontroller.DataError, e:
            tag = 'data'
            error = 'Error converting data to/from XML'
        except:
            # Should never happen...
            tag = 'unknown'
            error = 'Unknown error'

        description = "%s:\n%s\n\nOriginal Error:\n%s\n%s" % (error,
                                                              exception,
                                                              exception.origin,
                                                              exception.traceback)
        # TODO: exception trace
        self.__log(context=context, tag=tag, error=error, description=description)
        return "%s\n\n%s" % (error, description)

    def on_xml_sent(self, context):
        """
        Log all the messages we've successfully sent to GC.
        """
        self.__log(context=context, tag='to')

    def on_xml_received(self, context):
        """
        Log all the messages we've successfully received from GC.
        """
        self.__log(context=context, tag='from')

    def __log(self, context, tag, error=None, description=None):
        """
        Helper method that logs everything into DB. It stores successfull
        transaction and errors in the same way, so that it would be easy
        to display it later.
        """
        db.plugin_google_checkout_message.insert(
            order_id    = context.order_id,
            serial      = context.serial,
            tag         = tag,
            input_xml   = context.xml,
            output_xml  = context.response_xml,
            error       = error,
            description = description)

l2controller=Level2Controller(
    plugin_google_checkout.AUTO_CHARGE,
    plugin_google_checkout.MERCHANT_ID,
    plugin_google_checkout.MERCHANT_KEY,
    plugin_google_checkout.IS_SANDBOX,
    plugin_google_checkout.CURRENCY,
)

def button():
    next = request.vars.next
    cart_id = session.plugin_google_checkout.cart_id
    if not cart_id: raise HTTP(404)
    currency = plugin_google_checkout.CURRENCY
    payment=gmodel.checkout_shopping_cart_t()
    payment.shopping_cart=gmodel.shopping_cart_t(
        items=[],
        merchant_private_data=cart_id)
    rows = db(db.plugin_google_checkout_purchase.cart_id==cart_id)\
        (db.plugin_google_checkout_purchase.ordered==False).select()
    for row in rows:
        payment.shopping_cart.items.append(
            gmodel.item_t(
                merchant_item_id = row.item_id,
                name             = row.name,
                description      = row.description,
                unit_price       = gmodel.price_t(value=row.unit_price,
                                                  currency=currency),
                quantity         = row.quantity))
    payment.checkout_flow_support = gmodel.checkout_flow_support_t(
        edit_cart_url = None,
        continue_shopping_url = next,
        tax_tables = gmodel.tax_tables_t(
            merchant_calculated = (plugin_google_checkout.TAX_RATE!=None),
            default = gmodel.default_tax_table_t(
                tax_rules = [
                    gmodel.default_tax_rule_t(
                        shipping_taxed = True,
                        rate = plugin_google_checkout.TAX_RATE,
                        tax_area = gmodel.tax_area_t(
                            world_area = True
                            )
                        )
                    ]
                )
            )
        )
    payment.checkout_flow_support=gmodel.checkout_flow_support_t(
        continue_shopping_url=next,
        request_buyer_phone_number=False)
    prepared = l2controller.prepare_order(payment)
    return XML(prepared.html())

def notify():
    response.headers['Content-Type']='text/xml'
    return l2controller.receive_xml(request.body.read())
