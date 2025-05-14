import base64
import io
from datetime import datetime, timedelta
import requests
import sys
import time
from urllib.parse import urljoin
import uuid
import logging
from odoo import models, fields, api, _, tools, release, SUPERUSER_ID
from odoo.exceptions import ValidationError
from .server import debug
from .settings import MODULE_NAME

logger = logging.getLogger(__name__)


class Recording(models.Model):
    _name = 'asterisk_plus.recording'
    _inherit = 'mail.thread'
    _description = 'Recording'
    _rec_name = 'id'
    _order = 'id desc'

    uniqueid = fields.Char(size=64, index=True, readonly=True)
    transcript_short = fields.Char(compute='_get_transcript_short')
    call = fields.Many2one('asterisk_plus.call', ondelete='set null', readonly=True)
    called_users = fields.Many2many(related='call.called_users')
    channel = fields.Many2one('asterisk_plus.channel', ondelete='set null', readonly=True)
    partner = fields.Many2one('res.partner', ondelete='set null', readonly=True)
    calling_user = fields.Many2one('res.users', ondelete='set null', readonly=True)
    answered_user = fields.Many2one('res.users', ondelete='set null', readonly=True)
    calling_number = fields.Char(index=True, readonly=True)
    calling_name = fields.Char(compute='_get_calling_name', readonly=True)
    called_number = fields.Char(index=True, readonly=True)
    answered = fields.Datetime(index=True, readonly=True)
    duration = fields.Integer(related='call.duration', store=True)
    duration_human = fields.Char(related='call.duration_human', store=True)
    recording_widget = fields.Char(compute='_get_recording_widget',
                                   string='Recording')
    recording_filename = fields.Char(readonly=True, index=True)
    recording_data = fields.Binary(attachment=False, readonly=True, string=_('Download'))
    recording = fields.Binary(compute='_get_recording')
    recording_attachment = fields.Binary(attachment=True, readonly=True, string=_('Download'))
    file_path = fields.Char(readonly=True)
    tags = fields.Many2many('asterisk_plus.tag',
                            relation='asterisk_plus_recording_tag',
                            column1='tag', column2='recording')
    keep_forever = fields.Selection([
        ('no', 'Archivable'),
        ('yes', 'Keep Forever')
    ], default='no', tracking=True)
    icon = fields.Html(compute='_get_icon', string='I')
    ############## TRANSCRIPTION FIELDS ######################################
    transcript = fields.Text()
    transcription_token = fields.Char()
    transcription_error = fields.Char()
    transcription_price = fields.Char()
    summary = fields.Text()
    ##########################################################################

    def _get_recording(self):
        for rec in self:
            rec.recording = rec.recording_data if rec.recording_data else rec.recording_attachment

    def _get_transcript_short(self):
        for rec in self:
            if rec.transcript:
                rec.transcript_short = rec.transcript
            else:
                rec.transcript_short = ''

    @api.model
    def create(self, vals):
        rec = super(Recording, self.with_context(
            mail_create_nosubscribe=True, mail_create_nolog=True)).create(vals)
        # Commit to the database as recordings are created by the Agent.
        if self.env['asterisk_plus.settings'].sudo().get_param('transcript_calls'):
            rec.get_transcript(fail_silently=True)
        return rec

    def write(self, vals):
        if vals.get("tags"):
            # Get tags to be notified when attached to recording
            present_tags = self.tags.ids
            new_tags = vals.get("tags")
            tags_to_notify = set(new_tags[0][2]) - set(present_tags)
            msg = "Tag attached to recording {}".format(self.uniqueid)
            for tag in tags_to_notify:
                self.env['asterisk_plus.tag'].browse(
                    tag).sudo().message_post(
                        subject=_('Tag attached to recording'),
                        body=msg)
        res = super(Recording, self).write(vals)

    def _get_recording_widget(self):
        for rec in self:
            recording_source = 'recording_data' if rec.recording_data else 'recording_attachment'
            rec.recording_widget = '<audio id="sound_file" preload="auto" ' \
                'controls="controls"> ' \
                '<source src="/web/content?model=asterisk_plus.recording&' \
                'id={recording_id}&filename={filename}&field={source}&' \
                'filename_field=recording_filename&download=True" />' \
                '</audio>'.format(
                    recording_id=rec.id,
                    filename=rec.recording_filename,
                    source=recording_source)

    @api.model
    def save_call_recording(self, channel):
        """Save call recording."""
        recording_channel_data = self.env['asterisk_plus.channel_data'].search(
            [('channel', '=', channel.id), ('key', '=', 'recording_file_path')], limit=1)
        if not recording_channel_data:
            debug(self, 'Recording file not specified for channel {}, id: {}'.format(
                channel.channel, channel.id))
            return False
        recording_file_path = recording_channel_data.value
        debug(self, 'Channel %s getting recording from %s' % (
            channel.channel, recording_file_path))
        kwargs = {}
        mp3_encode = self.env['asterisk_plus.settings'].sudo().get_param(
            'use_mp3_encoder')
        if mp3_encode:
            kwargs['file_format'] = 'mp3'
            kwargs['mp3_bitrate'] = int(self.env['asterisk_plus.settings'].sudo().get_param(
                'mp3_encoder_bitrate', default=96))
            kwargs['mp3_quality'] = int(self.env['asterisk_plus.settings'].sudo().get_param(
                'mp3_encoder_quality', default=4))
        channel.server.local_job(
            fun='recording.get_file',
            args=recording_file_path,
            kwargs=kwargs,
            res_model='asterisk_plus.recording',
            res_method='upload_recording',
            pass_back={'channel_id': channel.id, 'file_path': recording_file_path},
            raise_exc=False,
        )
        return True

    @api.model
    def upload_recording(self, data, channel_id=None, file_path=None):
        """Upload call recording to Odoo."""
        if not isinstance(data, dict):
            debug(self, 'Upload recording error: {}'.format(data))
            return False
        if data.get('error'):
            logger.error('Cannot get call recoding: %s', data['error'])
            return False
        file_data = data.get('file_data')
        file_name = data.get('file_name')
        channel = self.env['asterisk_plus.channel'].browse(channel_id)
        debug(self, 'Call recording upload for channel {}'.format(
            channel.channel))
        vals = {
            'uniqueid': channel.uniqueid,            
            'recording_filename': data['file_name'],
            'call': channel.call.id,
            'channel': channel.id,
            'partner': channel.call.partner.id,
            'calling_user': channel.call.calling_user.id,
            'answered_user': channel.call.answered_user.id,
            'calling_number': channel.call.calling_number,
            'called_number': channel.call.called_number,
            'answered': channel.call.answered,
            'file_path': file_path,
        }
        if self.env['asterisk_plus.settings'].sudo().get_param(
                'recording_storage') == 'filestore':
            vals['recording_attachment'] = file_data
        else:
            vals['recording_data'] = file_data
        # Create a recording
        rec = self.create(vals)
        return True

    @api.model
    def delete_recordings(self):
        """Cron job to delete calls recordings.
        """
        days = self.env[
            'asterisk_plus.settings'].get_param('recordings_keep_days')
        expire_date = datetime.utcnow() - timedelta(days=int(days))
        expired_recordings = self.env['asterisk_plus.recording'].search([
            ('keep_forever', '=', 'no'),
            ('answered', '<=', expire_date.strftime('%Y-%m-%d %H:%M:%S'))
        ])
        logger.info('Expired {} recordings'.format(len(expired_recordings)))
        expired_recordings.unlink()

    def _get_icon(self):
        for rec in self:
            if rec.keep_forever == 'yes':
                rec.icon = '<span class="fa fa-floppy-o"></span>'
            else:
                rec.icon = ''

    def prepare_transcription_content(self):
        data = {
            'file_name': self.recording_filename,
            'content': self.recording.decode(),
        }
        return data

    ############## TRANSCRIPTION METHODS #####################################

    def get_transcript(self, fail_silently=False):
        self.ensure_one()
        url = urljoin(self.env['%s.settings' % MODULE_NAME].sudo().get_param('api_url'),
            'transcription')
        self.transcription_token = str(uuid.uuid4())
        self.env.cr.commit()
        try:
            data = self.prepare_transcription_content()
            data.update({
                'summary_prompt': self.env['%s.settings' % MODULE_NAME].sudo().get_param('summary_prompt'),
                'callback_url': urljoin(
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    '/{}/transcript/{}'.format(MODULE_NAME, self.id)),
            'transcription_token': self.transcription_token,
            'notify_uid': self.env.user.id,
            })
            res = requests.post(url,
                json=data,
                headers={
                    'x-instance-uid': self.env['%s.settings' % MODULE_NAME].sudo().get_param('instance_uid'),
                    'x-api-key': self.env['ir.config_parameter'].sudo().get_param('odoopbx.api_key')
                })
            if not res.ok:
                self.transcription_error = res.text
                if not fail_silently:
                    raise ValidationError(res.text)
            logger.info('Transcription request has been sent.')
        except Exception as e:
            logger.exception('Transcription error: %s', e)
            if not fail_silently:
                raise ValidationError('Transcription error: %s' % e)

    def update_transcript(self, data):
        # Update transcription and also erase access token.
        self.ensure_one()
        transcription_price = data.get('transcription_price')
        if transcription_price:
            # Round
            transcription_price = round(transcription_price, 2)
        vals = {
            'transcript': data.get('transcript'),
            'transcription_price': str(transcription_price),
            'summary': data.get('summary'),
            # Reset the token
            'transcription_token': False,
            'transcription_error': data.get('transcription_error')
        }
        self.write(vals)        
        # Reload views when transcription has come.
        self.env['%s.settings' % MODULE_NAME].odoopbx_reload_view('%.recording' % MODULE_NAME)
        # Notify user
        if data.get('notify_uid'):
            self.env['%s.settings' % MODULE_NAME].odoopbx_notify(
                'Transcription updated', notify_uid=data['notify_uid'])
            self.env['%s.settings' % MODULE_NAME].odoopbx_reload_view('%s.recording' % MODULE_NAME)
        # Register summary if partner is linked.
        if self.partner and data.get('summary') and self.env[
                '%s.settings' % MODULE_NAME].sudo().get_param('register_summary'):
            obj = self.partner
            try:
                if release.version_info[0] < 14:
                    obj.sudo(SUPERUSER_ID).message_post(body=data['summary'])
                else:
                    obj.with_user(SUPERUSER_ID).message_post(body=data['summary'])
                # Reload the view of res.partner
                self.env['%s.settings' % MODULE_NAME].odoopbx_reload_view('res.partner')
            except Exception as e:
                logger.error('Cannot register summary: %s', e)

##########  END OF TRANSCRIPTION METHODS #########################################################
