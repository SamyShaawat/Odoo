# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MyAppointmentsController(http.Controller):
    @http.route("/my-appointments", auth="public", website=True)
    def my_appointments(self, **kwargs):
        # Find the patient record related to the current user
        patient = (
            request.env["hospital.patient"]
            .sudo()
            .search([("user_id", "=", request.env.uid)], limit=1)
        )

        if patient:
            # Search all appointments linked to this patient's id
            appointments = (
                request.env["hospital.appointment"]
                .sudo()
                .search([("patient_id", "=", patient.id)])
            )
        else:
            appointments = request.env["hospital.appointment"].sudo().browse([])

        values = {
            "appointments": appointments,
            "patient": patient,
        }
        return request.render("om_hospital.my_appointments_template", values)
