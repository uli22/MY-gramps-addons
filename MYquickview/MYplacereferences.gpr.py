#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Benny Malengier
# Copyright (C) 2011       Tim G L Lyons
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
from gramps.gen.plug._pluginreg import *
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

MODULE_VERSION="5.1"

#------------------------------------------------------------------------
#
# MYReferences
#
#------------------------------------------------------------------------

refitems = [(CATEGORY_QR_PLACE, 'place', _("Place"))]

for (category, item, trans) in refitems:
    register(QUICKREPORT,
        id    = item + 'references',
        name  = _("%s MYReferences") % trans,
        description =  _("Display references for a %s") % trans,
        version = '1.0',
        gramps_target_version = MODULE_VERSION,
        status = STABLE,
        fname = 'MYplacereferences.py',
        authors = ["Hans Ulrich Frink"],
        authors_email = ["hansulrich.frink@gmail.com"],
        category = category,
        runfunc = 'run_%s' % item
        )

#register(QUICKREPORT,
#  id    = 'link_references',
#  name  = _("Link References"),
#  description =  _("Display link references for a note"),
#  version = '1.0',
#  gramps_target_version = MODULE_VERSION,
#  status = STABLE,
#  fname = 'linkreferences.py',
#  authors = ["Douglas Blank"],
#  authors_email = ["doug.blank@gmail.com"],
#  category = CATEGORY_QR_NOTE,
#  runfunc = 'run'
#)
