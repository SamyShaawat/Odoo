from odoo import api, models, fields
import base64
from odoo.http import request
import os
import re
from odoo.modules import get_modules, get_module_path, get_resource_path
from odoo.tools.mimetypes import get_extension, guess_mimetype
from odoo.tools import pycompat
import hashlib
from odoo.exceptions import UserError, AccessError, MissingError
import mimetypes
from odoo.tools import consteq
from odoo import SUPERUSER_ID, _, http
from odoo.http import root, content_disposition
class IrHttpNew(models.AbstractModel):
    _inherit = "ir.http"

    def _binary_set_headers(self, status, content, filename, mimetype, unique, filehash=None, download=False):
        headers = [('Content-Type', mimetype), ('X-Content-Type-Options', 'nosniff'), ('Content-Security-Policy', "default-src 'none'")]
        # cache
        etag = bool(request) and request.httprequest.headers.get('If-None-Match')
        status = status or 200
        if filehash:
            headers.append(('ETag', filehash))
            if etag == filehash and status == 200:
                status = 304
        headers.append(('Cache-Control', 'max-age=%s' % (http.STATIC_CACHE_LONG if unique else 0)))
        # content-disposition default name
        if download:
            headers.append(('Content-Disposition', content_disposition(filename)))

        return (status, headers, content)


    def _binary_record_content(
            self, record, field='datas', filename=None,
            filename_field='name', default_mimetype='application/octet-stream'):

        model = record._name
        mimetype = 'mimetype' in record and record.mimetype or False
        content = None
        filehash = 'checksum' in record and record['checksum'] or False

        field_def = record._fields[field]
        if field_def.type == 'binary' and field_def.attachment and not field_def.related:
            if model != 'ir.attachment':
                field_attachment = self.env['ir.attachment'].sudo().search_read(
                    domain=[('res_model', '=', model), ('res_id', '=', record.id), ('res_field', '=', field)],
                    fields=['datas', 'mimetype', 'checksum'], limit=1)
                if field_attachment:
                    mimetype = field_attachment[0]['mimetype']
                    content = field_attachment[0]['datas']
                    filehash = field_attachment[0]['checksum']
            else:
                mimetype = record['mimetype']
                content = record['datas']
                filehash = record['checksum']

        if not content and field_def.type == 'binary':
            try:
                content = record[field] or ''
            except AccessError:
                # `record[field]` may not be readable for current user -> 404
                content = ''

        # filename
        if not filename:
            if filename_field in record:
                filename = record[filename_field]
            if not filename:
                filename = "%s-%s-%s" % (record._name, record.id, field)

        if not mimetype:
            try:
                decoded_content = base64.b64decode(content)
            except base64.binascii.Error:  # if we could not decode it, no need to pass it down: it would crash elsewhere...
                return (404, [], None)
            mimetype = guess_mimetype(decoded_content, default=default_mimetype)

        # extension
        has_extension = get_extension(filename) or mimetypes.guess_type(filename)[0]
        if not has_extension:
            extension = mimetypes.guess_extension(mimetype)
            if extension:
                filename = "%s%s" % (filename, extension)

        if not filehash:
            filehash = '"%s"' % hashlib.md5(pycompat.to_text(content).encode('utf-8')).hexdigest()

        status = 200 if content else 404
        return status, content, filename, mimetype, filehash
    @classmethod
    def _binary_ir_attachment_redirect_content(cls, record, default_mimetype='application/octet-stream'):
        # mainly used for theme images attachemnts
        status = content = filename = filehash = None
        mimetype = getattr(record, 'mimetype', False)
        if record.type == 'url' and record.url:
            # if url in in the form /somehint server locally
            url_match = re.match(r"^/(\w+)/(static|images)/(.+)$", record.url)
            if url_match:
                module = url_match.group(1)
                static = url_match.group(2)
                module_path = get_module_path(module)
                module_resource_path = get_resource_path(module, static, url_match.group(3))

                if module_path and module_resource_path:
                    module_path = os.path.join(os.path.normpath(module_path), static,
                                               '')  # join ensures the path ends with '/'
                    module_resource_path = os.path.normpath(module_resource_path)
                    if module_resource_path.startswith(module_path):
                        with open(module_resource_path, 'rb') as f:
                            content = base64.b64encode(f.read())
                        status = 200
                        filename = os.path.basename(module_resource_path)
                        mimetype = guess_mimetype(base64.b64decode(content), default=default_mimetype)
                        filehash = '"%s"' % hashlib.md5(pycompat.to_text(content).encode('utf-8')).hexdigest()

            if not content:
                status = 301
                content = record.url

        return status, content, filename, mimetype, filehash

    def _get_record_and_check(self, xmlid=None, model=None, id=None, field='datas', access_token=None):
        # get object and content
        record = None
        if xmlid:
            record = self._xmlid_to_obj(self.env, xmlid)
        elif id and model in self.env:
            record = self.env[model].browse(int(id))

        # obj exists
        if not record or field not in record:
            return None, 404

        try:
            if model == 'ir.attachment':
                record_sudo = record.sudo()
                if access_token and not consteq(record_sudo.access_token or '', access_token):
                    return None, 403
                elif (access_token and consteq(record_sudo.access_token or '', access_token)):
                    record = record_sudo
                elif record_sudo.public:
                    record = record_sudo
                elif self.env.user.has_group('base.group_portal'):
                    # Check the read access on the record linked to the attachment
                    # eg: Allow to download an attachment on a task from /my/task/task_id
                    record.check('read')
                    record = record_sudo

            # check read access
            try:
                # We have prefetched some fields of record, among which the field
                # 'write_date' used by '__last_update' below. In order to check
                # access on record, we have to invalidate its cache first.
                if not record.env.su:
                    record._cache.clear()
                record['write_date']
            except AccessError:
                return None, 403

            return record, 200
        except MissingError:
            return None, 404

    def binary_content(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       unique=False, filename=None, filename_field='name', download=False,
                       mimetype=None, default_mimetype='application/octet-stream',
                       access_token=None):
        """ Get file, attachment or downloadable content

        If the ``xmlid`` and ``id`` parameter is omitted, fetches the default value for the
        binary field (via ``default_get``), otherwise fetches the field for
        that precise record.

        :param str xmlid: xmlid of the record
        :param str model: name of the model to fetch the binary from
        :param int id: id of the record from which to fetch the binary
        :param str field: binary field
        :param bool unique: add a max-age for the cache control
        :param str filename: choose a filename
        :param str filename_field: if not create an filename with model-id-field
        :param bool download: apply headers to download the file
        :param str mimetype: mintype of the field (for headers)
        :param str default_mimetype: default mintype if no mintype found
        :param str access_token: optional token for unauthenticated access
                                 only available  for ir.attachment
        :returns: (status, headers, content)
        """
        record, status = self._get_record_and_check(xmlid=xmlid, model=model, id=id, field=field,
                                                    access_token=access_token)

        if not record:
            return (status or 404, [], None)

        content, headers, status = None, [], None

        if record._name == 'ir.attachment':
            status, content, default_filename, mimetype, filehash = self._binary_ir_attachment_redirect_content(record,
                                                                                                                default_mimetype=default_mimetype)
            filename = filename or default_filename
        if not content:
            status, content, filename, mimetype, filehash = self._binary_record_content(
                record, field=field, filename=filename, filename_field=filename_field,
                default_mimetype='application/octet-stream')

        status, headers, content = self._binary_set_headers(
            status, content, filename, mimetype, unique, filehash=filehash, download=download)

        return status, headers, content


    @api.model
    def _get_feed_content_common(self, xmlid=None, model='ir.attachment', res_id=None, field='datas',
            unique=None, filename=None, filename_field='name', download=None, mimetype=None,
            access_token=None, token=None):
        status, headers, content = self.binary_content(
            xmlid=xmlid, model=model, id=res_id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype='', access_token=access_token
        )
        if status != 200:
            return self._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers=[('Content-Type', 'text/xml'), ('Content-Length', len(content_base64))]
            response = request.make_response(content_base64, headers)
        return response