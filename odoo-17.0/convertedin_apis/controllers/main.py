from odoo import http
from odoo.http import request, Response
from pytz import timezone
from datetime import datetime
from odoo.addons.convertedin_apis.tool.help import my_compute_price
from odoo.addons.convertedin_apis.tool.help import clean_phone_number
import pytz
import json
from PIL import Image
import io
import base64
class ConvertedInAPIController(http.Controller):

    @http.route('/convertedin/storeinfo', type='http', auth='none', methods=['POST'], csrf=False)
    def store_info(self, **kwargs):
        # Extract token from the request
        provided_token = kwargs.get('token')
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')

        # Token verification
        if provided_token != stored_token:
            return request.make_response(json.dumps({
                'code': 403,
                'message': 'Forbidden: Invalid Token'
            }), headers={'Content-Type': 'application/json'})

        # Fetch store information from Odoo
        store = request.env['res.company'].sudo().search([], limit=1)  # Adjust as needed
        if store:
            # Get the current timezone of the server
            current_timezone = timezone(
                request.env['ir.config_parameter'].sudo().get_param('web.base.timezone') or 'UTC')

            store_data = {
                'name': store.name,
                'currency': store.currency_id.name if store.currency_id else None,
                'time_zone': str(current_timezone),
                'email': store.email if store.email else None,
                'description': store.company_details if store.company_details else None,
                'country': store.country_id.name if store.country_id else None,
                'country_code': store.country_id.code if store.country_id else None
            }

        # Respond with the store data
        return request.make_response(json.dumps({
            'code': 200,
            'data': store_data
        }), headers={'Content-Type': 'application/json'})

    @http.route('/convertedin/categories', type='http', auth='none', methods=['POST'], csrf=False)
    def categories_info(self, **kwargs):
        # Extract the parameters from the request
        provided_token = kwargs.get('token')
        per_page = int(kwargs.get('per_page', 10))
        page = int(kwargs.get('page', 1))
        categories_id = kwargs.get('categories_id', None)

        # Retrieve the correct token from Odoo (replace with your logic)
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')

        # Token verification
        if provided_token != stored_token:
            return request.make_response(json.dumps({
                'code': 403,
                'message': 'Forbidden: Invalid Token'
            }), headers={'Content-Type': 'application/json'})

        # Fetch categories information from Odoo (replace with your logic)
        categories = request.env['product.public.category'].sudo()
        categories = categories.search([], limit = per_page, offset=(page - 1) * per_page)
        categories_data = []

        for category in categories:
            base_url = request.httprequest.host_url
            image_data = category.image_1920 and f'{base_url}web/image/product.public.category/{category.id}/image_1920'
            categories_data.append({
                'id': category.id,
                'taxonomy': category.parent_path if category.parent_path else None,
                'handle': category.name if category.name else None,
                'title': category.name if category.name else None,
                'updated_at': category.write_date.isoformat() if category.write_date else None,
                'published_at': category.create_date.isoformat() if category.create_date else None,
                'available': True,
                'image': {
                    'created_at': None,
                    'alt': None,
                    'width': None,
                    'height': None,
                    'src': image_data,
                }if image_data else None
            })

        # Example pagination logic (adjust based on your data)
        #total = len(categories_data)
        total = categories.search_count([])
        start = (page - 1) * per_page
        end = start + per_page
        # paginated_data = categories_data[start:end]

        # Respond with the paginated categories data
        return request.make_response(json.dumps({
            'data': categories_data,
            'total': total,
            'per_page': per_page,
            'current_page': page,
            'last_page': (total // per_page) + (1 if total % per_page > 0 else 0),
            'from': start + 1,
            'to': end if end < total else total
        }), headers={'Content-Type': 'application/json'})


  
    @http.route('/convertedin/products', type='http', auth='public', methods=['POST'], csrf=False)
    def get_products(self, **kwargs):
        token = kwargs.get('token')
        per_page = int(kwargs.get('per_page', 10))
        page = int(kwargs.get('page', 1))
        category_id = kwargs.get('collection_id')

        # stored_token and convertedIn_pricelist_id from system parameters
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')
        pricelist_id = request.env['ir.config_parameter'].sudo().get_param('convertedIn_pricelist_id')

        # The pricelist
        pricelist = request.env['product.pricelist'].sudo().search([('id', '=', pricelist_id)])

        if token != stored_token:
            return json.dumps({'error': 'Invalid token'}), 401

        # Prepare domain for product search
        domain = [('detailed_type', '=', 'product')]
        if category_id:
            domain.append(('public_categ_ids', 'in', [int(category_id)]))

        # Fetch products from Odoo database
        product_obj = request.env['product.product'].sudo()
        products = product_obj.search(domain, limit = per_page , offset=(page - 1) * per_page)

        # Prepare product data
        product_data = []
        for product in products:
            price = my_compute_price(product, pricelist)
            base_url = request.httprequest.host_url
            image_data = product.image_1920 and f'{base_url}web/image/product.product/{product.id}/image_1920'
            full_permalink = f'{request.env["ir.config_parameter"].sudo().get_param("web.base.url")}{product.website_url}'
            category_id = product.public_categ_ids[0].id if product.public_categ_ids else None
            tags = [tag.name for tag in product.product_tag_ids] if product.product_tag_ids else []
            product_data.append({
                'id': product.id,
                'title': product.name if product.name else None,
                'category_id': category_id,
                'image': image_data,
                'type': product.type if product.type else None,
                'vendor': None,
                'handle': product.default_code if product.default_code else None,
                "owner": product.company_id.name or None,
                'compare_at_price': product.lst_price if product.lst_price else None,
                'price': price if price else None,
                'stock_status': 'instock' if product.qty_available > 0 else 'outofstock',
                'quantity': product.qty_available if product.qty_available and product.is_published else 0,
                'published_at': str(product.create_date) if str(product.create_date) and product.is_published else None,
                'tags': tags or None,
                'images': {
                    'path': image_data,
                    'width': None,
                    'height': None,
                } if image_data else None,
                'full_permalink': full_permalink if full_permalink else None,
                'content': product.description_sale if product.description_sale else None,
            })

        # Response data
        total_products = request.env['product.product'].sudo().search_count(domain)
        response_data = {
            'data': product_data,
            'from': (page - 1) * per_page + 1,
            'current_page': page,
            'last_page': (total_products + per_page - 1) // per_page,
            'per_page': per_page,
            'to': page * per_page,
            'total': total_products,
        }

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])


    @http.route('/convertedin/customers', type='http', auth='public', methods=['POST'], csrf=False)
    def customers_data(self, **kwargs):
        token = kwargs.get('token')
        per_page = int(kwargs.get('per_page', 10))
        page = int(kwargs.get('page', 1))

        # Verify token
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')
        if token != stored_token:
            return request.make_response(json.dumps({'error': 'Invalid token'}),
                                         headers=[('Content-Type', 'application/json')], status=401)

        # Fetch customers from Odoo database
        domain = [
            '&', '&', '&',# Logical AND operators
            ('phone_mobile_search', '!=', False),  # Phone or Mobile is not empty or None
            ('customer_rank', '>=', 0),  # Customer rank is greater than or equal to 0
            ('supplier_rank', '<=', 0),  # Supplier rank is less than or equal to 0
            ('employee_ids', '=', False),  # Employee is not assigned
            ('parent_id', '=', False)  # Parent ID is not set
        ]
        customers = request.env['res.partner'].sudo().search(domain, limit=per_page, offset=(page - 1) * per_page)

        # Prepare customer data
        customer_data = []
        for customer in customers:
            phone_number = clean_phone_number(customer.phone) if customer.phone else None
            mobile_number = clean_phone_number(customer.mobile) if customer.mobile else None

            if phone_number and len(phone_number) >= 11:
                id = phone_number
            elif mobile_number and len(mobile_number) >= 11:
                id = mobile_number
            else:
                id = phone_number or mobile_number
            customer_data.append({
                'id': id,
                'email': customer.email,
                'accepts_marketing': False,
                'created_at': customer.create_date.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'updated_at': customer.write_date.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'first_name':  customer.name.split()[0] if customer.name and len(customer.name.split()) > 0 else None,
                'last_name': ' '.join(customer.name.split()[1:]) if customer.name else None,
                'orders_count': customer.sale_order_count,
                'state': customer.state_id.name if customer.state_id else 'unknown',
                'total_spent': customer.total_invoiced,  # customer.debit - customer.credit
                'last_order_id': customer.sale_order_ids[-1].id if customer.sale_order_ids else None,
                'verified_email': customer.email and '@' in customer.email,
                'phone': clean_phone_number(customer.phone) if customer.phone and len(clean_phone_number(customer.phone)) >= 11 else (clean_phone_number(customer.mobile) if customer.mobile and len(clean_phone_number(customer.mobile)) >= 11 else None),
                'last_order_name': customer.sale_order_ids[-1].name if customer.sale_order_ids else None,
                'currency': customer.currency_id.name or None,
                'addresses':
                    [{
                         'id': clean_phone_number(contact.phone) if contact.phone  else clean_phone_number(contact.mobile),
                         'contact_id': clean_phone_number(contact.phone) if contact else clean_phone_number(contact.mobile),
                         'first_name': contact.name.split()[0] if contact.name and len( contact.name.split()) > 0 else None,
                         'last_name': ' '.join(contact.name.split()[1:]) if contact.name else None,
                         'company': contact.commercial_company_name if contact.commercial_company_name else None,
                         'address1': contact.street if contact.street else None,
                         'address2': contact.street2 if contact.street2 else None,
                         'city':  contact.state_id.name if contact.state_id else None,
                         'province': contact.state_id.name if contact.state_id else None,
                         'country': contact.country_id.name if contact.country_id else None,
                         'zip': contact.zip if contact.zip else None,
                         'phone': clean_phone_number(contact.phone) if contact.phone and len(clean_phone_number(contact.phone)) >= 11 else (clean_phone_number(contact.mobile) if contact.mobile and len(clean_phone_number(contact.mobile)) >= 11 else None),
                         'name': contact.name if contact.name else None,
                         'province_code': contact.state_id.code if contact.state_id else None,
                         'country_code': contact.country_id.code if contact.country_id else None,
                         'country_name': contact.country_id.name if contact.country_id else None,
                         'default': False
                    }for contact in customer.child_ids],
                    'default_address':  {
                    'id': id,
                    'customer_id': id,
                    'first_name': customer.name.split()[0] if customer.name and len(customer.name.split()) > 0 else None,
                    'last_name': ' '.join(customer.name.split()[1:]) if customer.name else None,
                    'company': customer.commercial_company_name if customer.commercial_company_name else None,
                    'address1': customer.street if customer.street else None,
                    'address2': customer.street2 if customer.street2 else None,
                    'city': customer.state_id.name if customer.state_id else None,
                    'province': customer.state_id.name if customer.state_id else None,
                    'country': customer.country_id.name if customer.country_id else None,
                    'zip': customer.zip if customer.zip else None,
                    'phone': clean_phone_number(customer.phone) if customer.phone and len(clean_phone_number(customer.phone)) >= 11 else (clean_phone_number(customer.mobile) if customer.mobile and len(clean_phone_number(customer.mobile)) >= 11 else None),
                    'name': customer.name if customer.name else None,
                    'province_code': customer.state_id.code if customer.state_id else None,
                    'country_code': customer.country_id.code if customer.country_id else None,
                    'country_name': customer.country_id.name if customer.country_id else None,
                    'default': True
                }
            })

        # Response data
        total_customers = request.env['res.partner'].sudo().search_count(domain)
        response_data = {
            'data': customer_data,
            'from': (page - 1) * per_page + 1,
            'current_page': page,
            'last_page': (total_customers + per_page - 1) // per_page,
            'per_page': per_page,
            'to': page * per_page,
            'total': total_customers,
        }
        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])
    @http.route('/convertedin/orders', type='http', auth='public', methods=['POST'], csrf=False)
    def get_orders(self, **kwargs):
        token = kwargs.get('token')
        per_page = int(kwargs.get('per_page', 10))
        page = int(kwargs.get('page', 1))

        # Verify token
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')
        if token != stored_token:
            return request.make_response(json.dumps({'error': 'Invalid token'}),
                                         headers=[('Content-Type', 'application/json')], status=401)

        # Fetch orders from Odoo database
        order_obj = request.env['sale.order'].sudo()
        domain = [
            ('state', '=', 'sale')
        ]
        orders = order_obj.search(domain, limit = per_page, offset=(page - 1) * per_page)

        # Prepare order data
        order_data = []
        for order in orders:
            order_data.append({
                'id': order.id,
                'closed_at': None,
                'confirmed': True if order.state == 'sale' or 'locked' else False,
                'contact_email': order.user_id.email or None,
                # 'name': order.name,
                'created_at': str(order.create_date) if order.create_date else None,
                # 'updated_at': str(order.write_date) if order.write_date else None,
                'currency': order.currency_id.name if order.currency_id else None,
                'customer_locale': None,
                'discount_codes':
                [{
                    "code": copoun.code,
                    "amount": copoun.reward_point_amount,
                    "type": None
                } for copoun in order.code_enabled_rule_ids],
                'email': order.user_id.email or None,
                "financial_status": None,
                "fulfillment_status": None,
                "landing_site": None,
                "landing_site_ref": None,
                "name": order.name,
                "note": order.note,
                "number": order.id,
                "order_number": order.id,
                "order_status_url": None,
                "payment_gateway_names": [
                              payment.name for payment in order.payment_term_id
                ],
                "phone": order.user_id.phone,
                "presentment_currency": order.currency_id.name if order.currency_id else None,
                "processed_at": str(order.create_date) if order.create_date else None,
                "processing_method": None,
                "reference": order.reference,
                "referring_site": None,
                "source_identifier": None,
                "source_name": None,
                "source_url": None,
                "subtotal_price": None,
                "tags": [
                              tag.name for tag in order.tag_ids
                ],
                "taxes_included": None,
                "total_discounts": order.reward_amount,
                "total_line_items_price": order.amount_total,
                "total_price": order.amount_total,
                "total_price_usd": None,
                "total_tax": order.tax_totals['amount_total'],
                "total_tip_received": None,
                "total_weight": order.shipping_weight,
                "updated_at": str(order.write_date) if order.write_date else None,
                "billing_address": {
                    "first_name": order.partner_invoice_id.name.split()[0] if order.partner_invoice_id and order.partner_invoice_id.name else None,
                    "address1":  order.partner_invoice_id.street if order.partner_invoice_id else None,
                    "phone": order.partner_invoice_id.phone,
                    "city": order.partner_invoice_id.state_id.name if order.partner_invoice_id and order.partner_invoice_id.state_id else None,
                    "zip":  order.partner_invoice_id.zip,
                    "province": order.partner_invoice_id.state_id.name if order.partner_invoice_id and order.partner_invoice_id.state_id else None,
                    "country": order.partner_invoice_id.country_id.name if order.partner_invoice_id and order.partner_invoice_id.country_id else None,
                    "last_name": ' '.join(order.partner_invoice_id.name.split()[1:]) if order.partner_invoice_id and isinstance(order.partner_invoice_id.name, str) and len(order.partner_invoice_id.name.split()) > 1 else None,
                    "address2": order.partner_invoice_id.street2 if order.partner_invoice_id else None,
                    "company": order.partner_invoice_id.company_id.name if order.partner_invoice_id else None,
                    "latitude": None,
                    "longitude": None,
                    "name": order.partner_invoice_id.name if order.partner_invoice_id else None,
                    "country_code":  order.partner_invoice_id.country_code if order.partner_invoice_id and order.partner_invoice_id.state_id else None,
                    "province_code":  order.partner_invoice_id.state_id.code if order.partner_invoice_id and order.partner_invoice_id.state_id else None
                }if order.partner_invoice_id else None,
                "customer": {
                    "id": clean_phone_number(order.partner_id.phone) if order.partner_id.phone and len(clean_phone_number(order.partner_id.phone)) >= 11 else (clean_phone_number(order.partner_id.mobile) if order.partner_id.mobile and len(clean_phone_number(order.partner_id.mobile)) >= 11 else clean_phone_number(order.partner_id.phone) or clean_phone_number(order.partner_id.mobile)),
                    "email":  order.partner_id.email if order.partner_id else None,
                    "accepts_marketing": False,
                   # "created_at": order.partner_id.create_date.strftime('%Y-%m-%dT%H:%M:%S%z'),                   
                    "created_at": order.partner_id.create_date.strftime('%Y-%m-%dT%H:%M:%S%z') if isinstance(order.partner_id.create_date, datetime) else None,
                    "updated_at":  order.partner_id.write_date.strftime('%Y-%m-%dT%H:%M:%S%z'),
                    "first_name": order.partner_id.name.split()[0] if order.partner_id and order.partner_id.name else None,
                    "last_name": ' '.join(order.partner_id.name.split()[1:]) if order.partner_id and order.partner_id.name else None,
                    "orders_count": order.partner_id.sale_order_count,
                    "state": order.partner_id.state_id.name if order.partner_id.state_id else 'unknown',
                    "total_spent": order.partner_id.total_invoiced,
                    "last_order_id": order.partner_id.sale_order_ids[-1].id if order.partner_id.sale_order_ids else None,
                    "note":  None,
                    "verified_email": order.partner_id.email and '@' in order.partner_id.email,
                    "multipass_identifier": None,
                    "tax_exempt": False,
                    "phone": order.partner_id.phone or None,
                    "tags": None,
                    "last_order_name": order.partner_id.sale_order_ids[-1].id if order.partner_id.sale_order_ids else None,
                    "currency": order.partner_id.currency_id.name or None,
                    "accepts_marketing_updated_at": order.partner_id.create_date.strftime('%Y-%m-%dT%H:%M:%S%z') if isinstance(order.partner_id.create_date, datetime) else None,
                    "marketing_opt_in_level": None,
                    "tax_exemptions": [],
                    "admin_graphql_api_id": None,
                    "default_address": order.partner_id.contact_address_complete
                },

                "line_items": [
                    {
                        "id": line.id,
                        "fulfillable_quantity": line.qty_delivered,
                        "fulfillment_status": None, #line.qty_available_today quantity delivered
                        "name": line.name_short,
                        "price": line.price_unit,
                        "product_exists": line.product_id.free_qty > 0,
                        "product_id": line.product_id.id,
                        "quantity": line.product_uom_qty,
                        "title": line.name_short,
                        "total_discount": line.discount,
                        "variant_id": None,
                        "variant_title": None,
                        "vendor": None
                    }for line in order.order_line
                ]
            })

        # Response data
        total_orders = request.env['sale.order'].sudo().search_count(domain)
        response_data = {
            'data': order_data,
            'from': (page - 1) * per_page + 1,
            'current_page': page,
            'last_page': (total_orders + per_page - 1) // per_page,
            'per_page': per_page,
            'to': page * per_page,
            'total': total_orders,
        }

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

    @http.route('/convertedin/pos_orders', type='http', auth='public', methods=['POST'], csrf=False)
    def get_pos_orders(self, **kwargs):
        # token = request.httprequest.headers.get('Access-Token')
        token = kwargs.get('token')
        if not token:
            return request.make_response(json.dumps({'error': 'Missing token'}),
                                         headers=[('Content-Type', 'application/json')], status=401)
        per_page = int(kwargs.get('per_page', 10))
        page = int(kwargs.get('page', 1))

        # Verify token
        stored_token = request.env['ir.config_parameter'].sudo().get_param('convertedin.api_token')
        if token != stored_token:
            return request.make_response(json.dumps({'error': 'Invalid token'}),
                                         headers=[('Content-Type', 'application/json')], status=401)

        # Fetch POS orders from Odoo database
        order_obj = request.env['pos.order'].sudo()
        domain = []
        orders = order_obj.search(domain, limit = per_page , offset=(page - 1) * per_page)

        # Prepare order data
        order_data = []
        for order in orders:
            order_data.append({
                'id': order.id,
                'closed_at': None,
                'confirmed': True if order.state == 'sale' or 'locked' else False,
                'contact_email': order.partner_id.email if order.partner_id else None,
                # 'name': order.name,
                'created_at': str(order.create_date) if order.create_date else None,
                # 'updated_at': str(order.write_date) if order.write_date else None,
                'currency': order.currency_id.name if order.currency_id else None,
                'customer_locale': None,
                'discount_codes': None,
                    # [{
                    #     "code": copoun.code,
                    #     "amount": copoun.reward_point_amount,
                    #     "type": None
                    # } for copoun in order.code_enabled_rule_ids],
                'email': order.partner_id.email if order.partner_id else None,
                "financial_status": None,
                "fulfillment_status": None,
                "landing_site": None,
                "landing_site_ref": None,
                "name": order.name,
                "note": order.note,
                "number": order.id,
                "order_number": order.id,
                "order_status_url": None,
                "payment_gateway_names": [
                    payment.name for payment in order.payment_ids
                ],
                "phone": order.user_id.phone,
                "presentment_currency": order.currency_id.name if order.currency_id else None,
                "processed_at": str(order.create_date) if order.create_date else None,
                "processing_method": None,
                "reference": order.pos_reference,
                "referring_site": None,
                "source_identifier": None,
                "source_name": None,
                "source_url": None,
                "subtotal_price": None,
                "tags": None,
                #     [
                #     tag.name for tag in order.tag_ids
                # ],
                "taxes_included": None,
                "total_discounts": None,
                "total_line_items_price": order.amount_total,
                "total_price": order.amount_total,
                "total_price_usd": None,
                "total_tax": None,
                "total_tip_received": None,
                "total_weight": None,
                "updated_at": str(order.write_date) if order.write_date else None,
                "billing_address": None,
                # {
                #     "first_name": order.partner_invoice_id.name.split()[0] if order.partner_invoice_id else None,
                #     "address1": order.partner_invoice_id.street if order.partner_invoice_id else None,
                #     "phone": order.partner_invoice_id.phone,
                #     "city": order.partner_invoice_id.city,
                #     "zip": order.partner_invoice_id.zip,
                #     "province": order.partner_invoice_id.state_id.name if order.partner_invoice_id and order.partner_invoice_id.state_id else None,
                #     "country": order.partner_invoice_id.country_id.name if order.partner_invoice_id and order.partner_invoice_id.country_id else None,
                #     "last_name": ' '.join(
                #         order.partner_invoice_id.name.split()[1:]) if order.partner_invoice_id else None,
                #     "address2": order.partner_invoice_id.street2 if order.partner_invoice_id else None,
                #     "company": order.partner_invoice_id.company_id.name if order.partner_invoice_id else None,
                #     "latitude": None,
                #     "longitude": None,
                #     "name": order.partner_invoice_id.name if order.partner_invoice_id else None,
                #     "country_code": order.partner_invoice_id.country_code if order.partner_invoice_id and order.partner_invoice_id.state_id else None,
                #     "province_code": order.partner_invoice_id.state_id.code if order.partner_invoice_id and order.partner_invoice_id.state_id else None
                # } if order.partner_invoice_id else None,
                "customer": {
                    "id": clean_phone_number(order.partner_id.phone) if order.partner_id.phone and len(clean_phone_number(order.partner_id.phone)) >= 11 else (clean_phone_number(order.partner_id.mobile) if order.partner_id.mobile and len(clean_phone_number(order.partner_id.mobile)) >= 11 else clean_phone_number(order.partner_id.phone) or clean_phone_number(order.partner_id.mobile)),                    "email": order.partner_id.email if order.partner_id else None,
                    "accepts_marketing": False,
                    "created_at": order.partner_id.create_date.strftime('%Y-%m-%dT%H:%M:%S%z') if isinstance(order.partner_id.create_date, datetime) else None,
                    "updated_at": order.partner_id.write_date.strftime('%Y-%m-%dT%H:%M:%S%z') if isinstance(order.partner_id.write_date, datetime) else None,
                    "first_name": order.partner_id.name.split()[0] if order.partner_id else None,
                    "last_name": ' '.join(order.partner_id.name.split()[1:]) if order.partner_id else None,
                    "orders_count": order.partner_id.sale_order_count,
                    "state": order.partner_id.state_id.name if order.partner_id.state_id else 'unknown',
                    "total_spent": order.partner_id.total_invoiced,
                    "last_order_id": order.partner_id.sale_order_ids[-1].id if order.partner_id.sale_order_ids else None,
                    "note": None,
                    "verified_email": order.partner_id.email and '@' in order.partner_id.email,
                    "multipass_identifier": None,
                    "tax_exempt": False,
                    "phone": order.partner_id.phone or None,
                    "tags": None,
                    "last_order_name": order.partner_id.sale_order_ids[-1].id if order.partner_id.sale_order_ids else None,
                    "currency": order.partner_id.currency_id.name or None,
                    "accepts_marketing_updated_at": order.partner_id.create_date.strftime('%Y-%m-%dT%H:%M:%S%z') if isinstance(order.partner_id.create_date, datetime) else None,
                    "marketing_opt_in_level": None,
                    "tax_exemptions": [],
                    "admin_graphql_api_id": None,
                    "default_address": order.partner_id.contact_address_complete
                },

                "line_items": None,
                # [
                #     {
                #         "id": line.id,
                #         "fulfillable_quantity": line.id,
                #         "fulfillment_status": line.qty_available_today,  # quantity delivered
                #         "name": line.name,
                #         "price": line.price_unit,
                #         "product_exists": line.product_id.free_qty > 0,
                #         "product_id": line.product_id.id,
                #         "quantity": line.product_uom_qty,
                #         "title": line.name,
                #         "total_discount": line.discount,
                #         "variant_id": None,
                #         "variant_title": None,
                #         "vendor": None
                #     } for line in order.order_line
                # ]
            })

        # Response data
        response_data = {
            'data': order_data,
            'total': order_obj.search_count([]),
            'per_page': per_page,
            'current_page': page,
            'last_page': (order_obj.search_count([]) + per_page - 1) // per_page,
            'from': (page - 1) * per_page + 1,
            'to': page * per_page,

        }

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])
