# -*- coding: utf-8 -*-
{
    "name": "Balance de Comprobación de Saldos",
    "version": "17.0.1.0.1",
    "summary": """
     """,
    "countries": ["sv"],
    "category": "Accounting/Localizations",
    "author": "Juan D. Collado Vasquez",
    "website": "https://tagre.pe",
    "depends": [
        'base',
        'tgr_reports_base',
        'web',
        "account",
        'tgr_l10n_sv',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_trial_balance_views.xml',
        'reports/trial_balance.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tgr_l10n_sv_trial_balance/static/src/xml/account_trial_balance.xml',
            'tgr_l10n_sv_trial_balance/static/src/js/account_trial_balance.js',
        ]
    },
    'application': True,
    'installable': True,
    'auto_install': False

}
