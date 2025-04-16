from odoo import http
from odoo.http import request


class HospitalController(http.Controller):
    @http.route("/hello", auth="public", website=True)
    def hello(self, **kwargs):
        # Prepare any data you want to send to the template
        values = {"message": "Welcome to the Hospital Portal!"}
        # Render the template defined by its XML id.
        return request.render("om_hospital.template_hello", values)
