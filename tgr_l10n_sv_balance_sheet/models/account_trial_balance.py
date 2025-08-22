# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.tools.misc import formatLang
from odoo.tools import float_round
from odoo.tools.date_utils import get_month

_logger = logging.getLogger(__name__)

BALANCE_SHEET_TYPES = [
    'asset_current',
    'asset_non_current',
    'asset_fixed',
    'asset_prepayments',
    'asset_cash',
    'asset_receivable',
    'liability_current',
    'liability_non_current',
    'equity',
    'equity_unaffected',
]


class AccountTrialBalance(models.TransientModel):
    _name = 'l10n_sv.account.trial.balance.sheet'
    _inherit = 'tgr.report.mixin'
    _description = 'Balance General [SV]'

    # -------------------------------------------------------------------------
    # ENTRADA DEL REPORTE (con valores por defecto si no vienen options)
    # -------------------------------------------------------------------------
    @api.model
    def view_report(self, options=None):
        options = options or {}

        # Fechas por defecto: mes actual
        today = fields.Date.today()
        df, dt = get_month(today)
        date_from = options.get("date_from") or df
        date_to = options.get("date_to") or dt

        # Cuentas por defecto: todas las de balance
        account_ids = options.get("account_ids")
        if not account_ids:
            account_ids = self.env['account.account'].search([
                ('account_type', 'in', BALANCE_SHEET_TYPES)
            ]).ids

        # Diarios por defecto: todos
        journal_ids = options.get("journal_ids")
        if not journal_ids:
            journal_ids = self.env['account.journal'].search([]).ids

        only_posted_moves = bool(options.get("only_posted_moves", True))
        hide_account_at_0 = bool(options.get("hide_account_at_0", False))

        fy_base = fields.Date.to_date(date_from) if date_from else today
        fy_start_date = options.get("fy_start_date") or fy_base.replace(month=1, day=1)

        total_amount, accounts_data = self._get_data(
            account_ids, journal_ids, date_to, date_from,
            only_posted_moves, hide_account_at_0, fy_start_date
        )

        _logger.info("✅ Total cuentas procesadas: %s", len(accounts_data))
        return self._get_report_data(
            accounts_data,
            total_amount,
            {'date_to': date_to, 'date_from': date_from}
        )

    # -------------------------------------------------------------------------
    # FILTROS (llamado desde el front)
    # -------------------------------------------------------------------------
    @api.model
    def get_filter_values(self,
                          start_date=None,
                          end_date=None,
                          journal_ids=None,
                          only_posted_moves=True,
                          hide_account_at_0=False,
                          account_ids=None):

        def _norm_ids(seq):
            if not seq:
                return []
            out = []
            for it in seq:
                if isinstance(it, (int, float)):
                    out.append(int(it))
                elif isinstance(it, dict) and "id" in it:
                    out.append(int(it["id"]))
            return out

        journal_ids = _norm_ids(journal_ids)
        if not account_ids:
            account_ids = self.env['account.account'].search([
                ('account_type', 'in', BALANCE_SHEET_TYPES)
            ]).ids
        else:
            account_ids = _norm_ids(account_ids)

        today = fields.Date.today()
        if not start_date or not end_date:
            df, dt = get_month(today)
            start_date = start_date or df
            end_date = end_date or dt

        fy_base = fields.Date.from_string(start_date) if start_date else today
        fy_start_date = fy_base.replace(month=1, day=1)

        total_amount, accounts_data = self._get_data(
            account_ids, journal_ids, end_date, start_date,
            bool(only_posted_moves), bool(hide_account_at_0), fy_start_date
        )

        return self._get_report_data(
            accounts_data,
            total_amount,
            {'date_to': end_date, 'date_from': start_date}
        )

    # -------------------------------------------------------------------------
    # OBTENER DATOS CRUDOS (queries + armado dicts)
    #   Devuelve:
    #     - total_amount: {account_id: {...saldos...}}
    #     - accounts_data: {account_id: {code,name,account_type,..., ending_balance}}
    # -------------------------------------------------------------------------
    @api.model
    def _get_data(self, account_ids, journal_ids, date_to, date_from,
                  only_posted_moves, hide_account_at_0, fy_start_date):

        aml = self.env['account.move.line']

        # --- saldos iniciales (hasta < date_from) ---
        init_domain = self._get_initial_balances_bs_ml_domain(
            account_ids, journal_ids, date_from, only_posted_moves
        )
        init_rows = aml.read_group(
            domain=init_domain,
            fields=['account_id', 'balance:sum'],
            groupby=['account_id'],
        )
        init_by_id = {}
        for r in init_rows:
            aid = r.get('account_id')
            aid = aid[0] if isinstance(aid, (list, tuple)) else aid
            if aid:
                init_by_id[aid] = {'balance': float(r.get('balance', 0.0) or 0.0)}
        _logger.info("read_group iniciales -> filas: %s", len(init_rows))

        # --- periodo (date_from..date_to) ---
        period_domain = self._get_period_ml_domain(
            account_ids, journal_ids, date_to, date_from, only_posted_moves
        )
        period_rows = aml.read_group(
            domain=period_domain,
            fields=['account_id', 'debit:sum', 'credit:sum', 'balance:sum'],
            groupby=['account_id'],
        )
        period_by_id = {}
        for r in period_rows:
            aid = r.get('account_id')
            aid = aid[0] if isinstance(aid, (list, tuple)) else aid
            if not aid:
                continue
            debit = float(r.get('debit', 0.0) or 0.0)
            credit = float(r.get('credit', 0.0) or 0.0)
            bal = r.get('balance')
            bal = float(bal if bal is not None else (debit - credit))
            period_by_id[aid] = {'debit': debit, 'credit': credit, 'balance': bal}
        _logger.info("read_group periodo -> filas: %s", len(period_rows))

        # --- acumular saldos finales por cuenta ---
        total_amount = {}
        # Usa dicts {id: {...}} para no chocar con .keys()
        all_ids = set(account_ids) | set(init_by_id.keys()) | set(period_by_id.keys())
        for acc_id in all_ids:
            init = init_by_id.get(acc_id, {})
            per = period_by_id.get(acc_id, {})
            initial_balance = float(init.get("balance", 0.0) or 0.0)
            debit = float(per.get("debit", 0.0) or 0.0)
            credit = float(per.get("credit", 0.0) or 0.0)
            period_balance = float(per.get("balance", debit - credit) or 0.0)
            ending_balance = initial_balance + period_balance
            total_amount[acc_id] = {
                "initial_balance": initial_balance,
                "debit": debit,
                "credit": credit,
                "balance": period_balance,
                "ending_balance": ending_balance,
            }

            _logger.info("💰 Cuenta calculada: id=%s inicial=%s debit=%s credit=%s balance=%s ending=%s",
                         acc_id, initial_balance, debit, credit, period_balance, ending_balance)

        # --- decidir qué cuentas mostrar ---
        precision = self.env.company.currency_id.decimal_places
        if hide_account_at_0:
            render_ids = [
                aid for aid in all_ids
                if float_round(abs(total_amount.get(aid, {}).get('ending_balance', 0.0)), precision) != 0.0
            ]
        else:
            render_ids = list(all_ids)

        # --- metadata de cuentas a renderizar y mezclar saldos ---
        accounts_meta = self._get_accounts_data(render_ids)  # dict {id: meta}
        for aid in list(accounts_meta.keys()):  # ✅ hacemos copia de las llaves
            acc = accounts_meta[aid]

            if acc.get("type") != "account":
                continue

            grp_id = acc.get("group_id")
            grp = self.env["account.group"].browse(grp_id) if grp_id else False
            while grp and grp.exists():
                gid = grp.id
                if gid not in accounts_meta:
                    accounts_meta[gid] = {
                        "id": gid,
                        "code": grp.code_prefix_start,
                        "name": grp.name,
                        "type": "group",
                        "initial_balance": 0.0,
                        "debit": 0.0,
                        "credit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                        "parent_code": grp.parent_id.code_prefix_start if grp.parent_id else None,
                        "group_id": grp.parent_id.id if grp.parent_id else None,
                    }
                accounts_meta[gid]["initial_balance"] += acc.get("initial_balance", 0.0) or 0.0
                accounts_meta[gid]["debit"] += acc.get("debit", 0.0) or 0.0
                accounts_meta[gid]["credit"] += acc.get("credit", 0.0) or 0.0
                accounts_meta[gid]["balance"] += acc.get("balance", 0.0) or 0.0
                accounts_meta[gid]["ending_balance"] += acc.get("ending_balance", 0.0) or 0.0

                grp = grp.parent_id

        # for aid in list(accounts_meta.keys()):
        #     ta = total_amount.get(aid, {
        #         "initial_balance": 0.0, "debit": 0.0, "credit": 0.0,
        #         "balance": 0.0, "ending_balance": 0.0
        #     })
        #     accounts_meta[aid].update(ta)

        return total_amount, accounts_meta  # dicts

    # -------------------------------------------------------------------------
    # CONVIERTE A PAYLOAD PARA EL FRONT (assets/liabilities, totales)
    # -------------------------------------------------------------------------
    def _get_report_data(self, accounts_data, total_amount, rnge):
        precision = self.env.company.currency_id.decimal_places

        # Asegurar que cada cuenta tenga sus importes + tipo
        for aid in list(accounts_data):
            ta = total_amount.get(aid, {
                "initial_balance": 0.0, "credit": 0.0, "debit": 0.0,
                "balance": 0.0, "ending_balance": 0.0
            })
            accounts_data[aid].update(ta)
            accounts_data[aid]["type"] = "account"

        # Agregar los grupos
        groups_data = self._get_groups_data(accounts_data, total_amount)

        for acc in accounts_data.values():
            parent_code = acc.get("parent_code")
            while parent_code:
                if parent_code in groups_data:
                    groups_data[parent_code]["ending_balance"] += acc["ending_balance"]
                    groups_data[parent_code]["balance"] += acc["balance"]
                    parent_code = groups_data[parent_code].get("parent_code")
                else:
                    parent_code = None

        # Unificar (grupos + cuentas) y ordenar
        rows = list(groups_data.values()) + list(accounts_data.values())
        rows.sort(key=lambda r: (r.get("code") or r.get("code") or ""))

        def level_of(item):
            return (item.get("complete_code") or "").count("/")

        def is_asset(item):
            if item.get("type") == "account":
                at = (item.get("account_type") or "")
                return at.startswith('asset')
            code = (item.get("code") or item.get("complete_code") or "").strip()
            if code.startswith("1"):
                return True
            if code.startswith(("2", "3")):
                return False
            name = (item.get("name") or "").lower()
            return "activo" in name

        assets, liabilities = [], []
        total_assets, total_liab = 0.0, 0.0
        show_zero = False  # cambiar a False si quieres ocultar ceros en la grilla

        for it in rows:
            amount = it.get("ending_balance", 0.0) or 0.0

            if it.get("type") == "account":
                at = (it.get("account_type") or "")
                if at in ("liability_current", "liability_non_current", "equity", "income"):
                    amount = -amount

            if not show_zero and float_round(abs(amount), precision) == 0.0:
                continue

            line = {
                "id": f"{it['id']}_{it.get('type', '')}",
                "code": it.get("code") or "",
                "name": it.get("name") or "",
                "level": level_of(it),
                "type": it.get("type"),
                "amount": amount,
                "amount_fmt": formatLang(self.env, amount),
                "note": "",
            }

            if is_asset(it):
                assets.append(line)
                if it.get("type") == "account":
                    total_assets += abs(amount)
            else:
                liabilities.append(line)
                if it.get("type") == "account":
                    total_liab += abs(amount)

        _logger.info("🧱 Filas para TgrBalanceSheet: assets=%s, liabilities=%s", len(assets), len(liabilities))
        _logger.info("Σ Totales: Activo=%s  Pasivo+Patr=%s", total_assets, total_liab)

        return {
            "title": self._description,
            "date_from": rnge["date_from"],
            "date_to": rnge["date_to"],
            "assets": assets,
            "liabilities": liabilities,
            "totals": {
                "assets": {"value": total_assets, "text": formatLang(self.env, total_assets)},
                "liabilities": {"value": total_liab, "text": formatLang(self.env, total_liab)},
            },
            "journals": self.env["account.journal"].search_read([], ["id", "name"]),
        }

    # -------------------------------------------------------------------------
    # GRUPOS CONTABLES
    # -------------------------------------------------------------------------
    def _get_groups_data(self, accounts_data, total_amount):
        accounts_ids = list(accounts_data.keys())
        accounts = self.env["account.account"].browse(accounts_ids)

        account_group_relation = {}
        for account in accounts:
            accounts_data[account.id]["complete_code"] = (
                f"{account.group_id.complete_code} / {account.code}" if account.group_id.id else account.code
            )
            if account.group_id.id:
                account_group_relation.setdefault(account.group_id.id, []).append(account.id)

        groups = self.env["account.group"].browse(list(account_group_relation.keys()))
        groups_data = {}

        for group in groups:
            groups_data[group.id] = {
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

        for group_id, acc_ids in account_group_relation.items():
            for account_id in acc_ids:
                ta = total_amount.get(account_id)
                if not ta:
                    continue
                groups_data[group_id]["initial_balance"] += ta["initial_balance"]
                groups_data[group_id]["debit"] += ta["debit"]
                groups_data[group_id]["credit"] += ta["credit"]
                groups_data[group_id]["balance"] += ta["balance"]
                groups_data[group_id]["ending_balance"] += ta["ending_balance"]

        # Propagar importes a padres
        group_ids = list(groups_data.keys())
        groups_data = self._get_hierarchy_groups(group_ids, groups_data)
        return groups_data

    def _get_hierarchy_groups(self, group_ids, groups_data):
        for group_id in group_ids:
            parent_id = groups_data[group_id]["parent_id"]
            while parent_id:
                if parent_id not in groups_data:
                    group = self.env["account.group"].browse(parent_id)
                    groups_data[parent_id] = {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "type": "group_type",
                        "initial_balance": 0.0,
                        "debit": 0.0,
                        "credit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                    }
                for key in ("initial_balance", "debit", "credit", "balance", "ending_balance"):
                    groups_data[parent_id][key] += groups_data[group_id][key]
                parent_id = groups_data[parent_id]["parent_id"]
        return groups_data

    # -------------------------------------------------------------------------
    # DOMINIOS
    # -------------------------------------------------------------------------
    def _get_initial_balances_bs_ml_domain(self, account_ids, journal_ids, date_from, only_posted_moves):
        domain = [("date", "<", date_from)]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        domain += [("account_id.account_type", "in", BALANCE_SHEET_TYPES)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        domain += [("display_type", "not in", ["line_note", "line_section"])]
        domain += [("parent_state", "=", "posted")] if only_posted_moves else [
            ("parent_state", "in", ["posted", "draft"])]
        return domain

    # def _get_initial_balances_pl_ml_domain(self, account_ids, journal_ids, date_from, only_posted_moves, fy_start_date):
    #     # no usado aquí
    #     domain = [("date", "<", date_from)]
    #     if account_ids:
    #         domain += [("account_id", "in", account_ids)]
    #     if journal_ids:
    #         domain += [("journal_id", "in", journal_ids)]
    #     domain += [("display_type", "not in", ["line_note", "line_section"])]
    #     domain += [("parent_state", "=", "posted")] if only_posted_moves else [("parent_state", "in", ["posted", "draft"])]
    #     return domain

    def _get_period_ml_domain(self, account_ids, journal_ids, date_to, date_from, only_posted_moves):
        domain = [
            ("display_type", "not in", ["line_note", "line_section"]),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("account_id.account_type", "in", BALANCE_SHEET_TYPES),
        ]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        domain += [("parent_state", "=", "posted")] if only_posted_moves else [
            ("parent_state", "in", ["posted", "draft"])]
        return domain

    # -------------------------------------------------------------------------
    # EXCEL
    # -------------------------------------------------------------------------
    @api.model
    def tgr_generate_excel_report(self, report_dada):
        return super().tgr_generate_excel_report(report_dada)

    # -------------------------------------------------------------------------
    # METADATA DE CUENTAS
    # -------------------------------------------------------------------------
    def _get_accounts_data(self, accounts_ids):
        accounts = self.env["account.account"].browse(accounts_ids)
        accounts_data = {}
        for account in accounts:
            complete_code = (
                f"{account.group_id.complete_code} / {account.code}"
                if account.group_id else account.code
            )
            accounts_data[account.id] = {
                "id": account.id,
                "code": account.code,
                "name": account.name,
                "hide_account": False,
                "group_id": account.group_id.id,
                "currency_id": account.currency_id.id,
                "currency_name": account.currency_id.name,
                "account_type": account.account_type,
                "complete_code": complete_code,
            }
        return accounts_data
