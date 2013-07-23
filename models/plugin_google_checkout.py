from gluon.storage import Storage
plugin_google_checkout = Storage()
#########################################
plugin_google_checkout.MERCHANT_ID = "926113221087143"
plugin_google_checkout.MERCHANT_KEY = "uYHWPlDy9IHPpnfvZj4nTQ"
plugin_google_checkout.IS_SANDBOX = True
plugin_google_checkout.CURRENCY = 'USD'
plugin_google_checkout.AUTO_CHARGE = True
plugin_google_checkout.TAX_RATE = 7.0
#########################################
if not session.plugin_google_checkout:
    session.plugin_google_checkout=Storage()
    session.plugin_google_checkout.cart_id = None

### how to use from your own controllers
# 1) configure above parameters
# 2) give a unique name to your cart, has to be unique (can be string)
session.plugin_google_checkout.cart_id = 4321
# 3) add stuff to your shopping chart as follow:
# db.plugin_google_checkout_purchase.insert(
#    cart_id = 4321,  # this your cart name
#    item_id = 1234,  # this your id for the item
#    name="Apple",
#    unit_price=2.99,
#    quantity=34)
# 4) in your payment page add the button
# <img src="{{=URL(request.application,'plugin_google_checkout','button',
#   dict(next='http://complete_url_were_to_redirect_after_purchase'))}}" />
# 5) you can check orders in you cart via
#   db(db.plugin_google_checkout_purchase.ordered=True).select()
# and if they are ordered you can check their status
#   order.
###


db.define_table('plugin_google_checkout_order',
                Field('user_id'),
                Field('nature',default='unknown'),
                Field('order_id'),
                Field('cart_xml','text'),
                Field('state'),
                Field('payment'),
                Field('currency'),
                Field('total','double',default=0.0),
                Field('authorized','double',default=0.0),
                Field('charges','double',default=0.0),
                Field('charges_pending','double',default=0.0),
                Field('refunds','double',default=0.0),
                Field('refunds_pending','double',default=0.0),
                Field('chargebacks','double',default=0.0),
                Field('created_by',db.auth_user,
                      default=(auth.user and auth.user.id) or 0),
                Field('created_on','datetime',default=request.now),
                Field('modified_on','datetime',
                      default=request.now,update=request.now))

### order_id is None if order not submitted
db.define_table('plugin_google_checkout_purchase',
                Field('cart_id'),
                Field('ordered','boolean',default=False),
                Field('order_id',default=None),
                Field('item_id'),
                Field('name'),
                Field('description',
                      default=''),
                Field('unit_price','double'),
                Field('quantity','integer'),
                Field('created_by',db.auth_user,
                      default=(auth.user and auth.user.id) or 0),
                Field('created_on','datetime',default=request.now),
                Field('modified_on','datetime',
                      default=request.now,update=request.now))

db.define_table('plugin_google_checkout_message',
                Field('order_id',default=None),
                Field('serial'),
                Field('tag'),
                Field('input_xml','text'),
                Field('output_xml','text'),
                Field('error'),
                Field('description'),
                Field('created_by',
                      db.auth_user,default=(auth.user and auth.user.id) or 0),
                Field('created_on','datetime',default=request.now),
                Field('modified_on','datetime',
                      default=request.now,update=request.now))

"""
db.plugin_google_checkout_purchase.insert(
    cart_id = 4321,  # this your cart name
    item_id = 1234,  # this your id for the item
    name="Apple",
    unit_price=2.99,
    quantity=34)
"""
