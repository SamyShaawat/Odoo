# -*- coding: utf-8 -*-
# Part of AppJetty. See LICENSE file for full copyright and
# licensing details.

import os
import time
import datetime
from odoo import api, fields, models, _
# from odoo.addons.biztech_prod_data_feeds.controllers.main import GenerateFeeds
import logging
import base64
_logger = logging.getLogger(__name__)


class WebsiteDataFeeds(models.Model):
    _name = "website.data.feeds"
    _rec_name = 'sequence'
    _order = 'sequence'
    _description = 'Data Feed Manager'

    sequence = fields.Char(
        string="Sequence", readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(
        string="Active", default=True, help="Active true will count this feed and active false will not count this feed.")
    website_id = fields.Many2one('website', string="Website", required=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', required=True)
    file_name = fields.Char(string="File Name", required=True)
    header_pattern = fields.Text(string="Header Pattern", required=True)
    product_pattern = fields.Text(string="Product Pattern", required=True)
    final_product_pattern = fields.Text(string="Final Product Pattern")
    footer_pattern = fields.Text(string="Footer Pattern", required=True)
    url = fields.Char(string="Live Feed URL", readonly=True)
    file_last_modified = fields.Datetime(
        string='File last modified on', readonly=True)
    stored_file_path = fields.Char(
        string="Stored Feed Filepath", readonly=True)
    product_ids = fields.Many2many('product.product', 'feed_products_rel',
                                   'feed_id', 'prod_tmpl_id', string='Products')
    assign_parent_tag = fields.Char(string="Feed Parent Tag", default="product",
                                    required=True, help="You can declare the parent tag name of your feed")

    _sql_constraints = [
        ('feed_file_name_uniq', 'unique(file_name)',
         'File name must be unique !'),
    ]

    def create_prod_feed_file(self, automatic=False):
        feed_data = self.search([('active', '=', True)])
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        mail_tmpl_obj = self.env['mail.template']
        success_tmp_id = self.env.ref("biztech_prod_data_feeds.prod_data_feed_mail_template_success").id
        error_tmp_id = self.env.ref("biztech_prod_data_feeds.prod_data_feed_mail_template_error").id
        for feed in feed_data:
            self.env['generatefeeds.live.feeds'].sudo().generate_live_feeds(feed)
            try:
                xml_file = feed.file_name + '.xml'
                abc = str(feed.header_pattern) + '\n' + \
                    str(feed.final_product_pattern) + '\n' + str(feed.footer_pattern)
                attachment_obj = self.env['ir.attachment']
                exit_file = attachment_obj.sudo(
                ).search([('res_model', '=', 'website.data.feeds'),
                          ('name', '=', xml_file)])
                if exit_file:
                    # Update the existing attachment
                    exit_file.sudo().write({
                        'datas': base64.b64encode(abc.encode()),
                    })
                else:
                    # Create a new attachment if it does not exist
                    attch_id = attachment_obj.create({
                        'name': xml_file,
                        'res_model': 'website.data.feeds',
                        'res_id': feed.id,
                        'public': True,
                        'type': 'binary',
                        'datas': base64.b64encode(abc.encode()),
                        'mimetype': 'application/xml'
                    })
                if exit_file or attch_id:
                    feed.write({
                        'stored_file_path': base_url + '/feeds/web/content/' + str(
                            (exit_file or attch_id).id) + '/' + xml_file,
                        'file_last_modified': fields.Datetime.now(),
                    })
                    if success_tmp_id:
                        mail_tmpl_obj.browse(success_tmp_id).send_mail(
                            feed.id, force_send=True)
                        _logger.info(
                            'Data feed named %s successfully generated.', (feed.file_name))
            except:
                if error_tmp_id:
                    mail_tmpl_obj.browse(error_tmp_id).send_mail(
                        feed.id, force_send=True)
                    _logger.exception(
                        'Data feed generation failed for %s.', (feed.file_name))

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'website.data.feeds') or 'New'
        result = super(WebsiteDataFeeds, self).create(vals)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        result.url = base_url + '/feeds/' + str(result.id)
        return result

    def write(self, vals):
        res = super(WebsiteDataFeeds, self).write(vals)
        if vals.get('website_id'):
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            self.url = base_url + '/feeds/' + str(self.id)
        return res
