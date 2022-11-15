# -*- coding: utf-8 -*-
from openerp import api, fields, models, exceptions
import json
from lxml import etree


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('credit_limit')
    def onchange_credit_limit(self):
        if not self.user_has_groups('autolamps_base.group_edit_credit_limit'):
            old_limit = self._origin.credit_limit
            new_limit = self.credit_limit
            if old_limit != new_limit:
                raise exceptions.AccessError(
                    'You don\'t have Rights to change the Credit Limit. '
                    'Contact Administrator!')

    @api.multi
    def write(self, vals):
        if 'credit_limit' in vals:
            if not self.user_has_groups('autolamps_base.group_edit_credit_limit'):
                old_limit = self.credit_limit
                new_limit = vals.get('credit_limit', 0)
                if old_limit != new_limit:
                    raise exceptions.AccessError(
                        'You don\'t have Rights to change the Credit Limit. '
                        'Contact Administrator!')
        res = super(ResPartner, self).write(vals)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )

        if view_type == 'form':
            # user = self.env['res.users'].search(
            #     [('id', '=', self.env.context.get('uid', False))])
            if not self.user_has_groups('account.group_account_invoice'):
            # if not user[0].return_percentage_modify:
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//field"):
                    if node.get('name') in ['payment_responsible_id','payment_next_action','payment_note']:
                        continue
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res
