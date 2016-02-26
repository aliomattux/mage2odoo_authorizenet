from openerp.osv import osv, fields
from pprint import pprint as pp

class MageIntegrator(osv.osv_memory):

    _inherit = 'mage.integrator'




    def process_one_order(self, cr, uid, job, order, storeview, payment_defaults, defaults=False, mappinglines=False):
	"""
	Set the card information on an a sales order
	"""

        sale_order = super(MageIntegrator, self).process_one_order(cr, uid, job, order, \
		storeview, defaults, mappinglines)

	#Authnet method is a flag set on payment method object
	#signaling its a credit card payment from authorize.net
        if sale_order.payment_method and sale_order.payment_method.authnet_method:
	    payment = order.get('payment')
	    if payment and payment['additional_information']:
		card_data = payment['additional_information']

		profile_data = {
				'partner': sale_order.partner_id.id,
				'card_number': card_data['acc_number'],
				'customer_profile_id': card_data['profile_id'],
				'customer_id': card_data['customer_id'],
				'profile_description': 'Web Token',
				'payment_type': 'creditcard',
				'profile': card_data['payment_id'],
				'card_type': self.get_card_type(card_data['card_type']),
				'expiration_date': payment['cc_exp_year'] + '-' + payment['cc_exp_month'],
		}

	    	sale_order.payment_profile = self.get_or_create_payment_profile(cr, uid, \
			profile_data, sale_order)


		auth_obj = self.pool.get('authorizenet.authorizations')
                vals = {
                        'sale': sale_order.id,
                        'transaction_id': card_data['transaction_id'],
                        'payment_profile': sale_order.payment_profile.id,
			'auth_status': 'capture' if card_data.get('transaction_type') == 'auth_capture' else 'auth',
                        'card_number': card_data['acc_number'],
                        'authorization_code': card_data.get('approval_code') or card_data.get('auth_code'),
                        'amount': card_data['amount'],
                }

                i = auth_obj.create(cr, uid, vals)

#		sale_order.payment_auth_code = card_data.get('approval_code') or card_data.get('auth_code')
#		sale_order.authorization_amount = card_data['amount']
#		sale_order.payment_transaction_id = card_data['transaction_id']
#		sale_order.auth_type = card_data['transaction_type']


	return sale_order


    def get_card_type(self, ctype):
	ref_dict = {
		    'MasterCard': 'mc',
		    'Visa': 'visa',
		    'American Express': 'amex',
		    'Discover': 'disc',
		    'AmericanExpress': 'amex',
	}

	return ref_dict[ctype]


    def get_or_create_payment_profile(self, cr, uid, profile_data, sale):
	profile_obj = self.pool.get('payment.profile')
	partner_obj = self.pool.get('res.partner')

	#If a profile with this id exists return it
	profile_ids = profile_obj.search(cr, uid, [('profile', '=', profile_data['profile'])])
	if profile_ids:
	    return profile_ids[0]

	else:
	    return profile_obj.create(cr, uid, profile_data)

