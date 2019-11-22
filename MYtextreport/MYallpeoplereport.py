#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013-2014  Hans Ulrich Frink
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

"""MYAllPeople Report"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.plug.menu import (FilterOption, PlaceListOption,
                                  EnumeratedListOption, BooleanOption)
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle,
                                    TableStyle, TableCellStyle,
                                    FONT_SANS_SERIF, FONT_SERIF, 
                                    INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from gramps.gen.sort import Sort
from gramps.gen.utils.location import get_location_list
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.lib import PlaceType
from gramps.gen.errors import ReportError

class MYAllPeopleReport(Report):
    """
    MYAllPeople Report class
    """
    def __init__(self, database, options, user):
        """
        Create the PlaceReport object produces the Place report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - instance of a gen.user.User class

        This report needs the following parameters (class variables)
        that come in the options class.
        
        places          - List of places to report on.
        center          - Center of report, person or event
        incl_private    - Whether to include private data
        name_format     - Preferred format to display names

        """

        Report.__init__(self, database, options, user)

        self._user = user
        menu = options.menu

        self.set_locale(menu.get_option_by_name('trans').get_value())

        self.sort = Sort(self.database)

        self.person_handles=[h for h in self.database.iter_person_handles()]
        self.family_handles=[h for h in self.database.iter_family_handles()]
        self.place_handles=[h for h in self.database.iter_place_handles()]
        self.citation_handles=[h for h in self.database.iter_citation_handles()]
        self.source_handles=[h for h in self.database.iter_source_handles()]
        self.note_handles=[h for h in self.database.iter_note_handles()]
        self.media_handles=[h for h in self.database.iter_media_handles()]
        self.repository_handles=[h for h in self.database.iter_repository_handles()]
        self.event_handles=[h for h in self.database.iter_event_handles()]

        print("Länge", len(self.person_handles))
#        self.person_handles.sort(key=self.sort.by_place_title_key)

    def write_report(self):
        """
        The routine that actually creates the report.
        At this point, the document is opened and ready for writing.
        """

        # Write the title line. Set in INDEX marker so that this section will be
        # identified as a major category if this is included in a Book report.

        title = self._("all persons Report")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)        
        self.doc.start_paragraph("PLC-ReportTitle")
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        self.doc.start_table("PersonTable", "PLC-EventTable")
        column_titles = [_("LNr"), _("handle"), _("Person")] 
                    
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("PLC-Details")
            self.doc.start_paragraph("PLC-Details")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()     

        self.__write_all_persons()
                
    def __write_all_persons(self):
        """
        This procedure writes out each of the selected places.
        """
        person_nbr = 1
        print(len(self.person_handles))

        with self._user.progress(_("Person Report"), 
                                  _("Generating report"), 
                                  len(self.person_handles)) as step:
            
            for handle in self.person_handles:
                self.__write_person(handle, person_nbr)
                person_nbr += 1
                # increment progress bar
                step()
 
        family_nbr = 1
        print(len(self.family_handles))
        with self._user.progress(_("Family Report"), 
                                  _("Generating report"), 
                                  len(self.family_handles)) as step:
            
            for handle in self.family_handles:
                self.__write_family(handle, family_nbr)
                family_nbr += 1
                # increment progress bar
                step() 

        source_nbr = 1
        print(len(self.source_handles))
        with self._user.progress(_("Source Report"), 
                                  _("Generating report"), 
                                  len(self.source_handles)) as step:
            
            for handle in self.source_handles:
                self.__write_source(handle, source_nbr)
                source_nbr += 1
                # increment progress bar
                step()

        citation_nbr = 1
        print(len(self.citation_handles))                
        with self._user.progress(_("Citation Report"), 
                                  _("Generating report"), 
                                  len(self.citation_handles)) as step:
            
            for handle in self.citation_handles:
                self.__write_citation(handle, citation_nbr)
                citation_nbr += 1
                # increment progress bar
                step() 

 
        place_nbr = 1
        print(len(self.place_handles))
        with self._user.progress(_("Place Report"), 
                                  _("Generating report"), 
                                  len(self.place_handles)) as step:
            
            for handle in self.place_handles:
                self.__write_place(handle, place_nbr)
                place_nbr += 1
                # increment progress bar
                step()

        repository_nbr = 1
        print(len(self.repository_handles))
        with self._user.progress(_("Repository Report"), 
                                  _("Generating report"), 
                                  len(self.repository_handles)) as step:
            
            for handle in self.repository_handles:
                self.__write_repository(handle, repository_nbr)
                repository_nbr += 1
                # increment progress bar
                step() 

 
        media_nbr = 1
        print(len(self.media_handles))
        with self._user.progress(_("Media Report"), 
                                  _("Generating report"), 
                                  len(self.media_handles)) as step:
            
            for handle in self.media_handles:
                self.__write_media(handle, media_nbr)
                media_nbr += 1
                # increment progress bar
                step()

        event_nbr = 1
        print(len(self.event_handles))
        with self._user.progress(_("Event Report"), 
                                  _("Generating report"), 
                                  len(self.event_handles)) as step:
            
            for handle in self.event_handles:
                self.__write_event(handle, event_nbr)
                event_nbr += 1
                # increment progress bar
                step()

        note_nbr = 1
        print(len(self.note_handles))                
        with self._user.progress(_("Note Report"), 
                                  _("Generating report"), 
                                  len(self.note_handles)) as step:
            
            for handle in self.note_handles:
                self.__write_note(handle, note_nbr)
                note_nbr += 1
                # increment progress bar
                step() 
                
    def __write_person(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            person = self.database.get_person_from_handle(handle)
            self.__write_row(nbr, handle, person)
        except:
            person = "NOT FOUND"
            self.__write_row(nbr, handle, person)
                
    def __write_family(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            family = self.database.get_family_from_handle(handle)
            self.__write_row(nbr, handle, family)
        except:
            family = "NOT FOUND"
            self.__write_row(nbr, handle, family)
                
    def __write_source(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            source = self.database.get_source_from_handle(handle)
            self.__write_row(nbr, handle, source)
        except:
            source = "NOT FOUND"
            self.__write_row(nbr, handle, source)
                
    def __write_citation(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            citation = self.database.get_citation_from_handle(handle)
            self.__write_row(nbr, handle, citation)
        except:
            citation = "NOT FOUND"
            self.__write_row(nbr, handle, citation)
                
    def __write_place(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            place = self.database.get_place_from_handle(handle)
            self.__write_row(nbr, handle, place)
        except:
            place = "NOT FOUND"
            self.__write_row(nbr, handle, place)
                
    def __write_note(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            note = self.database.get_note_from_handle(handle)
            self.__write_row(nbr, handle, note)
        except:
            note = "NOT FOUND"
            self.__write_row(nbr, handle, note)
                                
    def __write_media(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            media = self.database.get_media_from_handle(handle)
            self.__write_row(nbr, handle, media)
        except:
            media = "NOT FOUND"
            self.__write_row(nbr, handle, media)
                
    def __write_event(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            event = self.database.get_event_from_handle(handle)
            self.__write_row(nbr, handle, event)
        except:
            event = "NOT FOUND"
            self.__write_row(nbr, handle, event)
    
    def __write_repository(self, handle, nbr):
        """
        This procedure writes out the details of a single place
        """
        try:
            repository = self.database.get_repository_from_handle(handle)
            self.__write_row(nbr, handle, repository)
        except:
            repository = "NOT FOUND"
            self.__write_row(nbr, handle, repository)
                        
    def __write_row(self, nbr, handle, text):

        self.doc.start_row()

        self.doc.start_cell("PLC-Cell")
        self.doc.start_paragraph("PLC-Details")
        self.doc.write_text("%s " % nbr)
        self.doc.end_paragraph()
        self.doc.end_cell()

        self.doc.start_cell("PLC-Cell")
        self.doc.start_paragraph("PLC-Details")
        self.doc.write_text("%s " % handle)
        self.doc.end_paragraph()
        self.doc.end_cell()
        
        self.doc.start_cell("PLC-Cell")
        self.doc.start_paragraph("PLC-Details")
        self.doc.write_text("%s " % text)
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
    
#------------------------------------------------------------------------
#
# MYPlaceOptions
#
#------------------------------------------------------------------------
class MYAllPeopleOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the place report.
        """
        category_name = _("Report Options")

        stdoptions.add_localization_option(menu, category_name)

    def make_default_style(self, default_style):
        """
        Make the default output style for the Place report.
        """
        self.default_style = default_style
        self.__report_title_style()
        self.__place_title_style()
        self.__place_details_style()
        self.__column_title_style()
        self.__section_style()
        self.__event_table_style()
        self.__details_style()
        self.__cell_style()
        self.__table_column_style()

    def __report_title_style(self):
        """
        Define the style used for the report title
        """
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)       
        para.set_description(_('The style used for the title of the report.'))
        self.default_style.add_paragraph_style("PLC-ReportTitle", para)

    def __place_title_style(self):
        """
        Define the style used for the place title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=12, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-1.5, lmargin=1.5)
        para.set_top_margin(0.75)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for place title.'))
        self.default_style.add_paragraph_style("PLC-PlaceTitle", para)

    def __place_details_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_description(_('The style used for place details.'))
        self.default_style.add_paragraph_style("PLC-PlaceDetails", para)

    def __column_title_style(self):
        """
        Define the style used for the event table column title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_description(_('The style used for a column title.'))
        self.default_style.add_paragraph_style("PLC-ColumnTitle", para)

    def __section_style(self):
        """
        Define the style used for each section
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, italic=0, bold=0)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-1.5, lmargin=1.5)
        para.set_top_margin(0.5)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for each section.'))
        self.default_style.add_paragraph_style("PLC-Section", para)

    def __event_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(5)
        table.set_column_width(0, 15)
        table.set_column_width(1, 15)
        table.set_column_width(2, 35)
        table.set_column_width(3, 20)
        table.set_column_width(4, 25)
        self.default_style.add_table_style("PLC-EventTable", table)
        table.set_width(100)
        table.set_columns(5)
        table.set_column_width(0, 35)
        table.set_column_width(1, 15)
        table.set_column_width(2, 25)
        table.set_column_width(3, 20)
        table.set_column_width(4, 25)
        self.default_style.add_table_style("PLC-PersonTable", table)
        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 20)
        table.set_column_width(1, 70)
        table.set_column_width(2, 10)
        self.default_style.add_table_style("PLC-LitTable", table)

    def __details_style(self):
        """
        Define the style used for person and event details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The style used for event and person details.'))
        self.default_style.add_paragraph_style("PLC-Details", para)

    def __cell_style(self):
        """
        Define the style used for cells in the event table
        """
        cell = TableCellStyle()
        self.default_style.add_cell_style("PLC-Cell", cell)

    def __table_column_style(self):
        """
        Define the style used for event table columns
        """
        cell = TableCellStyle()
        cell.set_bottom_border(1)
        self.default_style.add_cell_style('PLC-TableColumn', cell)
