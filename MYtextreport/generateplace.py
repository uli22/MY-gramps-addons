1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2015-2016 Nick Hall
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
 
"""Tools/Database Processing/Generate hierarchy from place titles"""
 
from gramps.gui.plug import tool
from gramps.gui.utils import ProgressMeter
from gramps.gen.db import DbTxn
from gramps.gen.lib import Place, PlaceRef, PlaceName, PlaceType
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
 
#-------------------------------------------------------------------------
#
# GeneratePlace
#
#-------------------------------------------------------------------------
class GeneratePlace(tool.BatchTool):
 
    def __init__(self, dbstate, user, options_class, name, callback=None):
        self.user = user
        tool.BatchTool.__init__(self, dbstate, user, options_class, name)
 
        if not self.fail:
            self.run()
 
    def run(self):
        """
        Generate the hierarchy.
        """
        with self.user.progress(
                _("Generating hierarchy"), '',
                self.db.get_number_of_places()) as step:
 
            for handle in self.db.get_place_handles():
                step()
                place = self.db.get_place_from_handle(handle)
 
                if (int(place.get_type()) != PlaceType.UNKNOWN or
                    ',' not in place.get_title()):
                    # Only process places with a type of Unknown.
                    continue
 
                names = [name.strip()
                         for name in place.get_title().split(',')
                         if name.strip()]
                place_name = PlaceName()
                place_name.set_value(names[0])
                place.set_name(place_name)
                place.set_title('')
 
                parent_handle = None
                for name, handle in self.find_hierarchy(names)[:-1]:
                    if handle is None:
                        new_place = Place()
                        place_name = PlaceName()
                        place_name.set_value(name)
                        new_place.set_name(place_name)
                        if parent_handle is None:
                            new_place.set_type(PlaceType.COUNTRY)
                        if parent_handle is not None:
                            placeref = PlaceRef()
                            placeref.ref = parent_handle
                            new_place.add_placeref(placeref)
                        with DbTxn(_("Add Place"), self.db) as trans:
                            parent_handle = self.db.add_place(new_place, trans)
                    else:
                        parent_handle = handle
 
                if parent_handle is not None:
                    placeref = PlaceRef()
                    placeref.ref = parent_handle
                    place.add_placeref(placeref)
                with DbTxn(_("Edit Place"), self.db) as trans:
                    self.db.commit_place(place, trans)
 
    def find_hierarchy(self, names):
        out = []
        handle = None
        level = self.get_countries()
        names.reverse()
        for name in names:
            if name not in level:
                out.append((name, None))
                level = {}
            else:
                handle = level[name]
                level = self.get_level(handle)
                out.append((name, handle))
        return out
 
    def get_level(self, handle):
        level = {}
        for obj, handle in self.db.find_backlink_handles(handle, ['Place']):
            place = self.db.get_place_from_handle(handle)
            level[place.get_name().get_value()] = handle
        return level
 
    def get_countries(self):
        countries = {}
        for handle in self.db.find_place_child_handles(''):
            place = self.db.get_place_from_handle(handle)
            if int(place.get_type()) != PlaceType.UNKNOWN:
                countries[place.get_name().get_value()] = handle
        return countries
 
#------------------------------------------------------------------------
#
# GeneratePlaceOptions
#
#------------------------------------------------------------------------
class GeneratePlaceOptions(tool.ToolOptions):
    """
    Define options and provides handling interface.
    """
 
    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)