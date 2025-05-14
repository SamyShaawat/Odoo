# -*- coding: utf-8 -*-
# ©️ OdooPBX by Odooist, Odoo Proprietary License v1.0, 2020
import inspect
import json
import requests
import logging
import sys
from urllib.parse import urljoin
import uuid
from odoo import fields, models, api, release, _
from odoo.exceptions import ValidationError
from odoo.tools import ormcache

logger = logging.getLogger(__name__)

MAX_EXTEN_LEN = 6
FORMAT_TYPE = 'e164'

############### BILLING SETTINGS #####################################
MODULE_NAME = 'asterisk_plus'
PRODUCT_CODE = 'prod_O75Ft5DaJlzR12'
BILLING_USER = 'asterisk_plus.user_asterisk1'
PREPAID_PAYMENT_URL = 'https://buy.stripe.com/aEU01VaER5D15lC4gj'
# Starting from Odoo 12.0 there is admin user with ID 2.
ADMIN_USER_ID = 1 if release.version_info[0] <= 11 else 2


def debug(rec, message, level='info'):
    caller_module = inspect.stack()[1][3]
    if level == 'info':
        fun = logger.info
    elif level == 'warning':
        fun = logger.warning
        fun('++++++ {}: {}'.format(caller_module, message))
    elif level == 'error':
        fun = logger.error
        fun('++++++ {}: {}'.format(caller_module, message))
    if rec.env['%s.settings' % MODULE_NAME].sudo().get_param('debug_mode'):
        rec.env['%s.debug' % MODULE_NAME].sudo().create({
            'model': str(rec),
            'message': caller_module + ': ' + message,
        })
        if level == 'info':
            fun('++++++ {}: {}'.format(caller_module, message))


def strip_number(number):
    """Strip number formating"""
    pattern = r'[\s\(\)\-\+]'
    return re.sub(pattern, '', number).lstrip('0')


