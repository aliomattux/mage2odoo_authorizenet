from openerp.osv import osv, fields
from pprint import pprint as pp

class MageIntegrator(osv.osv_memory):

    _inherit = 'mage.integrator'




    def process_one_order(self, cr, uid, job, order, storeview, defaults=False, mappinglines=False):
	"""
	Set the card information on an a sales order
	"""

        sale_order = super(MageIntegrator, self).process_one_order(cr, uid, job, order, storeview, defaults, mappinglines)
        if sale_order.payment_method and sale_order.payment_method.authnet_method:
	    payment = order.get('payment')
	    if payment and payment['additional_information']:
		card_data = payment['additional_information']
		profile_data = {
				'partner': sale_order.partner_id.id,
				'card_number': card_data['acc_number'],
				'payment_type': 'creditcard',
				'profile': card_data['payment_id'],
				'card_type': self.get_card_type(card_data['card_type']),
				'expiration_date': payment['cc_exp_year'] + '-' + payment['cc_exp_month'],
		}
	    	sale_order.payment_profile = self.get_or_create_payment_profile(cr, uid, profile_data, card_data['customer_id'], card_data['profile_id'])
		sale_order.payment_auth_code = card_data['approval_code']
		sale_order.authorization_amount = card_data['amount']
		sale_order.payment_transaction_id = card_data['transaction_id']
		sale_order.auth_type = card_data['transaction_type']


	return sale_order



    def get_card_type(self, ctype):
	ref_dict = {
		    'MasterCard': 'mc',
		    'Visa': 'visa',
		    'American Express': 'amex',
		    'Discover': 'disc'
	}

	return ref_dict[ctype]


    def get_or_create_payment_profile(self, cr, uid, profile_data, customer_id, customer_profile_id):
	profile_obj = self.pool.get('payment.profile')
	partner_obj = self.pool.get('res.partner')

	profile_ids = profile_obj.search(cr, uid, [('profile', '=', profile_data['profile'])])
	if profile_ids:
	    return profile_ids[0]


	partner = partner_obj.browse(cr, uid, profile_data['partner'])

	if partner.customer_profile_id and str(partner.customer_profile_id) == customer_profile_id:
	    return profile_obj.create(cr, uid, profile_data)

	elif not partner.customer_profile_id:
	    partner.customer_profile_id = customer_profile_id
	    partner.customer_id = customer_id
	    return profile_obj.create(cr, uid, profile_data)


	else:
	    print 'PROFILE ID', partner.customer_profile_id
	    print 'DATA PROFILE ID', customer_profile_id
	    print type(partner.customer_profile_id)
	    print type(customer_profile_id)
	    print profile_data
	    print 'Customer has profile and it doesnt match whats in Magento'
	    raise



