# vim: set fileencoding=utf-8 :
# GNU Solfege - free ear training software
# Copyright (C) 2009, 2010, 2011  Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import locale
import logging
import sys

import gobject
import gtk

import solfege
from solfege import frontpage
from solfege import gu
from solfege import lessonfile

def decode_entry_string(s):
    if sys.platform == 'win32':
        return s.decode("mbcs", "replace")
    return s.decode(locale.getpreferredencoding(), "decode")


class SelectWinBase(gtk.ScrolledWindow):
    """
    Base class for the classes that display the front page and the
    page where we select exerises or tests.
    """
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._on_focus_in_blocked = False
        self.m_min_width = 400
        self.m_min_height = 300
        self.set_size_request(self.m_min_width, self.m_min_height)
        self.m_linkbuttons = []
        self.g_searchentry = None
    def on_focus_in(self, w, event):
        """
        Set the vadjustment so that the window will scroll to make the button
        that has the focus visible in the scrolled window.
        """
        if self._on_focus_in_blocked:
            return
        a = w.get_allocation()
        adj = self.get_vadjustment()
        if a.y + a.height > adj.value + adj.page_size:
            if w.get_data('last'):
                adj.value = adj.upper - adj.page_size
            else:
                adj.value = a.y - adj.page_size + a.height
        elif a.y < adj.value:
            # If the widget is the first row of the first category, then...
            if w.get_data('first'):
                adj.value = 0.0
            else:
                adj.value = a.y
    def on_key_press_event(self, mainwin, event):
        if event.type == gtk.gdk.KEY_PRESS and event.state == 0:
            adj = self.get_vadjustment()
            if event.keyval in (gtk.keysyms.End, gtk.keysyms.KP_End):
                if self.m_linkbuttons:
                    self.m_linkbuttons[-1].grab_focus()
                return True
            elif event.keyval in (gtk.keysyms.Home, gtk.keysyms.KP_Home):
                if self.g_searchentry:
                    self.get_vadjustment().value = 0.0
                    self.g_searchentry.grab_focus()
                else:
                    self.m_linkbuttons[0].grab_focus()
                return True
            if event.keyval in (gtk.keysyms.Page_Down, gtk.keysyms.KP_Page_Down):
                # First we find the button that now has the keyboard focus
                for idx, btn in enumerate(self.m_linkbuttons):
                    if btn.is_focus():
                        break
                # Then we find a button that is approximately adj.page_increment
                # down and grabs that buttons focus.
                for to_btn in self.m_linkbuttons[idx:]:
                    if to_btn.get_allocation().y - adj.value > adj.page_size:
                        self._on_focus_in_blocked = True
                        to_btn.grab_focus()
                        self._on_focus_in_blocked = False
                        return True
                self.m_linkbuttons[-1].grab_focus()
                return True
            if event.keyval in (gtk.keysyms.Page_Up, gtk.keysyms.KP_Page_Up):
                for idx, btn in enumerate(self.m_linkbuttons):
                    if btn.is_focus():
                        break
                for to_btn in self.m_linkbuttons:
                    if to_btn.get_allocation().y > adj.value - adj.page_increment:
                        self._on_focus_in_blocked = True
                        to_btn.grab_focus()
                        self._on_focus_in_blocked = False
                        return True
    def adjust_scrolledwin_size(self):
        # We do set_size_request on the view to make the window so wide
        # that we avoid a horizontal scroll bar.
        w = self.g_box.size_request()[0]
        # It should be possible to check if the vscrollbar is visible, and
        # only reserve space for it. But I cannot get that to works. I find
        # that self.get_vscrollbar().props.visible is updated only part
        # of the time.
        w += self.get_vscrollbar().size_request()[0]
        # FIXME I don't understand why we have to add the extra
        # two pixels to avoid the horizontal scrollbar in all cases.
        w += self.style_get_property("scrollbar-spacing") + 2
        if w < self.m_min_width:
            w = self.m_min_width
        # I found no portable way to make sure the window use all available
        # vertical space without conflicting with panels or other things
        # on the desktop. So we will just use max 80% of the space available
        # Also, there is something about the spacing that is not correct,
        # because I need to add +2 below to avoid the vertical scrollbar on
        # ubuntu 10.04 and +4 on MS Windows XP.
        h = self.g_box.size_request()[1] + 4
        if h > gtk.gdk.screen_height() * 0.8:
            h = int(gtk.gdk.screen_height() *0.8)
        self.set_size_request(w, h if h > self.m_min_height else self.m_min_height)
        # Then we check if we have to move the app window higher up on the
        # screen so that the whole window is visible.
        px, py = solfege.win.get_position()
        if py + h > gtk.gdk.screen_height():
            solfege.win.move(px, 0)