class Settings(models.Model):
    """One record model to keep all settings. The record is created on 
    get_param / set_param methods on 1-st call.
    """
    _name = 'asterisk_plus.settings'
    _description = 'Settings'

    #: Just a friends name for a settings form.
    name = fields.Char(compute='_get_name')
    #: Debug mode
    debug_mode = fields.Boolean()
    #: Save all AMI messages on channels
    permit_ip_addresses = fields.Char(
        string=_('Permit IP address(es)'),
        help=_('Comma separated list of IP addresses permitted to query caller'
               ' ID number, etc. Leave empty to allow all addresses.'))
    originate_context = fields.Char(
        string='Default context',
        default='from-internal', required=True,
        help='Default context to set when creating PBX / Odoo user mapping.')
    originate_timeout = fields.Integer(default=60, required=True)
    # Search numbers by exact or partial match
    number_search_operation = fields.Selection(
        [('=', 'Equal'), ('like', 'Like')],
        default='=', required=True)
    disable_phone_format = fields.Boolean(help='Disable phone number format, e.g. +123456789 => +1 234 56 78')
    # Recording settings
    record_calls = fields.Boolean(
        default=True,
        help=_("If checked, call recording will be enabled"))
    recording_storage = fields.Selection(
        [('db', _('Database')), ('filestore', _('Files'))],
        default='filestore', required=True)
    use_mp3_encoder = fields.Boolean(
        default=True, string=_("Encode to mp3"),
        help=_("If checked, call recordings will be encoded using MP3"))
    mp3_encoder_bitrate = fields.Selection(
        selection=[('16', '16kbps'),
                   ('32', '32kbps'),
                   ('48', '48kbps'),
                   ('64', '64kbps'),
                   ('96', '96kbps'),
                   ('128', '128 kbps')],
        default='64',
        required=False)
    mp3_encoder_quality = fields.Selection(
        selection=[('2', '2-Highest'),
                   ('3', '3'),
                   ('4', '4'),
                   ('5', '5'),
                   ('6', '6'),
                   ('7', '7-Fastest')],
        default='4',
        required=False)
    calls_keep_days = fields.Char(
        string=_('Call History Keep Days'),
        default='365',
        required=True,
        help=_('Calls older then set value will be removed.'))
    recordings_keep_days = fields.Char(
        string=_('Call Recording Keep Days'),
        default='365',
        required=True,
        help=_('Call recordings older then set value will be removed.'))
    auto_reload_calls = fields.Boolean(
        default=True,
        help=_('Automatically refresh active calls view'))
    auto_reload_channels = fields.Boolean(
        help=_('Automatically refresh active channels view'))
    auto_create_partners = fields.Boolean(
        default=False,
        help=_('Automatically create partner record on calls from uknown numbers.'))    
    ############# TRANSCRIPT FIELDS ##############################################
    transcript_calls = fields.Boolean()
    summary_prompt = fields.Char(required=True, default='Summarise this phone call')
    register_summary = fields.Boolean(help='Register summary at partner of reference chat.')
    remove_recording_after_transcript = fields.Boolean()
    #############  BILLING FIELDS   ###############################################
    region = fields.Selection(
        [('eu-central-1', 'Europe')],
        required=True, default='eu-central-1')
    registration_code = fields.Char()
    instance_uid = fields.Char('Instance UID', compute='_get_instance_data')
    api_key = fields.Char('API Key', compute='_get_instance_data')
    api_url = fields.Char('API URL', compute='_get_instance_data')
    product_code = fields.Char(compute='_get_instance_data')
    postpaid_balance = fields.Char(readonly=True)
    prepaid_balance = fields.Char(readonly=True)
    prepaid_payment_url = fields.Char(compute='_get_instance_data')
    is_subscribed = fields.Boolean()
    subscription_pricing = fields.Text('Pricing', readonly=True)
    is_registered = fields.Boolean(compute='_get_instance_data')
    registration_id = fields.Char('Registration Number', compute='_get_instance_data')
    registration_date = fields.Datetime(compute='_get_instance_data')
    module_name = fields.Char(compute='_get_instance_data')
    module_version = fields.Char(compute='_get_instance_data')
    partner_code = fields.Char()
    discount_code = fields.Char()
    show_partner_code = fields.Boolean(default=True)
    show_discount_code = fields.Boolean(default=True)
    show_pricing = fields.Boolean(default=True)
    admin_name = fields.Char(compute='_get_instance_data', inverse='_set_instance_data')
    admin_phone = fields.Char(compute='_get_instance_data', inverse='_set_instance_data')
    admin_email = fields.Char(compute='_get_instance_data', inverse='_set_instance_data')
    company_name = fields.Char(compute='_get_instance_data', inverse='_set_instance_data')
    company_email = fields.Char(compute='_get_instance_data', inverse='_set_instance_data')
    web_base_url = fields.Char('WEB Base URL', 
        compute='_get_instance_data', inverse='_set_instance_data')

    def _get_instance_data(self):
        registration_id = self.env['ir.config_parameter'].get_param('odoopbx.registration_id')
        module = self.env['ir.module.module'].sudo().search([('name', '=', MODULE_NAME)])
        for rec in self:
            rec.prepaid_payment_url = self.env['ir.config_parameter'].get_param(
                'odoopbx.prepaid_payment_url') or PREPAID_PAYMENT_URL
            rec.product_code = self.env['ir.config_parameter'].get_param(
                'odoopbx.{}_product_code'.format(MODULE_NAME)) or PRODUCT_CODE
            rec.module_name = MODULE_NAME
            rec.module_version = module.installed_version[-3:]
            # Generate instance UUID.
            instance_uid = self.env['ir.config_parameter'].get_param('odoopbx.instance_uid')
            if not instance_uid:
                instance_uid = str(uuid.uuid4())
                self.env['ir.config_parameter'].set_param('odoopbx.instance_uid', instance_uid)
            rec.instance_uid = instance_uid
            # Generate registration date.
            registration_date = self.env['ir.config_parameter'].get_param('odoopbx.registration_date')
            if not registration_date:
                registration_date = fields.Datetime.now()
                self.env['ir.config_parameter'].set_param('odoopbx.registration_date', registration_date)
            rec.registration_date = registration_date
            # Adjust API URL to the region
            api_url = self.env['ir.config_parameter'].get_param('odoopbx.api_url')
            region = self.get_param('region')
            rec.api_url = api_url.replace('eu-central-1', region)
            rec.api_key = self.env['ir.config_parameter'].get_param('odoopbx.api_key')
            rec.company_email = self.env.user.company_id.email
            rec.company_name = self.env.user.company_id.name
            rec.registration_id = registration_id
            rec.is_registered = True if registration_id else False
            rec.admin_name = self.env['res.users'].browse(ADMIN_USER_ID).partner_id.name
            rec.admin_email = self.env['res.users'].browse(ADMIN_USER_ID).partner_id.email
            rec.admin_phone = self.env['res.users'].browse(ADMIN_USER_ID).partner_id.phone
            rec.web_base_url = self.env['ir.config_parameter'].get_param('web.base.url')

    def _set_instance_data(self):
        for rec in self:
            if rec.company_email:
                self.env.user.company_id.email = rec.company_email
            if rec.company_name:
                self.env.user.company_id.name = rec.company_name
            if rec.admin_name:
                self.env['res.users'].browse(ADMIN_USER_ID).partner_id.name = rec.admin_name
            if rec.admin_email:
                self.env['res.users'].browse(ADMIN_USER_ID).partner_id.email = rec.admin_email
            if rec.admin_phone:
                self.env['res.users'].browse(ADMIN_USER_ID).partner_id.phone = rec.admin_phone
            if rec.web_base_url:
                self.env['ir.config_parameter'].set_param('web.base.url', rec.web_base_url)

