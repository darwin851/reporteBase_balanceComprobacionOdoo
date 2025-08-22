# -*- coding: utf-8 -*-
{
    "name": "Balance General SV FUNPRES",
    "version": "17.0.1.0.1",
    "summary": """
     """,
    "countries": ["sv"],
    "category": "Accounting/Localizations",
    "author": "Darwin González",
    "website": "",
    "depends": [
        'base',
        'tgr_reports_base',
        'web',
        "account",
        'l10n_sv',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_balance_sheet_views.xml',
        'reports/balance_sheet.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tgr_l10n_sv_balance_sheet/static/src/xml/account_balance_sheet.xml',
            'tgr_l10n_sv_balance_sheet/static/src/js/account_balance_sheet.js',
        ]
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    "license": "LGPL-3",

}
