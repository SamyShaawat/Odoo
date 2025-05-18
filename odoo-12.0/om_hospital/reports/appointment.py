# -*- coding: utf-8 -*-
from odoo import models, api


class AppointmentReport(models.AbstractModel):
    _name = "report.om_hospital.appointment_report"
    _description = "Appointment Prescription Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["hospital.appointment"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "hospital.appointment",
            "docs": docs,
        }
