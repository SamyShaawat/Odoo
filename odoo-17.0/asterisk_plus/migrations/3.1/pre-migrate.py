import logging
from odoo.tools.sql import rename_column

logger = logging.getLogger(__name__)

def migrate(cr, version):
    print('Migrating answered user...')
    try:
        rename_column(cr, 'asterisk_plus_call', 'called_user', 'answered_user')
    except Exception as e:
        logger.warning('Migration error: %s.', e)
        cr.rollback()
    print('Answered user column migrated.')

