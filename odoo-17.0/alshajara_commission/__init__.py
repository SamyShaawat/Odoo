from . import models


def create_journal(env):

        env['account.journal'].create( {
            'name': 'Commission',
            'code': 'COM',
            'type': 'general',
            'company_id': env.user.company_id.id,
            'currency_id': env.user.company_id.currency_id.id,
        })

