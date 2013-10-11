#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'

import tempfile, shutil

from PyQt4.Qt import QObject

from calibre.gui2 import error_dialog
from calibre.ptempfile import PersistentTemporaryDirectory
from calibre.ebooks.oeb.polish.main import SUPPORTED
from calibre.ebooks.oeb.polish.container import get_container, clone_container
from calibre.gui2.tweak_book import set_current_container, current_container
from calibre.gui2.tweak_book.undo import GlobalUndoHistory

class Boss(QObject):

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.global_undo = GlobalUndoHistory()
        self.container_count = 0
        self.tdir = None

    def __call__(self, gui):
        self.gui = gui
        gui.file_list.delete_requested.connect(self.delete_requested)

    def mkdtemp(self):
        self.container_count += 1
        return tempfile.mkdtemp(prefix='%05d-' % self.container_count, dir=self.tdir)

    def check_dirtied(self):
        # TODO: Implement this
        return True

    def open_book(self, path):
        ext = path.rpartition('.')[-1].upper()
        if ext not in SUPPORTED:
            return error_dialog(self.gui, _('Unsupported format'),
                _('Tweaking is only supported for books in the %s formats.'
                  ' Convert your book to one of these formats first.') % _(' and ').join(sorted(SUPPORTED)),
                show=True)

        if not self.check_dirtied():
            return

        self.container_count = -1
        if self.tdir:
            shutil.rmtree(self.tdir, ignore_errors=True)
        self.tdir = PersistentTemporaryDirectory()
        self.gui.blocking_job('open_book', _('Opening book, please wait...'), self.book_opened, get_container, path, tdir=self.mkdtemp())

    def book_opened(self, job):
        if job.traceback is not None:
            return error_dialog(self.gui, _('Failed to open book'),
                    _('Failed to open book, click Show details for more information.'),
                                det_msg=job.traceback, show=True)
        container = job.result
        set_current_container(container)
        self.current_metadata = self.gui.current_metadata = container.mi
        self.global_undo.open_book(container)
        self.gui.update_window_title()
        self.gui.file_list.build(container)

    def add_savepoint(self, msg):
        nc = clone_container(current_container(), self.mkdtemp())
        self.global_undo.add_savepoint(nc, msg)
        set_current_container(nc)

    def delete_requested(self, spine_items, other_items):
        if not self.check_dirtied():
            return
        self.add_savepoint(_('Delete files'))
        c = current_container()
        c.remove_from_spine(spine_items)
        for name in other_items:
            c.remove_item(name)
        self.gui.file_list.delete_done(spine_items, other_items)


