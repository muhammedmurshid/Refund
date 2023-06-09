from odoo import models, fields, api


class RefundPayment(models.Model):
    _name = 'refund.payment'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name', readonly=True)
    amount = fields.Float(string='Refund Requested', readonly=True)
    batch = fields.Char(string='Batch', readonly=True)
    course = fields.Many2one('logic.courses', string='Course', readonly=True)
    id_refund_record = fields.Integer(string='Refund Record id')
    status = fields.Selection([
        ('in_payment', 'Draft'),
        ('cancel', 'Cancel'),
        ('paid', 'Paid'),
    ], string='Status', default='in_payment')
    transaction_id = fields.Char(string='Transaction id')
    student_admission_no = fields.Char('Admission number', readonly=True)
    # invoice_number = fields.Char('Invoice number', readonly=True)
    # invoice_date = fields.Date('Invoice date', readonly=True)
    date_of_refund = fields.Date('Refund date')
    refund_amount = fields.Float('Amount Refunded')

    @api.depends('refund_amount')
    def refund_amound_total(self):
        for rec in self:
            rec.total_refund = self.refund_amount

    total_refund = fields.Float('Total', compute='refund_amound_total', store=True, tracking=True)

    def paid(self):
        ss = self.env['student.refund'].search([])
        for i in ss:
            if self.name == i.student_name and self.student_admission_no == i.student_admission_no and self.id_refund_record == i.id:
                i.status = 'paid'
        self.status = 'paid'

    def cancel(self):
        self.status = 'cancel'
