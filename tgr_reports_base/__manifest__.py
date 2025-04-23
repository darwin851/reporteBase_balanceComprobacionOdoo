{
    "name": "Reportes dinámicos Base",
    "version": "17.0.1.0.1",
    "summary": """
     """,
    "category": "Accounting/Localizations",
    "author": "Juan D. Collado Vasquez",
    "website": "https://tagre.pe",
    "depends": [
        "web", 'base',
    ],
    "data": [
    ],
    'assets': {
        'web.assets_backend': [
            'tgr_reports_base/static/src/components/**/*.js',
            'tgr_reports_base/static/src/components/**/*.xml',
            'tgr_reports_base/static/src/scss/tgr_reports_base.scss',
        ],
        'web.assets_unit_tests': [
            'tgr_reports_base/static/tests/components/**/*.js',
        ],
    },
    # "images": ["static/description/banner.png"],
    "price": 35.00,
    "currency": "USD",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
