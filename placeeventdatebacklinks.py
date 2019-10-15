# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
# Copyright (C) 2011 Tim G L Lyons
# Copyright (C) 2019 Hans Ulrich Frink hansulrich.frink@gmail.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

#-------------------------------------------------------------------------
#
# Gtk modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gramps.gui.listmodel import ListModel
from gramps.gen.utils.db import navigation_label
from gramps.gen.plug import Gramplet
from gramps.gen.datehandler import get_date
from gramps.gui.utils import edit_object
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

class Backlinks(Gramplet):
    """
    Displays the back references for an object.
    """
    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        top = Gtk.TreeView()
        titles = [(_('Type'), 1, 100),
                  (_('Name'), 2, 100),
                  ('', 3, 1), #hidden column for the handle
                  ('', 4, 1), #hidden column for non-localized object type
                  (_('Date'), 5, 100),
                  ('', 6, 1)] #hidden column for date sort value
        self.model = ListModel(top, titles, event_func=self.cb_double_click)
        return top


    def get_date1(self, event, handle):
        #for eventref in person.event_ref_list:
        #    if handle == eventref.ref:
        #        role = eventref.get_role().string
        #        #print(f'{self.__format_date_place(eventref)}')
        return(f'{event.get_date_object()}')

    def display_backlinks(self, active_handle):
        """
        Display the back references for an object.
        """
        for classname, handle in \
                self.dbstate.db.find_backlink_handles(active_handle):
            name = navigation_label(self.dbstate.db, classname, handle)[0]
            plevent = self.dbstate.db.get_event_from_handle(handle)
            #pldate = self.get_date(plevent, active_handle) 
            pldate = get_date(plevent) 
            pldate_sort = '%012d' % plevent.get_date_object().get_sort_value()
            self.model.add((_(classname), name, handle, classname, pldate, pldate_sort))
        self.set_has_data(self.model.count > 0)

    def get_has_data(self, active_handle):
        """
        Return True if the gramplet has data, else return False.
        """
        if not active_handle:
            return False
        for handle in self.dbstate.db.find_backlink_handles(active_handle):
            return True
        return False

    def cb_double_click(self, treeview):
        """
        Handle double click on treeview.
        """
        (model, iter_) = treeview.get_selection().get_selected()
        if not iter_:
            return

        (objclass, handle) = (model.get_value(iter_, 3),
                              model.get_value(iter_, 2))

        edit_object(self.dbstate, self.uistate, objclass, handle)

class PlaceEventDateBacklinks(Backlinks):
    """
    Displays the back references for a place.
    """
    def db_changed(self):
        self.connect(self.dbstate.db, 'place-update', self.update)
        self.connect_signal('Place', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Place')
        self.set_has_data(self.get_has_data(active_handle))

    def main(self):
        active_handle = self.get_active('Place')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