class ExerciseView(SelectWinBase):
    max_exercise_label_width = int(gtk.gdk.screen_width() * 0.90)
    def __init__(self,  fields=('link',)):
        SelectWinBase.__init__(self)
        self.m_fields = fields
        app = solfege.app
        self.g_box = gtk.VBox()
        self.g_box.set_border_width(gu.hig.SPACE_MEDIUM)
        self.add_with_viewport(self.g_box)
        self.g_searchbox = gtk.HBox()
        self.g_box.pack_start(self.g_searchbox, False, padding=gu.hig.SPACE_MEDIUM)
        self.g_searchentry = gtk.Entry()
        self.g_searchbox.pack_start(self.g_searchentry, True)
        self.g_searchentry.connect('activate', self.on_search)
        gu.bButton(self.g_searchbox, _("Search"), callback=self.on_search, expand=False)
        self.show_all()
    def _display_data(self, page, display_only_tests=False,
            is_search_result=False, show_topics=False):
        """
        display_only_tests should be True when we are browsing available tests.
        This will validate statistics for each lesson and display the test result.
        """
        if not is_search_result:
            self.m_page = page
        try:
            self.g_hbox.destroy()
        except AttributeError:
            pass
        self.g_hbox = gu.bHBox(self.g_box)
        self.g_hbox.set_spacing(gu.hig.SPACE_MEDIUM)
        label = None
        do_sg = True
        if len(page[0]) > 0 and isinstance(page[0][0], frontpage.LinkList):
            count = 0
            for column in page:
                assert isinstance(column, frontpage.Column)
                for linklist in column:
                    assert isinstance(linklist, (frontpage.LinkList,
                                                 frontpage.Paragraph))
                    if isinstance(linklist, frontpage.LinkList):
                        count += len(linklist)
            if count > 80:
                do_sg = False
        for column in page:
            sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
            assert isinstance(column, frontpage.Column)
            first = True
            vbox = gtk.VBox()
            vbox.set_spacing(gu.hig.SPACE_MEDIUM)
            self.g_hbox.pack_start(vbox, False)
            for sect_id, linklist in enumerate(column):
                if isinstance(linklist, frontpage.Paragraph):
                    label = gtk.Label(linklist.m_text)
                    label.set_use_markup(True)
                    label.set_line_wrap(True)
                    label.set_alignment(0.0, 0.5)
                    vbox.pack_start(label, False)
                    continue
                assert isinstance(linklist, frontpage.LinkList)
                if (display_only_tests
                    and not frontpage._TreeCommon.tests_in_sub(linklist)):
                        continue
                linkbox = gtk.VBox()
                vbox.pack_start(linkbox, False)
                heading = gtk.Label("<b>%s</b>" % _no_xgettext(linklist.m_name))
                heading.set_alignment(0.0, 0.5)
                heading.set_use_markup(True)
                linkbox.pack_start(heading, False)
                sizegroups = dict((k, gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)) for k in self.m_fields)
                for idx, link in enumerate(linklist):
                    if isinstance(self, TestsView) and not frontpage._TreeCommon.tests_in_sub(link):
                        continue
                    if isinstance(link, frontpage.Page):
                        label = gu.ClickableLabel(_no_xgettext(link.m_name))
                        label.connect('clicked', self.on_page_link_clicked, link)
                    else:
                        assert isinstance(link, unicode), type(link)
                        label = gtk.HBox()
                        label.set_spacing(gu.hig.SPACE_SMALL)
                        if display_only_tests:
                            solfege.db.validate_stored_statistics(link)
                        try:
                            for fieldname in self.m_fields:
                                if fieldname in (u'link', u'link-with-filename-tooltip'):
                                    labeltxt = lessonfile.infocache.get(link, 'title')
                                    lbl = gu.ClickableLabel(_no_xgettext(labeltxt))
                                    if solfege.app.m_options.debug:
                                        lbl.set_tooltip_text(u"%s\n%s module" % (link, lessonfile.infocache.get(link, 'module')))
                                    elif fieldname == u'link-with-filename-tooltip':
                                        lbl.set_tooltip_text(link)
                                    if do_sg:
                                        sizegroups[fieldname].add_widget(lbl)
                                    if show_topics:
                                        topic = solfege.app.m_frontpage_data.get_topic_of_lesson_file(link)
                                        if topic and topic not in labeltxt:
                                            lbl.add_heading(topic)
                                    lbl.connect('clicked', self.on_link_clicked, link)
                                else:
                                    if fieldname == 'filename':
                                        lbl = gtk.Label(link)
                                    else:
                                        lbl = gtk.Label(lessonfile.infocache.get(link, fieldname))
                                    lbl.set_alignment(0.0, 0.5)
                                    if do_sg:
                                        sizegroups[fieldname].add_widget(lbl)
                                label.pack_start(lbl, False)
                        except lessonfile.InfoCache.FileNotFound:
                            label = gu.ClickableLabel(_(u"«%s» was not found") % link)
                            label.make_warning()
                        except lessonfile.InfoCache.FileNotLessonfile:
                            label = gu.ClickableLabel(_(u"Failed to parse «%s»") % link)
                            label.make_warning()
                    if first:
                        label.set_data('first', True)
                        first = False
                    w = label.size_request()[0]
                    if w > self.max_exercise_label_width:
                        w = self.max_exercise_label_width
                        if isinstance(link, unicode):
                            txt = _(lessonfile.infocache.get(link, "title"))
                        else:
                            txt = link.m_name
                        label.set_tooltip_text(txt)
                        label.set_size_request(w / len(page), -1)
                    self.m_linkbuttons.append(label)
                    label.connect('focus-in-event', self.on_focus_in)
                    if display_only_tests:
                        box = gtk.HBox()
                        box.pack_start(label)
                        if isinstance(link, unicode):
                            passed, result = solfege.db.get_test_status(link)
                            if passed == True:
                                box.pack_start(gtk.Label(_("passed, %.1f%%") % (result * 100)))
                            if passed == False:
                                box.pack_start(gtk.Label(_("failed, %.1f%%") % (result * 100)))
                            # do nothing if passed == None since
                        linkbox.pack_start(box, True)
                    else:
                        linkbox.pack_start(label, True)
                    if do_sg:
                        sizegroup.add_widget(label)
            if label:
                label.set_data('last', True)
        self.g_hbox.show_all()
        self.adjust_scrolledwin_size()
        self.get_vadjustment().set_value(0.0)
    def on_page_link_clicked(self, btn, link):
        self.g_searchbox.hide()
        self.emit('link-clicked', self.m_page)
        self.display_data(link)
    def on_link_clicked(self, w, filename):
        self.emit('link-clicked', self.m_page)
        solfege.app.practise_lessonfile(filename)
    def display_search_result(self, searchfor, result, result_C, display_only_tests=False):
        self._display_data(
          frontpage.Page(u'',
            frontpage.Column([
              frontpage.LinkList(
            _(u"Search results for “%s”:") % self.g_searchentry.get_text(),
              result),
              frontpage.LinkList(
            _(u"C-locale search results for “%s”:") % self.g_searchentry.get_text(),
              result_C),
              ])))
    def on_end_practise(self, w=None):
        pass
    def _search(self, substring, C_locale, only_tests):
        """
        substring - the string to search for
        C_locale - True if we should search in the untranslated titles
        only_tests - True if we should only return exercises that have
                     tests
        """
        logging.debug("search: '%s'", substring)
        match_func = {
            False: lambda filename: substring in _no_xgettext(lessonfile.infocache.get(filename, 'title')).lower(),
            True: lambda filename: substring in lessonfile.infocache.get(filename, 'title').lower()
        }[C_locale]
        test_filter = {
            False: lambda filename: True,
            True: lambda filename: lessonfile.infocache.get(filename, 'test')
        }[C_locale]
        page = frontpage.Page(listitems=frontpage.Column())
        cur_topic = None
        # the last topic appended to the page
        last_topic = None
        found = set()
        for child in self.m_page.iterate_flattened():
            if isinstance(child, frontpage.LinkList):
                cur_topic = child
            if isinstance(child, unicode):
                try:
                    if (match_func(child) and test_filter(child)) and child not in found:
                        if cur_topic != last_topic:
                            page[0].append(frontpage.LinkList(cur_topic.m_name))
                            last_topic = cur_topic
                        found.add(child)
                        page[0][-1].append(child)
                except lessonfile.infocache.InfoCacheException:
                    # Ignore missing lesson files and files with errors
                    pass
        return page

