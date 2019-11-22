#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Nick Hall
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id: CensusReport.py 2368 2014-02-15 19:10:23Z nick-h $

"""Census Report"""
#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.datehandler import get_date
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.lib import EventType
from gramps.gen.plug.menu import BooleanOption, PersonOption, EnumeratedListOption
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, TableStyle,
                             TableCellStyle, FONT_SANS_SERIF, INDEX_TYPE_TOC,
                             PARA_ALIGN_CENTER)
from gramps.gen.plug.report import Report, MenuReportOptions
from Census import ORDER_ATTR
from Census import (get_census_ids, get_census_id, get_census_columns,
                    get_report_columns, get_census_citation,
                    get_census_sources)
from gramps.gen.constfunc import cuni

#------------------------------------------------------------------------
#
# Internationalisation
#
#------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

#------------------------------------------------------------------------
#
# Private constants
#
#------------------------------------------------------------------------
TYPE_PERSON = 0
TYPE_SOURCE = 1
TYPE_BOTH = 2
TYPE_ALL = 3

#------------------------------------------------------------------------
#
# CensusReport
#
#------------------------------------------------------------------------
class CensusReport(Report):
    """
    Census Report class
    """
    def __init__(self, database, options_class, user):
        """
        Create the Census report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options_class   - instance of the Options class for this report
        user            - a gen.user.User() instance

        The following parameters are defined in the options class:
        
        pid       - Selected person.
        pg_break  - Whether to include page breaks between generations.

        """

        Report.__init__(self, database, options_class, user)

        menu = options_class.menu
        self.pgbrk = menu.get_option_by_name('pg_break').get_value()

        self.report_type = menu.get_option_by_name('report_type').get_value()

        pid = menu.get_option_by_name('pid').get_value()
        self.person = database.get_person_from_gramps_id(pid)
        if (self.person == None) :
            user.notify_error(_("Census Report"),
                              _("Person %s is not in the Database") % pid)

        self.src_handle = menu.get_option_by_name('src_handle').get_value()

    def write_report(self):
        """
        The routine the actually creates the report. At this point, the document
        is opened and ready for writing.
        """

        # Title
        name = name_displayer.display_formal(self.person)
        title = _("Census Report for %s") % name
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)        
        self.doc.start_paragraph("CEN-Title")
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        self.first_page = True
        if self.report_type in (TYPE_ALL, TYPE_SOURCE):
            for handle in self.database.get_event_handles():
                self.check_event(handle)
        else:
            for event_ref in self.person.get_event_ref_list():
                self.check_event(event_ref.ref)

    def check_event(self, handle):
        """
        Checks each event against the selection criteria.
        """
        event = self.database.get_event_from_handle(handle)
        if event.get_type() == EventType.CENSUS:
            citation = get_census_citation(self.database, event)
            if citation: # We may have census events with untagged sources.
                if self.report_type in (TYPE_SOURCE, TYPE_BOTH):
                    if citation.get_reference_handle() == self.src_handle:
                        self.write_census(event, citation)
                else:
                    if citation:
                        self.write_census(event, citation)

    def write_census(self, event, citation):
        """
        Called for each census.
        """
        if self.pgbrk and not self.first_page:
            self.doc.page_break()
            self.first_page = False
        
        # Date, Source, Place
        p_handle = event.get_place_handle()
        place = self.database.get_place_from_handle(p_handle)
        src_handle = citation.get_reference_handle()
        source = self.database.get_source_from_handle(src_handle)
        census_id = get_census_id(source)
        headings = [x[0] for x in get_report_columns(census_id)]

        # Census title
        self.doc.start_paragraph("CEN-Heading")
        self.doc.write_text(source.get_title())
        self.doc.end_paragraph()

        self.doc.start_table("centab", "CEN-HeadingTable")

        # Date
        self.write_heading(_("Date:"), get_date(event))
        
        # Source Reference
        self.write_heading(_("Citation:"), citation.get_page())

        # Address
        if place:
            self.write_heading(_("Address:"), place.get_title())
        else:
            self.write_heading(_("Address:"), "")

        # Blank line
        self.write_heading("", "")

        self.doc.end_table()
        self.doc.start_table("centab", "CEN-" + census_id)
       
        # People
        person_list = []
        e_handle = event.get_handle()
        for link in self.database.find_backlink_handles(
                                e_handle, include_classes=['Person']):
            person = self.database.get_person_from_handle(link[1])
            person_list.append(get_attributes(person, e_handle))

        # Heading row
        self.doc.start_row()

        for column in headings:
            self.doc.start_cell("CEN-ColumnCell")
            self.doc.start_paragraph("CEN-Column")
            self.doc.write_text(column)
            self.doc.end_paragraph()
            self.doc.end_cell()
            
        self.doc.end_row()
        
        for row in sorted(person_list):
            self.doc.start_row()

            for offset, column in enumerate(get_census_columns(census_id)):
                self.doc.start_cell("CEN-BodyCell")
                if column == _('Name'):
                    self.doc.start_paragraph("CEN-Name")
                    self.doc.write_text(row[2].get(column, row[1]))
                else:
                    self.doc.start_paragraph("CEN-Normal")
                    if column in row[2]:
                        self.doc.write_text(row[2].get(column))

                self.doc.end_paragraph()
                self.doc.end_cell()
                
            self.doc.end_row()
            
        self.doc.end_table()

    def write_heading(self, title, value):
        """
        Writes a census heading.
        """
        self.doc.start_row()
        self.doc.start_cell("CEN-HeadingCell")
        self.doc.start_paragraph("CEN-Normal")
        self.doc.write_text(title)
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.start_cell("CEN-HeadingCell")
        self.doc.start_paragraph("CEN-Normal")
        self.doc.write_text(value)
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()

