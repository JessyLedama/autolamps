import logging
from openerp import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    target = fields.Float(string='Agent Target', default=0.00)
    sale_agent_line_ids = fields.One2many('sale.order.line.agent', 'agent', string='Sale Agent Lines')
    invoice_agent_line_ids = fields.One2many('account.invoice.line.agent', 'agent', string='Invoice Agent Lines')
    settlement_ids = fields.One2many('sale.commission.settlement', 'agent', string='Settlements')
    generated_invoice_ids = fields.One2many('account.invoice', 'partner_id', string='Generated Invoices')
    
    @api.depends('settlement_ids', 'settlement_ids.invoice')
    def _compute_generated_invoice_ids(self):
        for record in self:
            if record.agent and record.settlement_ids:
                record.generated_invoice_ids = record.settlement_ids.mapped('invoice')
            else:
                record.generated_invoice_ids = False

    @api.multi
    def action_view_sale_agent_lines(self):
        form_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_form', False)
        tree_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_tree', False)
        search_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_search', False)
        domain = []

        if len(self.sale_agent_line_ids)>0:
            domain = [('agent','=',self.id)]
            return { 
                'name': "Agent Sale Commissions",
                'view_mode': 'tree,form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'sale.order.line.agent',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': domain,
                'search_view_id': search_view_ref and search_view_ref.id or False,
                'views': [(tree_view_ref and tree_view_ref.id or False, 'tree'),
                            (form_view_ref and form_view_ref.id or False, 'form'),
                        ],
            }
        else:
            raise exceptions.Warning(_("No agent lines for this agent."))

    @api.multi
    def action_view_invoice_agent_lines(self):
        form_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_form', False)
        tree_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_tree', False)
        search_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_search', False)
        _logger.info("tree view %s" % tree_view_ref.id)
        domain = []
        if len(self.invoice_agent_line_ids)>0:
            domain = [('agent','=',self.id)]
            return { 
                'name': "Agent Invoice Commissions",
                'view_mode': 'tree,form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'account.invoice.line.agent',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': domain,
                'search_view_id': search_view_ref and search_view_ref.id or False,
                'views': [(tree_view_ref and tree_view_ref.id or False, 'tree'),
                    (form_view_ref and form_view_ref.id or False, 'form'),
                        ],
            }
        else:
            raise exceptions.Warning(_("No agent lines for this agent."))

    @api.multi
    def action_view_settlements(self):
        domain = []
        if len(self.settlement_ids)>0:
            domain = [('agent','=',self.id)]
            return { 
                'name': "Agent Settlements",
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.commission.settlement',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': domain,
            }
        else:
            raise exceptions.Warning(_("No settlements for this agent."))

    @api.multi
    def action_view_agent_invoices(self):
        domain = []
        if len(self.generated_invoice_ids)>0:
            domain = [('partner_id','=',self.id)]
            return { 
                'name': "Agent Invoices",
                'view_mode': 'tree,form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': domain,
            }
        else:
            raise exceptions.Warning(_("No invoices for this agent."))

    def get_invoices_by_date(self, date_from, date_to):
        # TODO: Test this
        return self.invoice_agent_line_ids.filtered(lambda line: line.invoice_date >= date_from and line.invoice_date <= date_to).mapped('invoice')

    def get_invoice_sale_orders(self, invoice):
        # TODO: Test this
        commission_sale_orders = set(self.sale_agent_line_ids.mapped('sale_order_id'))
        invoice_sale_orders = set(invoice.mapped('sale_ids'))
        # TODO: What is the output type of a set intersection?
        sale_orders = list(commission_sale_orders.intersection(invoice_sale_orders))
        return ','.join([so.name for so in sale_orders])

    def get_total_commission_by_invoice(self, invoice):
        self.invoice_agent_line_ids.filtered(lambda line: line.invoice.id == invoice.id)
        return sum(line.amount for line in agent_lines)

    def get_settlements_by_invoice(self, invoice):
        settlements = self.settlement_ids.filtered(lambda s: invoice.id in s.mapped('lines.invoice.id'))
        _logger.info("settlements %s" % settlements)
        return settlements.name
