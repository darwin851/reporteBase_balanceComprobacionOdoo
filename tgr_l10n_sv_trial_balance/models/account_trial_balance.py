from odoo import models, fields, api
from odoo.tools.misc import formatLang
from odoo.tools import date_range, float_round
from odoo.tools.date_utils import get_month
import json


class AccountTrialBalance(models.TransientModel):
    _name = 'l10n_sv.account.trial.balance'
    _inherit ='tgr.report.mixin'
    _description ='Balance de comprobacion de saldos [SV]'

    @api.model
    def view_report(self):
        account_ids = self.env['account.move.line'].search([]).mapped('account_id').ids
        journal_ids = self.env['account.journal'].search_read([], ['id'])
        journal_ids = [journal['id'] for journal in journal_ids]
        today = fields.Date.today()
        date_to = get_month(today)[1]
        date_from = get_month(today)[0]
        only_posted_moves = True
        hide_account_at_0 = True
        fy_start_date = today.replace(month=1, day=1)

        total_amount, accounts_data = self._get_data(
            account_ids, journal_ids, date_to, date_from, only_posted_moves, hide_account_at_0, fy_start_date)
        return self._get_report_data(accounts_data,total_amount,{'date_to':date_to,'date_from':date_from})
    
    def _get_report_data(self, accounts_data,total_amount,range):
        precision_digits=self.env.company.currency_id.decimal_places
        trial_balance = []
        for account_id in accounts_data.keys():
            accounts_data[account_id].update(
                {"initial_balance": total_amount[account_id]["initial_balance"],
                 "credit": total_amount[account_id]["credit"],
                 "debit": total_amount[account_id]["debit"],
                 "balance": total_amount[account_id]["balance"],
                 "ending_balance": total_amount[account_id]["ending_balance"],
                 "type": "account_type",
                 }
            )
        groups_data = self._get_groups_data(accounts_data, total_amount)
        trial_balance = list(groups_data.values())
        trial_balance += list(accounts_data.values())
        trial_balance = sorted(trial_balance, key=lambda k: k['code'])

        # Inicializar los totales para cada columna
        total_initial_deudor = 0
        total_initial_acreedor = 0
        total_cargos = 0
        total_abonos = 0
        total_ending_deudor = 0
        total_ending_acreedor = 0
        for item in trial_balance:
            counter = item['complete_code'].count('/')
            item['level'] = counter
            # Saldos iniciales
            if item['type']== 'account_type':
                if item['initial_balance'] > 0 :
                    total_initial_deudor += item['initial_balance']
                else:
                    total_initial_acreedor += item['initial_balance'] * -1
                
                # Cargos y abonos
                total_cargos += item['debit']
                total_abonos += item['credit']
                
                # Saldos finales
                if item['ending_balance'] > 0:
                    total_ending_deudor += item['ending_balance']
                else:
                    total_ending_acreedor += item['ending_balance'] * -1

        column={'name':'0.00','no_format':0.00,'figure_type':'monetary'}
        repor_data = {
            'journal_ids': self.env['account.journal'].search_read([], ['id','name']),
            'title':self._description,
            'header_0':[
                {'name':'','colspan':2},
                {'name':'Inicio del Periodo','colspan':2},
                {'name':'%s al %s'%(range['date_from'],range['date_to']),'colspan':2},
                {'name':'Fin del Periodo','colspan':2},
            ],
            'header':['Codigo','Descripción','Deudor','Acreedor','Cargos','Abonos','Deudor','Acreedor'],
            'lines':[{
                'id':'%s_%s'%(str(item['id']),item['type']),
                'code':item['code'],
                'name':item['name'],
                'level':item['level'],
                'visible':True,
                'columns':[
                    {'name':formatLang(self.env,item['initial_balance']),'figure_type':'monetary','no_format':float_round(item['initial_balance'],precision_digits)} if item['initial_balance']>0 else column ,
                    {'name':formatLang(self.env,item['initial_balance']*-1),'figure_type':'monetary','no_format':float_round(item['initial_balance'],precision_digits)*-1} if item['initial_balance']<0 else column,
                    {'name':formatLang(self.env,item['debit']),'figure_type':'monetary','no_format':float_round(item['debit'],precision_digits)} ,
                    {'name':formatLang(self.env,item['credit']),'figure_type':'monetary','no_format':float_round(item['credit'],precision_digits)} ,
                    {'name':formatLang(self.env,item['ending_balance']),'figure_type':'monetary','no_format':float_round(item['ending_balance'],precision_digits)} if item['ending_balance']>0 else column,
                    {'name':formatLang(self.env,item['ending_balance']*-1),'figure_type':'monetary','no_format':float_round(item['ending_balance'],precision_digits)*-1} if item['ending_balance']<0 else column ,
                ] 
                } for item in trial_balance
            ],
            'footer':{
                'name': 'Total',
                'columns':[
                    {'name': formatLang(self.env, total_initial_deudor), 'figure_type': 'monetary', 'no_format': float_round(total_initial_deudor, precision_digits)},
                    {'name': formatLang(self.env, total_initial_acreedor), 'figure_type': 'monetary', 'no_format': float_round(total_initial_acreedor, precision_digits)},
                    {'name': formatLang(self.env, total_cargos), 'figure_type': 'monetary', 'no_format': float_round(total_cargos, precision_digits)},
                    {'name': formatLang(self.env, total_abonos), 'figure_type': 'monetary', 'no_format': float_round(total_abonos, precision_digits)},
                    {'name': formatLang(self.env, total_ending_deudor), 'figure_type': 'monetary', 'no_format': float_round(total_ending_deudor, precision_digits)},
                    {'name': formatLang(self.env, total_ending_acreedor), 'figure_type': 'monetary', 'no_format': float_round(total_ending_acreedor, precision_digits)},
                ]
            }
        }
        return repor_data 


    def _get_accounts_data(self, accounts_ids):
        accounts = self.env["account.account"].browse(accounts_ids)
        accounts_data = {}
        for account in accounts:
            accounts_data.update(
                {
                    account.id: {
                        "id": account.id,
                        "code": account.code,
                        "name": account.name,
                        "hide_account": False,
                        "group_id": account.group_id.id,
                        "currency_id": account.currency_id.id,
                        "currency_name": account.currency_id.name,
                    }
                }
            )
        return accounts_data

    def _get_groups_data(self, accounts_data, total_amount):
        accounts_ids = list(accounts_data.keys())
        accounts = self.env["account.account"].browse(accounts_ids)
        account_group_relation = {}
        for account in accounts:
            accounts_data[account.id]["complete_code"] = (
                account.group_id.complete_code + " / " + account.code if account.group_id.id else "")
            if account.group_id.id:
                if account.group_id.id not in account_group_relation.keys():
                    account_group_relation.update({account.group_id.id: [account.id]})
                else:
                    account_group_relation[account.group_id.id].append(account.id)
        groups = self.env["account.group"].browse(account_group_relation.keys())
        groups_data = {}
        for group in groups:
            groups_data.update(
                {
                    group.id: {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "type": "group_type",
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "initial_balance": 0.0,
                        "credit": 0.0,
                        "debit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                    }
                }
            )
        for group_id in account_group_relation.keys():
            for account_id in account_group_relation[group_id]:
                groups_data[group_id]["initial_balance"] += total_amount[account_id][
                    "initial_balance"
                ]
                groups_data[group_id]["debit"] += total_amount[account_id]["debit"]
                groups_data[group_id]["credit"] += total_amount[account_id]["credit"]
                groups_data[group_id]["balance"] += total_amount[account_id]["balance"]
                groups_data[group_id]["ending_balance"] += total_amount[account_id][
                    "ending_balance"
                ]
        group_ids = list(groups_data.keys())
        groups_data = self._get_hierarchy_groups(
            group_ids,
            groups_data,
        )
        return groups_data

    @ api.model
    def get_filter_values(self, start_date, end_date, journal_ids):
        account_ids = self.env['account.move.line'].search([]).mapped('account_id').ids
        if not journal_ids:
            journal_ids = self.env['account.journal'].search_read([], ['id']) 
            journal_ids = [journal['id'] for journal in journal_ids]
        today = fields.Date.today()
        date_to = end_date
        date_from = start_date
        only_posted_moves = True
        hide_account_at_0 = True
        fy_start_date = today.replace(month=1, day=1)

        total_amount, accounts_data = self._get_data(
            account_ids, journal_ids, date_to, date_from, only_posted_moves, hide_account_at_0, fy_start_date)
        return self._get_report_data(accounts_data,total_amount,{'date_to':date_to,'date_from':date_from})

    def _get_hierarchy_groups(self, group_ids, groups_data):
        for group_id in group_ids:
            parent_id = groups_data[group_id]["parent_id"]
            while parent_id:
                if parent_id not in groups_data.keys():
                    group = self.env["account.group"].browse(parent_id)
                    groups_data[group.id] = {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "type": "group_type",
                        "initial_balance": 0.00,
                        "debit": 0.00,
                        "credit": 0.00,
                        "balance": 0.00,
                        "ending_balance": 0.0,
                    }
                acc_keys = ["debit", "credit", "balance"]
                acc_keys += ["initial_balance", "ending_balance"]
                for acc_key in acc_keys:
                    groups_data[parent_id][acc_key] += groups_data[group_id][acc_key]
                parent_id = groups_data[parent_id]["parent_id"]
        return groups_data

    @api.model
    def _compute_account_amount(self, total_amount, tb_initial_acc, tb_period_acc):
        for tb in tb_period_acc:
            acc_id = tb["account_id"][0]
            total_amount[acc_id] = self._prepare_total_amount(tb)
            total_amount[acc_id]["credit"] = tb["credit"]
            total_amount[acc_id]["debit"] = tb["debit"]
            total_amount[acc_id]["balance"] = tb["balance"]
            total_amount[acc_id]["initial_balance"] = 0.0
        for tb in tb_initial_acc:
            acc_id = tb["account_id"]
            if acc_id not in total_amount.keys():
                total_amount[acc_id] = self._prepare_total_amount(tb)
            else:
                total_amount[acc_id]["initial_balance"] = tb["balance"]
                total_amount[acc_id]["ending_balance"] += tb["balance"]
        return total_amount

    @api.model
    def _prepare_total_amount(self, tb):
        res = {
            "credit": 0.0,
            "debit": 0.0,
            "balance": 0.0,
            "initial_balance": tb["balance"],
            "ending_balance": tb["balance"],
        }
        return res

    @api.model
    def _get_data(self, account_ids, journal_ids, date_to, date_from, only_posted_moves, hide_account_at_0, fy_start_date):

        if not journal_ids:
            journal_ids = [journal['id']for journal in self.env['account.journal'].search_read([], ['id'])]
        today = fields.Date.today()
        if not date_to:
            date_to = today
        if not date_from:
            date_from = today.replace(day=1)

        accounts_domain = []
        if account_ids:
            accounts_domain += [('id', 'in', account_ids)]
            unaffected_earnings_account = False

        accounts = self.env['account.account'].search(accounts_domain)
        # ----------Saldos--------------------
        tb_initial_acc = []
        for account in accounts:
            tb_initial_acc.append({'account_id': account.id, 'balance': 0, 'amount_currency': 0})

        initial_domain_bs = self._get_initial_balances_bs_ml_domain(
            account_ids, journal_ids, date_from, only_posted_moves)

        # Saldos iniciales de cuentas del balance
        tb_initial_acc_bs = self.env['account.move.line'].read_group(
            domain=initial_domain_bs, fields=['account_id', 'balance', 'amount_currency:sum'], groupby=['account_id'])

        initial_domain_pl = self._get_initial_balances_pl_ml_domain(
            account_ids, journal_ids, date_from, only_posted_moves, fy_start_date)

        # Saldos iniciales de cuentas de ganancias y perdidas
        tb_initial_acc_pl = self.env['account.move.line'].read_group(
            domain=initial_domain_pl, fields=['account_id', 'balance', 'amount_currency:sum'], groupby=['account_id'])

        # Combina saldos iniciales de balance general y ganancias y perdidas
        tb_initial_acc_rg = tb_initial_acc_bs+tb_initial_acc_pl
        for account_rg in tb_initial_acc_rg:
            element = list(filter(lambda acc_dict: acc_dict['account_id']
                                  == account_rg['account_id'][0], tb_initial_acc))
            if element:
                element[0]['balance'] += account_rg['balance']
                element[0]['amount_currency'] += account_rg['amount_currency']
        if hide_account_at_0:
            tb_initial_acc = [p for p in tb_initial_acc if p['balance'] != 0]

        # ----------Periodo--------------------
        period_domain = self._get_period_ml_domain(
            account_ids, journal_ids, date_to, date_from, only_posted_moves)
        tb_period_acc = self.env['account.move.line'].read_group(
            domain=period_domain, fields=['account_id', 'debit', 'credit', 'balance', 'amount_currency:sum'], groupby=['account_id'])
        total_amount = {}
        total_amount = self._compute_account_amount(total_amount, tb_initial_acc, tb_period_acc)
        account_ids = list(total_amount.keys())
        accounts_data = self._get_accounts_data(account_ids)

        return total_amount, accounts_data

    def _get_initial_balances_bs_ml_domain(self, account_ids, journal_ids, date_from, only_posted_moves):

        accounts_domain = [
            ("include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        return domain

    def _get_initial_balances_pl_ml_domain(self, account_ids, journal_ids, date_from, only_posted_moves, fy_start_date):
        accounts_domain = [
            ("include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        # domain = [("date", "<", date_from), ("date", ">=", fy_start_date)]
        domain = [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        return domain

    @api.model
    def _get_period_ml_domain(self, account_ids, journal_ids,  date_to, date_from, only_posted_moves):
        domain = [
            ("display_type", "not in", ["line_note", "line_section"]),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        return domain
    
    @api.model
    def tgr_generate_excel_report(self, report_dada):

        return super().tgr_generate_excel_report(report_dada)


    
   
