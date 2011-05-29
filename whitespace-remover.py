# Whitespace Remover - gedit plugin
# Copyright (C) 2011 Alexandr Grigorcea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This software is heavily inspried and in parts based on Osmo Salomaa's
# trailsave plugin <http://users.tkk.fi/~otsaloma/gedit/>.

from gi.repository import Gedit, Gio, GObject, Gtk, PeasGtk

class WhitespaceRemover(GObject.Object, Gedit.ViewActivatable, PeasGtk.Configurable):
    __gtype_name__ = "WhitespaceRemover"
    view = GObject.property(type=Gedit.View)
    settings = Gio.Settings.new("org.gnome.gedit.plugins.whitespace-remover")

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.handler = self.view.get_buffer().connect('saving', self.on_saving)

    def do_deactivate(self):
        self.view.get_buffer().disconnect(self.handler)

    def do_update_state(self):
        pass

    def on_saving(self, document, *args):
        """Strip trailing spaces in document."""
        if not document.get_readonly():
            document.begin_user_action()
            preserve_cursor = self.settings.get_boolean("preserve-cursor")

            if (self.settings.get_boolean('remove-whitespaces')):
                self.strip_trailing_spaces_on_lines(document, preserve_cursor)

            if (self.settings.get_boolean('remove-newlines')):
                self.strip_trailing_blank_lines(document, preserve_cursor)

            document.end_user_action()

    def strip_trailing_blank_lines(self, doc, preserve_cursor):
        """Delete trailing newlines at the end of the document."""
        cursor_line = doc.get_iter_at_mark(doc.get_insert()).get_line()
        buffer_end = doc.get_end_iter()

        if buffer_end.starts_line():
            itr = buffer_end.copy()
            while itr.backward_line():
                if (preserve_cursor and itr.get_line() < cursor_line):
                    itr.forward_line()
                    break
                if not itr.ends_line():
                    itr.forward_to_line_end()
                    break
            doc.delete(itr, buffer_end)

    def strip_trailing_spaces_on_lines(self, doc, preserve_cursor):
        """Delete trailing space at the end of each line."""
        cursor_line = doc.get_iter_at_mark(doc.get_insert()).get_line()

        for line in range(doc.get_end_iter().get_line() + 1):
            end = doc.get_iter_at_line(line)
            if not end.ends_line():
                end.forward_to_line_end()
            itr = end.copy()
            while itr.backward_char():
                if preserve_cursor and line == cursor_line:
                    cursor = doc.get_iter_at_mark(doc.get_insert())
                    if itr.compare(cursor) < 0:
                        itr.forward_char()
                        break
                if not itr.get_char() in (" ", "\t"):
                    itr.forward_char()
                    break
            if itr.compare(end) < 0:
                doc.delete(itr, end)

    def do_create_configure_widget(self):
        main_box = Gtk.VBox()

        whitespaces = Gtk.CheckButton("Remove trailing whitespaces")
        whitespaces.set_active(self.settings.get_boolean("remove-whitespaces"))
        whitespaces.connect('toggled', self.update_setting, 'remove-whitespace')

        newlines = Gtk.CheckButton("Remove empty lines at the end of document")
        newlines.set_active(self.settings.get_boolean("remove-newlines"))
        newlines.connect('toggled', self.update_setting, 'remove-newlines')

        preserve = Gtk.CheckButton("Preserve cursor position")
        preserve.set_active(self.settings.get_boolean("remove-whitespaces"))
        preserve.connect('toggled', self.update_setting, 'remove-whitespace')

        main_box.pack_start(whitespaces, False, False, 0)
        main_box.pack_start(newlines, False, False, 0)
        main_box.pack_start(preserve, False, False, 0)

        return main_box

    def setting_changed(self, settings, key, check_button):
        check_button.set_active(settings.get_boolean(key))

    def update_setting(self, button, key):
        self.settings.set_boolean(key, button.get_active())
