from odoo import fields, models

class AccessList(models.Model):
    _name = 'asterisk_plus.access_list'
    _description = 'Access List'

class ChannelMessage(models.Model):
    _name = 'asterisk_plus.channel_message'
    _description = 'Channel Message'

class Ban(models.Model):
    _name = 'asterisk_plus.access_ban'    
    _description = 'Access Ban'

class AsteriskConf(models.Model):
    _name = 'asterisk_plus.conf'    
    _description = 'Conf'

class SaltJob(models.Model):
    _name = 'asterisk_plus.salt_job'
    _description = 'Salt Job'