gobject.signal_new('link-clicked', ExerciseView,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))


class FrontPage(ExerciseView):
    def display_data(self, data, display_only_tests=False,
            is_search_result=False, show_topics=False):
        self._display_data(data, display_only_tests, is_search_result,
                           show_topics)
        self.g_searchentry.grab_focus()
    def on_search(self, *button):
        search_for = decode_entry_string(self.g_searchentry.get_text().lower())
        logging.debug(u"FrontPage.on_search '%s'", search_for)
        page = self._search(search_for, False, False)
        page_C = self._search(search_for, True, False)
        page_C.m_name = _('Search untranslated lesson titles')
        if not page_C.is_empty():
            page[0].append(frontpage.LinkList(_('Too few matches?'),
                listitems=[page_C]))
        self.display_data(page, is_search_result=True)


class TestsView(ExerciseView):
    def on_link_clicked(self, w, filename):
        self.emit('link-clicked', self.m_page)
        solfege.app.test_lessonfile(filename)
    def display_data(self, data=None, is_search_result=False, show_topics=False):
        self._display_data(data, True, is_search_result, show_topics)
        self.g_searchentry.grab_focus()
    def on_search(self, *button):
        search_for = decode_entry_string(self.g_searchentry.get_text().lower())
        page = self._search(search_for, False, True)
        page_C = self._search(search_for, True, True)
        page_C.m_name = u'Search exercises without translating them'
        if not page_C.is_empty():
            page[0].append(frontpage.LinkList(_('Too few matches?'),
                listitems=[page_C]))
        self.display_data(page, is_search_result=True)


class SearchView(ExerciseView):
    def __init__(self, infotext, fields=('link',)):
        ExerciseView.__init__(self, fields)
        page = """FileHeader(1,
        Page(u'', [
         Column([
          Paragraph('%s'),
         ]),
        ])
        )""" % infotext
        p = frontpage.parse_tree(page)
        self.display_data(frontpage.parse_tree(page))
        self.g_searchentry.show()
    def display_data(self, data):
        self._display_data(data)
        self.g_searchentry.grab_focus()
    def on_search(self, *button):
        search_for = decode_entry_string(self.g_searchentry.get_text().lower())
        lessonfile.infocache.update_modified_files()
        self.display_search_result(decode_entry_string(self.g_searchentry.get_text()), [
            filename for filename in lessonfile.infocache._data
            if search_for in _(lessonfile.infocache.get(filename, 'title')).lower()
        ], [
            filename for filename in lessonfile.infocache._data
            if search_for in lessonfile.infocache.get(filename, 'title').lower()
        ])


