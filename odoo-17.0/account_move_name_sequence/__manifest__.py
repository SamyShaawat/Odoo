# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Account Move Number Sequence",
    "category": "Accounting",
    "summary": "Generate journal entry number from sequence",
    "author": "Akretion,Vauxoo,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via", "moylop260", "frahikLV"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account", "branch", 'branch_sequence'
    ],
    "data": [
        "security/ir.model.access.csv",
        'security/multi_branch.xml',
        "views/account_journal.xml",
        "views/account_move.xml",
    ],
    'assets': {
    },
    # "post_init_hook": "create_journal_sequences",
    "installable": True,
    'version': '0.0.1',
    'application': True,
    'installable': True,
}
