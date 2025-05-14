from email.policy import default

from chardet import detect_all
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError, AccessError, ValidationError, RedirectWarning
import base64
from io import BytesIO
from datetime import datetime, time, timedelta
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class InheritSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    months = fields.Many2many('months.model')
    created = fields.Boolean('Created', readonly=False, copy=False)
    number_of_services = fields.Integer(compute='get_number_of_services', store=True)

    def _timesheet_service_generation(self):
        """ For service lines, create the task or the project. If already exists, it simply links
            the existing one to the line.
            Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
            new project/task. This explains the searches on 'sale_line_id' on project/task. This also
            implied if so line of generated task has been modified, we may regenerate it.
        """
        so_line_task_global_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project')
        so_line_new_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking in ['project_only', 'task_in_project'])

        # search so lines from SO of current so lines having their project generated, in order to check if the current one can
        # create its own project, or reuse the one of its order.
        map_so_project = {}
        if so_line_new_project:
            order_ids = self.mapped('order_id').ids
            so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), (
                'product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                                                 ('product_id.project_template_id', '=', False)])
            map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
            so_lines_with_project_templates = self.search(
                [('order_id', 'in', order_ids), ('project_id', '!=', False), (
                    'product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                 ('product_id.project_template_id', '!=', False)])
            map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for
                                        sol
                                        in so_lines_with_project_templates}

        # search the global project of current SO lines, in which create their task
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in
                               so_line_task_global_project}

        def _can_create_project(sol):
            if not sol.project_id:
                if sol.product_id.project_template_id and not self.order_id.sale_order_template_id:
                    return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
                elif sol.order_id.id not in map_so_project:
                    return True
            return False

        def _determine_project(so_line):
            """Determine the project for this sale order line.
            Rules are different based on the service_tracking:

            - 'project_only': the project_id can only come from the sale order line itself
            - 'task_in_project': the project_id comes from the sale order line only if no project_id was configured
              on the parent sale order"""

            if so_line.product_id.service_tracking == 'project_only':
                return so_line.project_id
            elif so_line.product_id.service_tracking == 'task_in_project':
                return so_line.order_id.project_id or so_line.project_id

            return False

        # task_global_project: create task in global project
        for so_line in so_line_task_global_project:
            if not so_line.task_id:
                if map_sol_project.get(so_line.id) and so_line.product_uom_qty > 0:
                    if not self.order_id.sale_order_template_id:
                        so_line._timesheet_create_task(project=map_sol_project[so_line.id])
                    else:
                        self.set_lines_as_tasks()

        # project_only, task_in_project: create a new project, based or not on a template (1 per SO). May be create a task too.
        # if 'task_in_project' and project_id configured on SO, use that one instead
        for so_line in so_line_new_project:
            project = _determine_project(so_line)
            if not project and _can_create_project(so_line):
                project = so_line._timesheet_create_project()
                if so_line.product_id.project_template_id and not self.order_id.sale_order_template_id:
                    map_so_project_templates[
                        (so_line.order_id.id, so_line.product_id.project_template_id.id)] = project
                else:
                    map_so_project[so_line.order_id.id] = project
            elif not project and not self.order_id.sale_order_template_id:
                # Attach subsequent SO lines to the created project
                so_line.project_id = (
                        map_so_project_templates.get(
                            (so_line.order_id.id, so_line.product_id.project_template_id.id))
                        or map_so_project.get(so_line.order_id.id)
                )
            if so_line.product_id.service_tracking == 'task_in_project':
                if not project:
                    if so_line.product_id.project_template_id and not self.order_id.sale_order_template_id:
                        project = map_so_project_templates[
                            (so_line.order_id.id, so_line.product_id.project_template_id.id)]
                    else:
                        project = map_so_project[so_line.order_id.id]
                if not so_line.task_id:
                    if not self.order_id.sale_order_template_id:
                        so_line._timesheet_create_task(project=project)
                    else:
                        self.set_lines_as_tasks()
            so_line._generate_milestone()

    def set_lines_as_tasks(self):
        for rec in self.filtered(
                lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_in_project' and not sol.created):
            tasklist = []
            monthlist = {}
            start = rec.order_id.project_start_date
            end = rec.order_id.project_end_date
            if start and end:
                for k in range(start.year, end.year + 1):
                    monthlist[k] = set()
                for i in range(1, (end - start).days + 1, 20):
                    for n in monthlist.keys():
                        if start.year == n:
                            monthlist[n].add(start.month)
                            start = start + timedelta(days=20)

            else:
                raise ValidationError(_("You Need Start Date And End Date"))
            if rec.order_id.project_ids:
                if not rec.created:
                    numbers_months = rec.months.filtered(
                        lambda k: k.name != 'All Months')
                    for i in numbers_months:
                        for key, value in monthlist.items():
                            if int(i.name) in value:
                                deadline = datetime(key, int(i.name), rec.order_id.projectstart_date.day, 0o1, 30, 0o1)
                                tasklist.append(
                                    (0, 0, {'name': rec.product_template_id.name,
                                            'planned_date_begin': deadline if rec.order_id.project_start_date == deadline.date() else deadline.replace(
                                                day=1),
                                            'date_deadline': deadline.replace(day=1) + timedelta(days=30),
                                            'user_ids': False,
                                            'sale_line_id': rec.id,
                                            'sale_order_id': rec.order_id.id,
                                            'description': rec.name,
                                            }))
                                rec.created = True
                for line in rec.order_id.project_ids:
                    line.task_ids = tasklist
            else:
                raise ValidationError(_("You Don't have project to assign Tasks"))

    @api.onchange('order_id.project_start_date', 'order_id.project_end_date', 'order_id.num_of_trees')
    @api.depends('order_id.project_start_date', 'order_id.project_end_date', 'order_id.num_of_trees')
    def get_number_of_services(self):
        monthlist = {}
        for line in self:
            start = line.order_id.project_start_date
            end = line.order_id.project_end_date
            if start and end:
                for k in range(start.year, end.year + 1):
                    monthlist[k] = set()
                for i in range(1, (end - start).days + 1, 20):
                    for n in monthlist.keys():
                        if start.year == n:
                            monthlist[n].add(start.month)
                            start = start + timedelta(days=20)
                for j in line.months:
                    for key, value in monthlist.items():
                        if int(j.name) in value:
                            line.number_of_services += 1
                line.product_uom_qty = line.order_id.num_of_trees * line.number_of_services
