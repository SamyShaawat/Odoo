# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def default_get(self, default_fields):
        res = super(StockQuant, self).default_get(default_fields)
        if 'branch_id' in default_fields:
            if self.env.user.branch_id:
                res.update({
                    'branch_id' : self.env.user.branch_id.id or False
                })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self._context.get('branch'):
                vals.update({'branch_id':self.env.user.branch_id.id})
        return super(StockQuant, self).create(vals_list)

    def write(self, vals):
        if not self._context.get('branch'):
            vals.update({'branch_id':self.env.user.branch_id.id})
        return super(StockQuant, self).write(vals)
    
    @api.model
    def _get_inventory_fields_create(self):
        res = super(StockQuant, self)._get_inventory_fields_create()
        res.append('branch_id')
        return res


    @api.model
    def _get_inventory_fields_write(self):
        res = super(StockQuant, self)._get_inventory_fields_write()
        res.append('branch_id')
        return res

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        selected_brach = self.branch_id
        if selected_brach:
            user_id = self.env['res.users'].browse(self.env.uid)
            user_branch = user_id.sudo().branch_id
            if not self.env.user.has_group('base.group_user') or (user_branch and user_branch.id != selected_brach.id):
                raise UserError("Please select active branch only. Other may create the Multi branch issue. \n\ne.g: If you wish to add other branch then Switch branch from the header and set that.")



    def action_apply_inventory(self):
        res = super(StockQuant, self).action_apply_inventory()
        for quant in self:
            if not self._context.get('branch'):
                quant.branch_id = self.env.user.branch_id.id or False
        return res


    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ Increase or decrease `quantity` or 'reserved quantity' of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        if not (quantity or reserved_quantity):
            raise ValidationError(_('Quantity or Reserved Quantity should be set.'))
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if lot_id and quantity > 0:
            quants = quants.filtered(lambda q: q.lot_id)

        if location_id.should_bypass_reservation():
            incoming_dates = []
        else:
            incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                              float_compare(quant.quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute("SELECT id FROM stock_quant WHERE id IN %s ORDER BY lot_id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED", [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])
        
        if self._context.get('branch'):
            if quant:
                vals = {'in_date': in_date,'branch_id':self._context.get('branch')}
                if quantity:
                    vals['quantity'] = quant.quantity + quantity
                if reserved_quantity:
                    vals['reserved_quantity'] = quant.reserved_quantity + reserved_quantity
                quant.write(vals)
            else:
                vals = {
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'lot_id': lot_id and lot_id.id,
                    'package_id': package_id and package_id.id,
                    'owner_id': owner_id and owner_id.id,
                    'in_date': in_date,
                    'branch_id':self._context.get('branch')
                }
                if quantity:
                    vals['quantity'] = quantity
                if reserved_quantity:
                    vals['reserved_quantity'] = reserved_quantity
                self.create(vals)
        else:
            if quant:
                vals = {'in_date': in_date}
                if quantity:
                    vals['quantity'] = quant.quantity + quantity
                if reserved_quantity:
                    vals['reserved_quantity'] = quant.reserved_quantity + reserved_quantity
                quant.write(vals)
            else:
                vals = {
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'lot_id': lot_id and lot_id.id,
                    'package_id': package_id and package_id.id,
                    'owner_id': owner_id and owner_id.id,
                    'in_date': in_date,
                }
                if quantity:
                    vals['quantity'] = quantity
                if reserved_quantity:
                    vals['reserved_quantity'] = reserved_quantity
                self.create(vals)
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=False, allow_negative=True), in_date
