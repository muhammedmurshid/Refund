from odoo import fields, models, api, _
import requests
from datetime import date, datetime
from odoo.exceptions import UserError


class StudentRefund(models.Model):
    _name = 'student.refund'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_no'
    _description = "Refund"

    student_name = fields.Char(string='Name', readonly=True)
    reference_no = fields.Char(string="Sequence Number", readonly=True, required=True,
                               copy=False, default='New')
    batch = fields.Char(string='Batch', readonly=True)
    course = fields.Many2one('logic.courses', string='Course', readonly=True)
    email = fields.Char(string='Email', readonly=True)
    phone_number = fields.Char(string='Phone number', widget='phone', readonly=True)
    reason = fields.Text(string='Student reason', readonly=True)
    status = fields.Selection([
        ('accountant', 'Draft'),
        ('teacher', 'Teacher Approval'),
        ('head_assign', 'Head Approval'),
        ('head', 'Head Approval'),
        ('manager', 'Manager Approval'),
        ('accounts', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
    ], string='Status', default='accountant')
    assign_head = fields.Many2one('res.users', string='Assign head')

    branch = fields.Char('Branch', readonly=True)
    student_admission_no = fields.Char('Admission number', readonly=True)
    parent_number = fields.Char('Parent number', readonly=True)
    # invoice_number = fields.Text('Invoice number', readonly=True)
    # invoice_date = fields.Text('Invoice date', readonly=True)
    sat_class = fields.Integer(string='How many days he sat in the class')
    teacher_reason = fields.Text('Remarks for teacher')
    head_reason = fields.Text('Remarks of head')
    assign_to = fields.Many2one('hr.employee', string='Assign to')

    make_visible_teacher = fields.Boolean(string="User", default=True, compute='get_teacher')
    action_testing = fields.Float('Action')
    stream = fields.Selection([
                ('online', 'Online'),
                ('offline', 'Offline'),
            ], string='Stream')
    attended_class = fields.Integer(string='Attended class')
    total_class = fields.Integer(string='Total class')
    session_completed = fields.Text(string='Session completed')
    part_attended = fields.Text(string='Part attended')
    admission_officer = fields.Char(string='Admission officer')
    board_registration = fields.Selection([('completed', 'Completed'),
                                           ('not', 'Not')], string='Board registration')
    board_check = fields.Boolean()
    inv_ids = fields.One2many('refund.invoice.details', 'inv_id', string='Invoices')
    account_number = fields.Char(string='Account number')
    account_holder_name = fields.Char(string='Account holder name')
    ifsc_code = fields.Char(string='IFSC code')
    bank_name = fields.Char(string='Bank name')

    @api.depends('inv_ids.refund_amt')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        total = 0
        for order in self.inv_ids:
            total += order.refund_amt
        self.update({
            'ref_total': total,
        })

    ref_total = fields.Float(string='Total Refund', compute='_amount_all', store=True)

    @api.depends('ref_total')
    def total_amount_refund(self):
        for rec in self:
            rec.amount = rec.ref_total

    amount = fields.Float(string='Amount', readonly=True, compute='total_amount_refund', store=True)

    def confirm_assign(self):
        if not self.assign_to:
            raise UserError('Please assign a Teacher..')
        else:
            self.status = 'teacher'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Assigned')
            other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
                'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            other_activity_ids.unlink()

            if self.course.board_registration == True:
                self.board_check = True
            else:
                self.board_check = False
        # return {
        #     'effect': {
        #         'fadeout': 'slow',
        #         'message': 'Teacher Assigned',
        #         'type': 'rainbow_man',
        #     }
        # }

        # users = self.env.ref('refund_logic.group_refund_teacher').users
        # activity_type = self.env.ref('refund_logic.mail_activity_refund_alert_custome')
        # self.activity_schedule('refund_logic.mail_activity_refund_alert_custome', user_id=self.assign_to.id,
        #                        note=f'Please Approve {self.assign_to.name}')
        #
        # print(self.env.ref('refund_logic.mail_activity_refund_alert_custome').id, 'lll')

    def confirm_assign_teacher(self):
        if not self.assign_to:
            raise UserError('Please assign a Teacher..')
        else:
            self.status = 'teacher'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Assigned')
            other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
                'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            other_activity_ids.unlink()

    @api.depends('make_visible_teacher')
    def get_teacher(self):
        print('kkkll')
        user_crnt = self.env.user.id

        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('Refund.group_refund_teacher'):
            self.make_visible_teacher = False

        else:
            self.make_visible_teacher = True

    make_visible_head = fields.Boolean(string="User", default=True, compute='get_head')

    @api.depends('make_visible_head')
    def get_head(self):
        print('kkkll')
        user_crnt = self.env.user.id

        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('Refund.group_refund_marketing_head'):
            self.make_visible_head = False

        else:
            self.make_visible_head = True

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'student.refund') or _('New')
        res = super(StudentRefund, self).create(vals)
        return res

    # def accountant_approval(self):
    #     # self.make_visible_teacher = True
    #     self.status = 'teacher'

    def teacher_approval(self):
        self.message_post(body="Teacher is approved")
        self.status = 'head_assign'
        activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback='Teacher Approved')
        other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        other_activity_ids.unlink()
        # self.activity_schedule('refund_logic.mail_activity_refund_alert_custome', user_id=user.id,
        #                        note='Please Approve')

    def head_approval(self):
        print(self.assign_to.parent_id.user_id.name, 'jjj')

        if self.assign_to.parent_id.user_id.id == self.env.user.id:
            self.message_post(body="Head is approved")
            self.status = 'manager'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Head Approved')
            other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
                'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            other_activity_ids.unlink()
        else:
            raise UserError('Only approval access teacher head')



    def manager_approval(self):
        self.message_post(body="Marketing Manager is approved")
        self.env['refund.payment'].create({
            'name': self.student_name,
            'amount': self.ref_total,
            'batch': self.batch,
            'course': self.course.id,
            'student_admission_no': self.student_admission_no,
            'id_refund_record': self.id,
            # 'invoice_number': self.invoice_number,
            # 'invoice_date': self.invoice_date,

        }
        )
        self.status = 'accounts'
        activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback='Manager Approved')
        other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        other_activity_ids.unlink()

    def rejected(self):
        self.status = 'reject'
        activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback=f'Rejected {self.env.user.name}')
        other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        other_activity_ids.unlink()

        # current = self.env.user
        # main_content = {
        #     'subject': 'STUDENT REFUND',
        #     'body_html': f"<h1>Hello {self.name} Your refund request is rejected..</h1>",
        #     'email_to': self.email,
        #     # 'attachment_ids': attachment
        #
        # }
        # self.env['mail.mail'].create(main_content).send()

    def paid_payments(self):
        self.status = 'paid'

    def teacher_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'teacher':
                users = ss.env.ref('Refund.group_refund_teacher').users
                activity_type = i.env.ref('Refund.mail_activity_refund_alert_custome')
                i.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=i.assign_to.id,
                                    note=f'Please Approve {i.assign_to.name}')

    def head_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'head':
                users = ss.env.ref('Refund.group_refund_marketing_head').users
                for j in users:
                    activity_type = i.env.ref('Refund.mail_activity_refund_alert_custome')
                    i.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=j.id,
                                        note=f'Please Approve {j.name}')

    def accounts_request_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'accountant':
                users = ss.env.ref('Refund.group_refund_accounts').users
                for j in users:
                    activity_type = i.env.ref('Refund.mail_activity_refund_alert_custome')
                    i.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=j.id,
                                        note='Received a new Refund request form')

    def marketing_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'manager':
                users = ss.env.ref('Refund.refund_manager').users
                for j in users:
                    activity_type = i.env.ref('Refund.mail_activity_refund_alert_custome')
                    i.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=j.id,
                                        note=f'Please Approve {j.name}')


class PaymentDetails(models.Model):
    _name = 'payment.details'
    _inherit = 'mail.thread'

    refund_amount = fields.Float(string='Refund amount')
    refund_date = fields.Date(string='Refund date')
    transaction_id = fields.Integer(string='Transaction id')


class RefundInvoiceDetails(models.Model):
    _name = 'refund.invoice.details'
    _inherit = 'mail.thread'

    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')
    refund_amt = fields.Integer(string='Refund Amount')
    inv_id = fields.Many2one('student.refund', string='Invoice')
