from odoo import fields, models, api, _
import requests
from datetime import date, datetime
from odoo.exceptions import UserError
import requests


class StudentRefund(models.Model):
    _name = 'student.refund'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_no'
    _description = "Refund"

    student_name = fields.Char(string='Name', readonly=True)
    reference_no = fields.Char(string="Sequence Number", readonly=True, required=True,
                               copy=False, default='New')
    batch = fields.Char(string='Batch', readonly=True)
    course = fields.Many2one('logic.courses', string='Course', readonly=True)
    email = fields.Char(string='Email', readonly=True)
    phone_number = fields.Char(string='Phone Number', widget='phone', readonly=True)
    reason = fields.Text(string='Student Reason', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    ded_ids = fields.One2many('refund.deduction', 'ded_id', string='Deduction')
    status = fields.Selection([
        ('accountant', 'Draft'),
        ('teacher', 'Teacher Approval'),
        ('head_assign', 'Academic Head Approval'),
        ('head', 'Head Approval'),
        ('manager', 'Marketing Manager Approval'),
        ('accounts', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
    ], string='Status', default='accountant')
    assign_head = fields.Many2one('res.users', string='Assign head')

    branch = fields.Char('Branch', readonly=True)
    student_admission_no = fields.Char('Admission Number', readonly=True)
    parent_number = fields.Char('Parent Number', readonly=True)
    # invoice_number = fields.Text('Invoice number', readonly=True)
    # invoice_date = fields.Text('Invoice date', readonly=True)
    sat_class = fields.Integer(string='How many days he sat in the class')
    teacher_reason = fields.Text('Remarks for teacher')
    head_reason = fields.Text('Remarks of Academic Head')
    assign_to = fields.Many2one('hr.employee', string='Assign to')

    make_visible_teacher = fields.Boolean(string="User", default=True, compute='get_teacher')
    action_testing = fields.Float('Action')
    stream = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
    ], string='Stream')
    attended_class = fields.Integer(string='Attended Class')
    total_class = fields.Integer(string='Total Class')
    session_completed = fields.Text(string='Session Completed')
    part_attended = fields.Text(string='Part Attended')
    admission_officer = fields.Char(string='Admission Officer')
    board_registration = fields.Selection([('completed', 'Completed'),
                                           ('not', 'Not')], string='Board registration')
    board_check = fields.Boolean()
    inv_ids = fields.One2many('refund.invoice.details', 'inv_id', string='Invoices')
    account_number = fields.Char(string='Account Number')
    account_holder_name = fields.Char(string='Account holder name')
    ifsc_code = fields.Char(string='IFSC Code')
    bank_name = fields.Char(string='Bank Name')

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

    ref_total = fields.Float(string='Refund Requested', compute='_amount_all', store=True)

    # @api.depends('ref_total')
    # def refund_allowed_total(self):
    #     for i in self:
    #         if i.refund_allowed== 0.0 and i.ref_total:
    #             self.refund_allowed = i.ref_total
    #         else:
    #             self.refund_allowed = i.refund_allowed
    refund_allowed_amt = fields.Float(string='Total Paid', readonly=False)

    @api.depends('ded_ids.amount')
    def _amount_deduction_all(self):
        """
        Compute the total amounts of the SO.
        """
        total_deduction = 0
        for order in self.ded_ids:
            total_deduction += order.amount
        self.update({
            'total_deduction': total_deduction,
        })

    total_deduction = fields.Float(string='Total Deduction', compute='_amount_deduction_all', store=True)

    @api.depends('total_deduction', 'ref_total', 'refund_allowed_amt')
    def _amount_total_refund(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            total_deduction = order.refund_allowed_amt - order.total_deduction
        self.update({
            'total_all_refund': total_deduction
        })

    total_all_refund = fields.Float(string='Total Refund', compute='_amount_total_refund', store=True)

    @api.depends('ref_total')
    def total_amount_refund(self):
        for rec in self:
            rec.amount = rec.ref_total

    amount = fields.Float(string='Amount', readonly=True, compute='total_amount_refund', store=True)

    def confirm_assign(self):
        if not self.assign_to:
            raise UserError('Please assign a Teacher..')
        else:
            if self.phone_number:
                # for students refund responds
                std_mobile = self.phone_number
                student = self.student_name
                std_template = '1107169772717746551'
                refund_student = "Greetings" + " " + student + " " + "from Logic School of Management  we have received your refund request and will be contacting you soon."
                url_std = "http://sms.mithraitsolutions.com/httpapi/httpapi?token=adf60dcda3a04ec6d13f827b38349609&sender=LSMKCH&number=" + str(
                    std_mobile) + "&route=2&type=Text&sms=" + refund_student + "&templateid=" + std_template

                # A GET request to the API
                response = requests.get(url_std)
                # Print the response
                response_json = response.json()


            # for teacher refund request
            if self.assign_to.mobile_phone:
                mobile = self.assign_to.mobile_phone
                user = self.assign_to.name
                type = "Logic Students"
                message_approved = "Hi " + user + ", new refund request received from " + type + " Ref : " + self.reference_no + " " + "For more details login to Logic Odoo ERP"
                dlt_approved = '1107169772701012154'
                url = "http://sms.mithraitsolutions.com/httpapi/httpapi?token=adf60dcda3a04ec6d13f827b38349609&sender=LSMKCH&number=" + str(
                    mobile) + "&route=2&type=Text&sms=" + message_approved + "&templateid=" + dlt_approved

                # A GET request to the API
                response = requests.get(url)

                # Print the response
                response_json = response.json()
                print(response_json)
            self.status = 'teacher'
            self.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=self.assign_to.user_id.id,
                                   note='Please approve the refund request.')
            # self.message_post(body="Assigned To " + self.assign_to.name)
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            if activity_id:
                activity_id.action_feedback(feedback='Assigned')
            # activity_id.action_feedback(feedback='Assigned To' + " " + self.assign_to.name)
            # other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
            #     'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            # other_activity_ids.unlink()
            if self.course.board_registration == True:
                self.board_check = True
            else:
                self.board_check = False
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Teacher Assigned',
                    'type': 'rainbow_man',
                }
            }

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
            # self.status = 'teacher'
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

    def compute_count(self):
        for record in self:
            record.payment_count = self.env['refund.payment'].search_count(
                [('id_refund_record', '=', self.id)])

    payment_count = fields.Integer(compute='compute_count')

    def get_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'view_mode': 'tree,form',
            'res_model': 'refund.payment',
            'domain': [('id_refund_record', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('make_visible_accountant')
    def get_accountant(self):
        print('kkkll')
        user_crnt = self.env.user.id

        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('Refund.group_refund_accounts'):
            self.make_visible_accountant = False

        else:
            self.make_visible_accountant = True

    make_visible_accountant = fields.Boolean(string="User", default=True, compute='get_accountant')

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
        self.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=self.assign_to.parent_id.user_id.id,
                               note='Please approve the refund request.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved successfully.',
                'type': 'rainbow_man',
            }
        }
        # self.activity_schedule('refund_logic.mail_activity_refund_alert_custome', user_id=user.id,
        #                        note='Please Approve')

    def head_approval(self):
        if self.assign_to.parent_id.user_id.id == self.env.user.id:

            print(self.assign_to.parent_id.user_id.name, 'jjj')
            self.status = 'manager'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Head Approved')
            users = self.env.ref('Refund.refund_manager').users
            for j in users:
                self.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=j.id,
                                       note='Please approve the refund request.')
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Approved successfully.',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise UserError('Only approval access teacher head')

    def manager_approval(self):
        # self.message_post(body="Marketing Manager is approved")
        self.env['refund.payment'].create({
            'name': self.student_name,
            'amount': self.total_all_refund,
            'batch': self.batch,
            'course': self.course.id,
            'student_admission_no': self.student_admission_no,
            'id_refund_record': self.id,
            'account_number': self.account_number,
            'bank_name': self.bank_name,
            'ifsc_code': self.ifsc_code,
            'account_holder_name': self.account_holder_name,
            'total_refund': self.total_all_refund,
            # 'invoice_number': self.invoice_number,
            # 'invoice_date': self.invoice_date,

        }
        )
        self.status = 'accounts'
        manager_users = self.env.ref('Refund.refund_manager').users
        for manager in manager_users:
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', manager.id), (
                    'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Manager Approved')

        users = self.env.ref('Refund.group_refund_accounts').users
        for j in users:
            self.activity_schedule('Refund.mail_activity_refund_alert_custome', user_id=j.id,
                                   note='Please approve the refund request.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved successfully.',
                'type': 'rainbow_man',
            }
        }

    def remove_activity_for_manager(self):
        print('erwyuqqwqwi')
        # if self.status != 'manager':
        #     users = self.env.ref('Refund.refund_manager').users
        #     for i in users:
        #         activity_id = self.env['mail.activity'].search([('user_id', '=', i.id), (
        #             'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        #         activity_id.unlink()

    def remove_activity_for_accounts(self):
        refund_record = self.env['student.refund'].search([])
        users = self.env.ref('Refund.group_refund_accounts').users
        for i in users:
            # print(i.name, 'lll')
            for record in refund_record:
                if record.status != 'accounts':
                    activity_id = record.env['mail.activity'].search(
                        [('res_id', '=', record.id), ('user_id', '=', i.id), (
                            'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
                    activity_id.unlink()

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
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Paid successfully.',
                'type': 'rainbow_man',
            }
        }

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
    inv_id = fields.Many2one('student.refund', string='Invoice', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)


class RefundDeduction(models.Model):
    _name = 'refund.deduction'
    _inherit = 'mail.thread'

    item = fields.Char(string='Name')
    amount = fields.Float(string='Amount')
    ded_id = fields.Many2one('student.refund', string='Deduction', ondelete='cascade')
