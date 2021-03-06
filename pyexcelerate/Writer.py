import os
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import time
from jinja2 import Environment, FileSystemLoader

class Writer(object):
    TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
    env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), auto_reload=False)

    _docProps_app_template = env.get_template("docProps/app.xml")
    _docProps_core_template = env.get_template("docProps/core.xml")
    _content_types_template = env.get_template("[Content_Types].xml")
    _rels_template = env.get_template("_rels/.rels")
    _workbook_template = env.get_template("xl/workbook.xml")
    _workbook_rels_template = env.get_template("xl/_rels/workbook.xml.rels")
    _worksheet_template = env.get_template("xl/worksheets/sheet.xml")

    def __init__(self, workbook):
        self.workbook = workbook

    def _render_template_wb(self, template, extra_context=None):
        context = {'workbook': self.workbook}
        if extra_context:
            context.update(extra_context)
        return template.render(context)

    def _get_utc_now(self):
        now = datetime.utcnow()
        return now.strftime("%Y-%m-%dT%H:%M:00Z")


    def save(self, f):
        zf = ZipFile(f, 'w', ZIP_DEFLATED)
        zf.writestr("docProps/app.xml", self._render_template_wb(self._docProps_app_template))
        zf.writestr("docProps/core.xml", self._render_template_wb(self._docProps_core_template, {'date': self._get_utc_now()}))
        zf.writestr("[Content_Types].xml", self._render_template_wb(self._content_types_template))
        zf.writestr("_rels/.rels", self._rels_template.render())
        zf.writestr("xl/workbook.xml", self._render_template_wb(self._workbook_template))
        zf.writestr("xl/_rels/workbook.xml.rels", self._render_template_wb(self._workbook_rels_template))
        for index, sheet in self.workbook.get_xml_data():
            tfd, tfn = tempfile.mkstemp()
            tf = os.fdopen(tfd, 'wb')
            sheetStream = self._worksheet_template.generate({'worksheet': sheet})
            for s in sheetStream:
                tf.write(s)
            tf.close()
            zf.write(tfn, "xl/worksheets/sheet%s.xml" % (index))
            os.remove(tfn)
        zf.close()
