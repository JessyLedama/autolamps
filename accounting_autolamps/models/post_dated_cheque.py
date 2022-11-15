from openerp import api, fields, models, exceptions
from datetime import datetime, timedelta

class PostDatedCheques(models.Model):
    _name = 'post.dated.cheques'
    _rec_name = 'cheque_number'

    partner_id = fields.Many2one('res.partner', string = 'Customer')
    date_received = fields.Date(string = 'Date Recieved')
    date_due = fields.Date(string = "Date Due")
    comment = fields.Text()
    banked = fields.Boolean()
    amount = fields.Float()
    reminder_sent = fields.Boolean()
    cheque_number = fields.Char(string='Cheque No.', required=True)
    voucher_id = fields.Many2one('account.voucher')

class PostDatedChequeReminders(models.Model):
    _name = 'post.dated.cheque.reminders'

    date = fields.Date()
    reminder_ids = fields.One2many('post.dated.cheque.reminder.lines', 'reminder_id')
    company_id = fields.Many2one('res.company')

    @api.model
    def scheduler_generate_pd_cheque_reminders(self):
        scheduler = self.env['post.dated.cheque.reminders'].create({
            'date':datetime.now(),
            'company_id':self.env.user.company_id.id
            })
        scheduler.generate_pd_cheque_reminders() 

    @api.one
    def generate_pd_cheque_reminders(self):
        today = datetime.now()
        cheques = self.env['post.dated.cheques'].search([
            ('banked','=',False),
            ('date_due', '<=', today)
            ])
        for cheque in cheques:
            self.env['post.dated.cheque.reminder.lines'].create({
                'reminder_id':self.id,
                'date_received':cheque.date_received,
                'date_due':cheque.date_due,
                'amount':cheque.amount,
                'banked':cheque.banked,
                'partner_id':cheque.partner_id.id
                })

        template = self.env.ref('accounting_autolamps.email_template_pd_cheque_reminder')
        
        self.env['email.template'].browse(
            template.id).send_mail(self.id)


class PostDatedChequeReminderLines(models.Model):
    _name = 'post.dated.cheque.reminder.lines'
    _inherit = 'post.dated.cheques'

    reminder_id = fields.Many2one('post.dated.cheque.reminders')