####################################################################################
##### BILLING REGISTRATION ##### NO CHANGES ALLOWED HERE ###########################

    def get_registration_code(self):
        # Send registration code to admin.
        self.registration_code = ''
        if self.get_param('admin_email') == 'admin@example.com':
            raise ValidationError('Please set your real email address, not admin@example.com.')
        url = urljoin(self.get_param('api_url'), 'signup')        
        res = requests.post(url,
            json={
                'email': self.get_param('admin_email'),
                'name': self.get_param('admin_name'),
            },
            headers={'x-instance-uid': self.get_param('instance_uid')}
        )
        if not res.ok:
            raise ValidationError(res.text)
        # Notify works in Odoo starting from 12.0
        if release.version_info[0] >= 12:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Signup",
                    'message': 'Check mail for %s for the registration code!' % self.get_param('admin_email'),
                    'sticky': False,
                    'type': 'info',
                }
            }


    def register_instance(self):
        if self.get_param('api_key'):
            raise ValidationError('This instance is already registered!')
        # Reset billing user password. 
        # This billing account has very limited access (portal) and does not consume Odoo user license.
        # It is used only by our billing system to account resources of this application.
        # Don't change its password manually otherwise your subscription will be interrupted.
        billing_user = self.env.ref(BILLING_USER)
        billing_password = str(uuid.uuid4())
        billing_user.password = billing_password
        self.env.cr.commit()
        company_email = self.get_param('company_email')
        admin_email = self.get_param('admin_email')
        admin_phone = self.get_param('admin_phone')
        if not company_email or not admin_email or not admin_phone:
            raise ValidationError('Please enter all required fields: company email, '
                                  'your email, and your phone!')
        if admin_email == 'admin@example.com' or company_email == 'admin@example.com':
            raise ValidationError('Please set your real email address, not admin@example.com.')
        url = urljoin(self.get_param('api_url'), 'registration')
        res = requests.post(url,
            json={
                'registration_code': self.get_param('registration_code'),
                'name': self.get_param('company_name'),
                'admin_name': self.get_param('admin_name'),
                'admin_email': admin_email,
                'admin_phone': admin_phone,
                'email': company_email,
                'partner_code': self.get_param('partner_code'),
                'product_id': self.get_param('product_code'),
                'odoo_url': self.get_param('web_base_url'),
                'odoo_password': billing_password,
                'odoo_version': release.major_version,
                'odoo_db': self.env.cr.dbname,
                'odoo_uid': billing_user.id,
                'odoo_user': billing_user.login,
                'module_version': self.get_param('module_version'),
                'module_name': MODULE_NAME,
                'region': self.get_param('region'),
            },
            headers={'x-instance-uid': self.get_param('instance_uid')})
        if not res.ok:
            raise ValidationError(res.text)
        data = res.json()
        # The register function must return json data with api_key.
        self.env['ir.config_parameter'].sudo().set_param(
            'odoopbx.api_key', data['api_key'])
        self.env['ir.config_parameter'].sudo().set_param(
            'odoopbx.registration_id', data['registration_id'])
        self.registration_code = ''

    def unregister_instance(self):
        if not self.get_param('api_key'):
            raise ValidationError('This instance is not registered!')
        if self.get_param('is_subscribed'):
            raise ValidationError('Unsubscribe first!')
        api_url = self.get_param('api_url')
        instance_uid = self.get_param('instance_uid') or ''
        api_key = self.get_param('api_key') or ''
        res = requests.delete(urljoin(api_url, 'registration'),
            headers={'x-instance-uid': instance_uid, 'x-api-key': api_key})
        if not res.ok:
            raise ValidationError(res.text)
        self.env['ir.config_parameter'].set_param('odoopbx.api_key', '')
        self.env['ir.config_parameter'].set_param('odoopbx.registration_id', '')
        self.set_param('subscription_pricing', '')

    def billing_session_url_action(self):
        api_url = self.get_param('api_url')
        instance_uid = self.get_param('instance_uid') or ''
        api_key = self.get_param('api_key') or ''
        locale = self.env['res.lang'].search(
            [('code','=', self.env.user.lang)]).iso_code
        res = requests.get(urljoin(api_url, 'customer'),
            json={
                'create_billing_session': True,
                'locale': locale,
            },
            headers={'x-instance-uid': instance_uid, 'x-api-key': api_key})
        if not res.ok:
            raise ValidationError(res.text)
        data = res.json()
        self.set_param('prepaid_balance', data['prepaid_balance'])
        self.set_param('postpaid_balance', data['postpaid_balance'])
        return {
            'type': 'ir.actions.act_url',
            'url': data.get('session_url')
        }

    def check_balance(self):
        api_url = self.get_param('api_url')
        instance_uid = self.get_param('instance_uid') or ''
        api_key = self.get_param('api_key') or ''
        res = requests.get(
            urljoin(api_url, 'customer'),
            headers={'x-instance-uid': instance_uid, 'x-api-key': api_key})
        if not res.ok:
            raise ValidationError(res.json().get('message', 'Server error'))
        data = res.json()
        self.set_param('prepaid_balance', data['prepaid_balance'])
        self.set_param('postpaid_balance', data['postpaid_balance'])
        self.env['%s.settings' % MODULE_NAME].odoopbx_notify(
            title="Balance Updated",
            message='Prepaid balance: {}, postpaid balance: {}'.format(
                data['prepaid_balance'], data['postpaid_balance']))

    def subscribe_product(self, trial=False):
        if self.get_param('is_subscribed'):
            raise ValidationError('Already subscribed')
        api_url = self.get_param('api_url')
        url = urljoin(api_url, 'subscription')
        data = {
                'module_name': self.get_param('module_name'),
                'promotion_code': self.get_param('discount_code'),
                'product_id': self.get_param('product_code'),
            }
        if trial:
            data['is_trial'] = True
        res = requests.post(url,
            json=data,
            headers={
                'x-instance-uid': self.get_param('instance_uid'),
                'x-api-key': self.get_param('api_key')
            })
        if not res.ok:
            # Check if it comes from ref and discount code is wrong.
            if 'Discount code is not valid' in res.text and not self.get_param('show_discount_code'):
                # Yes, it's a ref, so reset discount code and re-subscribe.
                self.set_param('show_discount_code', True)
                self.set_param('show_partner_code', True)
                self.env.cr.commit()
                raise ValidationError('The preset discount code is not valid anymore! Please reload the page to show and remove it!')
            else:
                raise ValidationError(res.text)
        else:
            self.set_param('is_subscribed', True)
            if hasattr(self, 'post_subscribe_product'):
                self.post_subscribe_product()
            return True

    def subscribe_trial_product(self):
        return self.subscribe_product(trial=True)

    def unsubscribe_product(self):
        api_url = self.get_param('api_url')
        url = urljoin(api_url, 'subscription')
        res = requests.delete(url,
            json={
                'module_name': self.get_param('module_name'),
            },
            headers={
                'x-instance-uid': self.get_param('instance_uid') or '',
                'x-api-key': self.get_param('api_key') or ''
            })
        if not res.ok:
            raise ValidationError(res.text)
        else:
            self.set_param('is_subscribed', False)
            # This is checked in the wizard to show the notification dialog.
            return True

    @api.model
    def get_instance_support_data(self):
        return {
            'user_id': 'test',
            'user_hash': 'Test',
            'name': self.env.user.name,
            'email': self.env.user.email,
            'created_at': datetime.strptime(
                self.get_param('registration_date'),
                '%Y-%m-%d %H:%M:%S').timestamp()
        }

    @api.model
    def subscription_cancelled(self):
        if self.env.user.id != self.env.ref(BILLING_USER).id:
            raise ValidationError('Cancelling subscription is not allowed!')
        self.sudo().set_param('is_subscribed', False)
        self.sudo().odoopbx_notify(
            'Your %s subscription is cancelled!' % MODULE_NAME,
            title='OdooPBX Billing',
            notify_uid=2,
            warning=True,
            sticky=True,
        )
        self.sudo().odoopbx_reload_view('%s.settings' % MODULE_NAME)
        return True

    def update_billing_data(self):
        if not self.get_param('is_registered'):
            raise ValidationError('Not registered!')
        # Change also billing user password.
        billing_user = self.env.ref(BILLING_USER)
        billing_password = str(uuid.uuid4())
        billing_user.password = billing_password
        self.env.cr.commit()
        api_url = self.get_param('api_url')
        url = urljoin(api_url, 'registration')
        res = requests.put(url,
            json={
                'name': self.get_param('company_name'),
                'admin_name': self.get_param('admin_name'),
                'admin_email': self.get_param('admin_email'),
                'admin_phone': self.get_param('admin_phone'),
                'email': self.get_param('company_email'),
                'odoo_url': self.get_param('web_base_url'),
                'odoo_password': billing_password,
                'odoo_version': release.major_version,
                'odoo_db': self.env.cr.dbname,
                'module_version': self.get_param('module_version'),
                'odoo_uid': billing_user.id,
                'odoo_user': billing_user.login,
                'module_name': MODULE_NAME,
            },
            headers={
                'x-instance-uid': self.get_param('instance_uid'),
                'x-api-key': self.get_param('api_key')
            })
        if not res.ok:
            raise ValidationError(res.text)
        if hasattr(self, 'post_update_billing_data'):
            self.post_update_billing_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Status",
                'message': 'Billing data updated',
                'sticky': False,
                'type': 'info',
            }
        }

    @api.model
    def set_default_api_url(self):
        # Called on installation to set default value
        api_url = self.get_param('api_url')
        if not api_url:
            # Set default value
            self.env['ir.config_parameter'].set_param(
                'odoopbx.api_url', 'https://api.odoopbx.eu-central-1.odooist.com')

    def update_system_settings(self, data):
        # Used to update billing server
        self.check_access('write')
        if data.get('api_url'):
            self.env['ir.config_parameter'].sudo().set_param('odoopbx.api_url')
        return True

    def update_prepaid_balance(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_param('prepaid_payment_url')
        }

    @api.model
    def odoopbx_notify(self, message, title='PBX', notify_uid=None,
                             sticky=False, warning=False):
        """Send a notification to logged in Odoo user.

        Args:
            message (str): Notification message.
            title (str): Notification title. If not specified: PBX.
            uid (int): Odoo user UID to send notification to. If not specified: calling user UID.
            sticky (boolean): Make a notiication message sticky (shown until closed). Default: False.
            warning (boolean): Make a warning notification type. Default: False.
        Returns:
            Always True.
        """
        # Use calling user UID if not specified.
        if not notify_uid:
            notify_uid = self.env.uid

        if release.version_info[0] < 15:
            self.env['bus.bus'].sendone(
                'odoopbx_actions_{}'.format(notify_uid),
                {
                    'action': 'notify',
                    'message': message,
                    'title': title,
                    'sticky': sticky,
                    'warning': warning
                })
        else:
            self.env['bus.bus']._sendone(
                'odoopbx_actions_{}'.format(notify_uid),
                'odoopbx_notify',
                {
                    'message': message,
                    'title': title,
                    'sticky': sticky,
                    'warning': warning
                })

        return True

    @api.model
    def odoopbx_reload_view(self, model):
        if release.version_info[0] < 15:
            msg = {
                'action': 'reload_view',
                'model': model,
            }
            self.env['bus.bus'].sendone('odoopbx_actions', json.dumps(msg))
        else:
            msg = {'model': model}
            self.env['bus.bus']._sendone(
                'odoopbx_actions',
                'reload_view',
                json.dumps(msg)
            )

    def get_pricing(self):
        api_url = self.get_param('api_url')
        url = urljoin(api_url, 'pricing')
        res = requests.get(url,
            json={
                'module_name': self.get_param('module_name'),
                'product_id': self.get_param('product_code'),
                'promotion_code': self.get_param('discount_code'),
            },
            headers={
                'x-instance-uid': self.get_param('instance_uid') or '',
                'x-api-key': self.get_param('api_key') or ''
            })
        if not res.ok:
            raise ValidationError(res.text)
        else:
            self.subscription_pricing = res.text


