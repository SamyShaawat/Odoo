from odoo import api, models, fields, _

class productTemplateNew(models.Model):
    _inherit = "product.template"

    product_website_link = fields.Char(string="Product website Link", compute="_compute_product_website_link")
    product_availability = fields.Selection([('in stock', 'in stock'), ('out of stock', 'out of stock')], compute="compute_product_availability")
    prod_condition = fields.Char(string="Condition", default="new")
    google_product_availability = fields.Selection([('in_stock', 'in_stock'), ('out_of_stock', 'out_of_stock')], compute="compute_product_availability")

    def _compute_product_website_link(self):
        for product in self:
            baseurl = self.env["ir.config_parameter"].sudo().search([('key', '=', 'web.base.url')])
            product.product_website_link = baseurl.value + product.website_url

    def compute_product_availability(self):
        for product in self:
            if product.qty_available > 0:
                product.product_availability = 'in stock'
                product.google_product_availability = 'in_stock'
            else:
                product.product_availability = 'out of stock'
                product.google_product_availability = 'out_of_stock'


class productTemplateNew(models.Model):
    _inherit = "product.product"

    product_website_link = fields.Char(string="Product website Link", compute="_compute_product_variant_website_link")
    product_availability = fields.Selection([('in stock', 'in stock'), ('out of stock', 'out of stock')], compute="compute_product_variant_availability")
    prod_condition = fields.Char(string="Condition", default="new")
    google_product_availability = fields.Selection([('in_stock', 'in_stock'), ('out_of_stock', 'out_of_stock')], compute="compute_product_variant_availability")
    google_brand = fields.Char(string="google brand", compute="compute_brand_vals")
    price_with_currency = fields.Monetary(string="Price", compute="compute_price_with_currency")

    def _compute_product_variant_website_link(self):
        for product in self:
            baseurl = self.env["ir.config_parameter"].sudo().search([('key', '=', 'web.base.url')])
            product.product_website_link = baseurl.value + product.website_url

    def compute_product_variant_availability(self):
        for product in self:
            if product.qty_available > 0:
                product.product_availability = 'in stock'
                product.google_product_availability = 'in_stock'
            else:
                product.product_availability = 'out of stock'
                product.google_product_availability = 'out_of_stock'

    def compute_brand_vals(self):
        for product in self:
            product.google_brand = ''
            attribute_line_ids = product.product_tmpl_id.attribute_line_ids.filtered(lambda line : line.attribute_id.name == 'Brand')
            if attribute_line_ids and attribute_line_ids[0].value_ids:
                product.google_brand = attribute_line_ids[0].value_ids[0].name

    def compute_price_with_currency(self):
        for product in self:
            product.price_with_currency = product.lst_price