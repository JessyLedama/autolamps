import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class SaleCommission(models.Model):
    _inherit = "sale.commission"

    grace_period = fields.Integer(string="Grace Period", default=0, help="Days")