#------------------------------------------------------------------------
#
# Helper functions
#
#------------------------------------------------------------------------
def get_attributes(person, event_handle):
    """
    Return the row number of the person in the census along with a
    dictionary of attributes.
    """
    attrs = {}
    order = None
    for event_ref in person.get_event_ref_list():
        if event_ref.ref == event_handle:
            for attr in event_ref.get_attribute_list():
                if cuni(attr.get_type()) == ORDER_ATTR:
                    order = int(attr.get_value())
                else:
                    attrs[cuni(attr.get_type())] = attr.get_value()

    return (order, name_displayer.display_formal(person), attrs)

#------------------------------------------------------------------------
#
# CensusOptions
#
#------------------------------------------------------------------------
class CensusOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, database):
        self.database = database
        MenuReportOptions.__init__(self, name, database)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the ancestor report.
        """
        category_name = _("Report Options")
        
        report_type = EnumeratedListOption(_('Census Selection'), TYPE_PERSON)
        report_type.add_item(TYPE_PERSON, _('By Person'))
        report_type.add_item(TYPE_SOURCE, _('By Source'))
        report_type.add_item(TYPE_BOTH, _('By Person and Source'))
        report_type.add_item(TYPE_ALL, _('All Census records'))
        report_type.set_help(_("The type of report"))
        menu.add_option(category_name, "report_type", report_type)
        
        pid = PersonOption(_("Person"))
        pid.set_help(_("The selected person for the report."))
        menu.add_option(category_name, "pid", pid)

        default = None
        sources = get_census_sources(self.database)
        if len(sources) > 0:
            if len(sources[0]) > 0:
                default = sources[0][0]
        src_handle = EnumeratedListOption(_('Source'), default)
        for source in sources:
            src_handle.add_item(source[0], source[1])
        menu.add_option(category_name, "src_handle", src_handle)
        
        pg_break = BooleanOption(_("Page break after each census."), False)
        pg_break.set_help(_("Start a new page after each census."))
        menu.add_option(category_name, "pg_break", pg_break)
        
    def make_default_style(self, default_style):
        """
        Make the default output style for the Census report.
        """
        #
        # CEN-Title
        #
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)       
        para.set_description(_('The style used for the title of the page.'))
        default_style.add_paragraph_style("CEN-Title", para)
    
        #
        # CEN-Heading
        #
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=14, italic=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set_top_margin(0.5)
        para.set_bottom_margin(0.125)        
        para.set_description(_('The style used for headings.'))
        default_style.add_paragraph_style("CEN-Heading", para)
    
        #
        # CEN-Name
        #
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The style used for names.'))
        default_style.add_paragraph_style("CEN-Name", para)
        
        #
        # CEN-Column
        #
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10, italic=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The style used for column headings.'))
        default_style.add_paragraph_style("CEN-Column", para)
        
        #
        # CEN-Normal
        #
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        #para.set(first_indent=-1.0, lmargin=1.0)
        para.set_description(_('The default text style.'))
        default_style.add_paragraph_style("CEN-Normal", para)

        #
        # Table Styles
        #
        for census_id in get_census_ids():
            columns = get_report_columns(census_id)
            tbl = TableStyle()
            tbl.set_width(100)
            tbl.set_columns(len(columns))
            for index, column in enumerate(columns):
                tbl.set_column_width(index, column[1])
            default_style.add_table_style("CEN-" + census_id, tbl)

        #
        # CEN-HeadingTable
        #
        tbl = TableStyle()
        tbl.set_width(100)
        tbl.set_columns(2)
        tbl.set_column_width(0, 30)
        tbl.set_column_width(1, 70)
        default_style.add_table_style("CEN-HeadingTable", tbl)
        
        #
        # CEN-HeadingCell
        #
        cell = TableCellStyle()
        default_style.add_cell_style("CEN-HeadingCell", cell)
        
        #
        # CEN-ColumnCell
        #
        cell = TableCellStyle()
        cell.set_left_border(1)
        cell.set_right_border(1)
        default_style.add_cell_style("CEN-ColumnCell", cell)
        
        #
        # CEN-BodyCell
        #
        cell = TableCellStyle()
        cell.set_left_border(1)
        cell.set_right_border(1)
        cell.set_top_border(1)
        cell.set_bottom_border(1)
        default_style.add_cell_style("CEN-BodyCell", cell)
