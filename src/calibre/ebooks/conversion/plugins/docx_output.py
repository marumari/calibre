#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'

from calibre.customize.conversion import OutputFormatPlugin, OptionRecommendation

PAGE_SIZES = ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'b0', 'b1',
              'b2', 'b3', 'b4', 'b5', 'b6', 'legal', 'letter']

class DOCXOutput(OutputFormatPlugin):

    name = 'DOCX Output'
    author = 'Kovid Goyal'
    file_type = 'docx'

    options = {
        OptionRecommendation(name='docx_page_size', recommended_value='letter',
            level=OptionRecommendation.LOW, choices=PAGE_SIZES,
            help=_('The size of the page. Default is letter. Choices '
            'are %s') % PAGE_SIZES),

        OptionRecommendation(name='docx_custom_page_size', recommended_value=None,
            help=_('Custom size of the document. Use the form widthxheight '
            'EG. `123x321` to specify the width and height (in pts). '
            'This overrides any specified page-size.')),

        OptionRecommendation(name='extract_to',
            help=_('Extract the contents of the generated %s file to the '
                'specified directory. The contents of the directory are first '
                'deleted, so be careful.') % 'DOCX'),
    }

    def convert_metadata(self, oeb):
        from lxml import etree
        from calibre.ebooks.oeb.base import OPF, OPF2_NS
        from calibre.ebooks.metadata.opf2 import OPF as ReadOPF
        from io import BytesIO
        package = etree.Element(OPF('package'), attrib={'version': '2.0'}, nsmap={None: OPF2_NS})
        oeb.metadata.to_opf2(package)
        self.mi = ReadOPF(BytesIO(etree.tostring(package, encoding='utf-8')), populate_spine=False, try_to_guess_cover=False).to_book_metadata()

    def convert(self, oeb, output_path, input_plugin, opts, log):
        from calibre.ebooks.docx.writer.container import DOCX
        from calibre.ebooks.docx.writer.from_html import Convert
        docx = DOCX(opts, log)
        self.convert_metadata(oeb)
        Convert(oeb, docx)()
        docx.write(output_path, self.mi)
        if opts.extract_to:
            from calibre.ebooks.docx.dump import do_dump
            do_dump(output_path, opts.extract_to)

