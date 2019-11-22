# encoding:utf-8
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Benny Malengier
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

MODULE_VERSION="5.0" 

#------------------------------------------------------------------------
#
# Database Summary Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'MYsummary'
plg.name  = _("Database - MY- Summary Report")
plg.description =  _("Provides a detailed summary of the current database")
plg.version = '1.0'
plg.gramps_target_version = MODULE_VERSION
plg.status = STABLE
plg.fname = 'MYsummary.py'
plg.ptype = REPORT
plg.authors = ["Hans Ulrich Frink"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'MYSummaryReport'
plg.optionclass = 'MYSummaryOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False
