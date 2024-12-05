from odoo import fields,models,api
from odoo.exceptions import ValidationError
import random


class NewReferral(models.Model):
    _name = 'new.referral'
    _description = 'New Referral'
    _inherit = 'mail.thread'
    _sql_constraints = [
        ('phone_unique', 'unique(phone)', 'This phone number is already used.'),
        ('email_unique', 'unique(email)', 'This email is already used.'),
    ]

    name = fields.Char(string='Opportunity', compute='_compute_name', store=True)
    customer_name = fields.Char(string='Customer', required=True)
    phone = fields.Char(string='Phone')
    course_id = fields.Many2one('product.product', string='Course', required=True)
    email = fields.Char(string='Email')
    state = fields.Selection(selection=[('draft', 'Draft'), ('submitted', 'Submitted')], string='State',
                             default='draft', tracking=True)
    location = fields.Char(string='Location')
    user = fields.Many2one('res.users', string='Request Owner', default=lambda self: self.env.user, readonly=True)


    @api.depends('customer_name')
    def _compute_name(self):
        for rec in self:
            if rec.customer_name:
                rec.name = f"Referral Lead - {rec.customer_name}"
            else:
                rec.name = "Referral Lead"

    # @api.constrains('phone', 'email')
    # def _check_phone_email_in_crm_lead(self):
    #     for record in self:
    #         # Check for duplicate phone in crm.lead
    #         if record.phone:
    #             crm_lead_with_same_phone = self.env['crm.lead'].search([('phone', '=', record.phone)], limit=1)
    #             if crm_lead_with_same_phone:
    #                 raise ValidationError(f"The phone number {record.phone} is already used in CRM Leads.")
    #
    #         # Check for duplicate email in crm.lead
    #         if record.email:
    #             crm_lead_with_same_email = self.env['crm.lead'].search([('email_from', '=', record.email)], limit=1)
    #             if crm_lead_with_same_email:
    #                 raise ValidationError(f"The email address {record.email} is already used in CRM Leads.")

    def action_submit(self):
        team = self.env['crm.team'].search([('name', '=', 'Sales Team Mavelikkara')], limit=1)
        print("team",team.member_ids)
        employee = self.env['hr.employee'].search([('user_id', '=', self.user.id)])
        for record in self:
            # Check if a partner already exists with the same name or email
            partner = self.env['res.partner'].search(
                ['|', ('name', '=', record.customer_name), ('email', '=', record.email)], limit=1
            )

            # Create a new partner if none exists
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': record.customer_name,
                    'phone': record.phone,
                    'email': record.email,
                })
            lead = self.env['crm.lead'].sudo().create({
                'name': record.name,
                'partner_id': partner.id,
                'referred_by': employee.id,
                'phone': record.phone,
                'team_id': team.id,
                'course_id': record.course_id.id,
                'city': record.location,
                'email_from': record.email,
                'user_id': self._get_salesperson_for_referral()
            })
            record.state = 'submitted'
            return lead

    def _get_salesperson_for_referral(self):
        team = self.env['crm.team'].search([('name', '=', 'Sales Team Mavelikara')], limit=1)
        print(team.member_ids)
        if team:
            sales_team_users = team.member_ids
            if sales_team_users:
                random_user = random.choice(sales_team_users)
                return random_user.user_id.id
        return False