####################################################################################

    @api.model
    def _get_name(self):
        for rec in self:
            rec.name = 'General Settings'

    def open_settings_form(self):
        rec = self.env['asterisk_plus.settings'].search([])
        if not rec:
            rec = self.sudo().with_context(no_constrains=True).create({})
        else:
            rec = rec[0]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'asterisk_plus.settings',
            'res_id': rec.id,
            'name': 'General Settings',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    @api.model
    @ormcache('param')
    def get_param(self, param, default=False):
        """
        """
        data = self.search([])
        if not data:
            data = self.sudo().with_context(no_constrains=True).create({})
        else:
            data = data[0]
        return getattr(data, param, default)

    @api.model
    def set_param(self, param, value, keep_existing=False):
        """
        """
        data = self.search([])
        if not data:
            data = self.sudo().with_context(no_constrains=True).create({})
        else:
            data = data[0]
        # Check if the param is already there.
        if not keep_existing or not getattr(data, param):
            # TODO: How to handle Boolean fields!?
            setattr(data, param, value)
        else:
            debug(self, "Keeping existing value for param: {}".format(param))
        return True

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(Settings, self).create(vals)

    def write(self, vals):
        self.clear_caches()
        return super(Settings, self).write(vals)

    @api.model
    def odoopbx_notify(self, message, title='PBX', notify_uid=None,
                             sticky=False, warning=False):
        """Send a notification to logged in Odoo user.

        Args:
            message (str): Notification message.
            title (str): Notification title. If not specified: PBX.
            uid (int): Odoo user UID to send notification to. If not specified: calling user UID.
            sticky (boolean): Make a notiication message sticky (shown until closed). Default: False.
            warning (boolean): Make a warning notification type. Default: False.
        Returns:
            Always True.
        """
        # Use calling user UID if not specified.
        if not notify_uid:
            notify_uid = self.env.uid

        if release.version_info[0] < 15:
            self.env['bus.bus'].sendone(
                'odoopbx_actions_{}'.format(notify_uid),
                {
                    'action': 'notify',
                    'message': message,
                    'title': title,
                    'sticky': sticky,
                    'warning': warning
                })
        else:
            self.env['bus.bus']._sendone(
                'odoopbx_actions_{}'.format(notify_uid),
                'odoopbx_notify',
                {
                    'message': message,
                    'title': title,
                    'sticky': sticky,
                    'warning': warning
                })

        return True

    @api.model
    def odoopbx_reload_view(self, model):
        if release.version_info[0] < 15:
            msg = {
                'action': 'reload_view',
                'model': model,
            }
            self.env['bus.bus'].sendone('odoopbx_actions', json.dumps(msg))
        else:
            msg = {'model': model}
            self.env['bus.bus']._sendone(
                'odoopbx_actions',
                'reload_view',
                json.dumps(msg)
            )

    @api.constrains('record_calls')
    def record_calls_toggle(self):
        if 'no_constrains' in self.env.context:
            return
        # Enable/disable call recording event
        recording_event = self.env.ref('asterisk_plus.var_set_mixmon')
        # Check if enent can be updated
        if recording_event.update == 'no':
            raise ValidationError(
                _('Event {} is not updatebale'.format(recording_event.name)))
        recording_event.is_enabled = True if self.record_calls is True else False
        # Reload events map
        servers = self.env['asterisk_plus.server'].search([])
        for s in servers:
            s.ami_action(
                {'Action': 'ReloadEvents'},
            )

    @api.onchange('use_mp3_encoder')
    def on_change_mp3_encoder(self):
        if 'no_constrains' in self.env.context:
            return
        for rec in self:
            if rec.use_mp3_encoder:
                rec.mp3_encoder_bitrate = '96'
                rec.mp3_encoder_quality = '4'

    def sync_recording_storage(self):
        """Sync where call recordings are stored.
        """
        count = 0
        try:
            recordings = self.env['asterisk_plus.recording'].search([])
            for rec in recordings:
                if self.recording_storage == 'filestore' and not rec.recording_attachment:
                    rec.write({
                        'recording_data': False,
                        'recording_attachment': rec.recording_data})
                    count += 1
                    self.env.cr.commit()
                elif self.recording_storage == 'db' and not rec.recording_data:
                    rec.write({
                        'recording_attachment': False,
                        'recording_data': rec.recording_attachment})
                    count += 1
                    self.env.cr.commit()
                logger.info('Recording {} moved to {}'.format(rec.id, self.recording_storage))
        except Exception as e:
            logger.info('Sync recordings error: %s', str(e))
        finally:
            logger.info('Moved %s recordings', count)
            # Perform the garbage collection of the filestore.
            if release.version_info[0] >= 14:
                self.env['ir.attachment']._gc_file_store()
            else:
                self.env['ir.attachment']._file_gc()

    def post_update_billing_data(self):
        # Reload Agent config
        self.env.cr.commit()
        if self.get_param('is_subscribed'):
            self.env.ref('asterisk_plus.default_server').local_job(
                fun='agent_reload_config')

