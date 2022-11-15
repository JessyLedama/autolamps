# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    pd_cheque_ids = fields.One2many('post.dated.cheques','voucher_id', string="PD Cheques")

    @api.multi
    def send_receipt(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'accounting_autolamps', 'email_template_payment_receipt')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'email', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'account.voucher',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def print_receipt(self):
        return self.env['report'].get_action(
            self, 'accounting_autolamps.report_payment_receipt')

    @api.multi
    def proforma_voucher(self):
        for pd in self.pd_cheque_ids:
            pd.unlink()
        res = super(AccountVoucher,self).proforma_voucher()
        return res

    @api.onchange('pd_cheque_ids')
    def get_memo(self):
        self.reference = ",".join([pd.cheque_number for pd in self.pd_cheque_ids])
