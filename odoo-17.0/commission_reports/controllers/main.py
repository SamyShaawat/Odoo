# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import content_disposition, request
# from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class CommissionReportController(http.Controller):

    @http.route('/commission_reports/<string:output_format>/<string:report_name>', type='http', auth='user')
    def report(self, model, output_format, report_name=False, **kw):
        uid = request.session.uid
        options = json.loads(kw.get('options', '{}'))
        cids = kw.get('allowed_company_ids')
        if not cids or cids == 'null':
            cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        report_obj = request.env[model].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        try:
            if output_format == 'pdf':
                response = request.make_response(
                    report_obj.get_pdf(options),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', content_disposition(report_name + '.pdf'))
                    ]
                )
                return response
            if output_format == 'xlsx':
                response = request.make_response(
                    report_obj.get_xlsx(options),
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                # response.stream.write(request.env[model].with_user(uid).get_xlsx(options))
                return response
        except Exception as e:
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
            }
            return request.make_response(html_escape(json.dumps(error)))
