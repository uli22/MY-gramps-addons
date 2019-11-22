#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2012       Hans Ulrich Frink
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
# Version 4.2
# $Id: SourcesCitationsReport.py 2014-06-19 Frink hansulrich.frink@gmail.com $

"""
Reports/Text Report.

Developed for gramps 4.2 under win 8 64bit

PLEASE FEEL FREE TO CORRECT AND TEST.

This report lists all the citations and their notes in the database. so it 
is possible to have all the copies made from e.g. parish books together grouped 
by source and ordered by citation.page.

I needed such a report after I changed recording notes and media with the
citations and no longer with the sources.

works well in pdf, text and odf Format. The latter contains TOC which are also
accepted by ms office 2010 

Changelog:

Version 2.5:
- sources are sorted by source.author+title+publ+abbrev
- no German non translatables
- added Filter cf. PlaceReport.py
- changed citasource from gramps_id to citation rsp. source

Version 3.3:
- constructing dic directly
- or function
- sorting direct 
- Stylesheet in Options

Version 3.4:
- added .lower to sortfunctions to sources and to citation

Version 3.5: 
- get translation work
- include Persons names and gramps_id cited in the notes.

Version 3.6: 
- show relation to Indexperson    

Version 3.7:
- have footer
- replace Anno YYYY by local Datestring 
- sources sort by Editor+Name
- Person table on Family events with relation to bride and groom
- Person table in own subroutine

Version 4.2:
- adapted for gramps 4.2


Known issues:
-Translation of Relation
-Translation of and


next steps:

- have an index on Persons   
       

"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import datetime, time
from collections import defaultdict

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------

from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.const import URL_HOMEPAGE
from gramps.gen.errors import ReportError
from gramps.gen.lib import NameType, EventType, Name, Date, Person, Surname
from gramps.gen.lib.date import gregorian
from gramps.gen.relationship import get_relationship_calculator
from gramps.gen.plug.docgen import (FontStyle, ParagraphStyle, GraphicsStyle,
                                    TableStyle, TableCellStyle,
                                    FONT_SERIF, PARA_ALIGN_RIGHT,
                                    PARA_ALIGN_LEFT, PARA_ALIGN_CENTER,
                                    IndexMark, INDEX_TYPE_TOC)
from gramps.gen.plug.menu import (BooleanOption, StringOption, NumberOption, 
                                  EnumeratedListOption, FilterOption, MediaOption,
                                  PersonOption, PlaceListOption, EnumeratedListOption,)
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.utils.string import conf_strings
from gramps.gen.utils.db import (find_children, find_parents, find_witnessed_people,
                                 get_age, get_timeperiod, preset_name)

import gramps.plugins.lib.libholiday as libholiday

# localization for BirthdayOptions only!!
from gramps.gen.datehandler import displayer as _dd
from gramps.gen.datehandler import get_date

def _T_(value): # enable deferred translations (see Python docs 22.1.3.4)
    return value
# _T_ is a gramps-defined keyword -- see po/update_po.py and po/genpot.sh

_TITLE0 = _T_("Birthday and Anniversary Report")
_TITLE1 = _T_("My Birthday Report")
_TITLE2 = _T_("Produced with Gramps")

#------------------------------------------------------------------------
#
# MarriageregisterReport
#
#------------------------------------------------------------------------
class MarriageregisterReport(Report):
    """
    This report produces a summary of the objects in the database.
    """
    def __init__(self, database, options, user):
        """
        Create the SourceReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User() instance

        This report needs the following parameters (class variables)
        that come in the options class.
        
        Sources          - List of places to report on.
        """

        Report.__init__(self, database, options, user)
        self._user = user
        self.__db = database
       
        menu = options.menu
        self.title_string = menu.get_option_by_name('title').get_value()
        self.subtitle_string = menu.get_option_by_name('subtitle').get_value()
        self.footer_string = menu.get_option_by_name('footer').get_value()
        self.showperson = menu.get_option_by_name('showperson').get_value()

        
        filter_option = menu.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
#        self.sort = Sort.Sort(self.database)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of source handles
            sourcefilterlist = self.__db.iter_source_handles()
            self.source_handles = self.filter.apply(self.__db, sourcefilterlist)
        else:
            self.source_handles = self.__db.get_source_handles()

#        name_format = menu.get_option_by_name("name_format").get_value()
#        if name_format != 0:
#            self._name_display.set_default_format(name_format)
#        self._nd = self._name_display

    def write_report(self):
        """
        Overridden function to generate the report.
        """
        self._user.begin_progress(_('BurialRegister Report'), 
                                  _('printing...'), 100)
        self.doc.start_paragraph("SRC-ReportTitle")
        title = self.title_string
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)  
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SRC-ReportTitle")
        title = self.subtitle_string
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)  
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()
        
        self.listeventref()
        
        self.doc.start_paragraph('SRC-Footer')
        self.doc.write_text(self.footer_string)
        self.doc.end_paragraph()
        self._user.end_progress()
        
    def _formatlocal_source_text(self, source):
        if not source: return
    
        src_txt = ""
        
        if source.get_author():
            src_txt += source.get_author()
        
        if source.get_title():
            if src_txt:
                src_txt += ", "
            src_txt += '"%s"' % source.get_title()
            
        if source.get_publication_info():
            if src_txt:
                src_txt += ", "
            src_txt += source.get_publication_info()
            
        if source.get_abbreviation():
            if src_txt:
                src_txt += ", "
            src_txt += "(%s)" % source.get_abbreviation()
            
        return src_txt
        
    def listeventref(self):
    
        sc = {'source': 'S_ID',
              'citalist': 'C_ID' }
        stc = {}      
        citation_without_notes = 0
        EMPTY = " "

        def toYear(date):
            yeartext = date.get_year()
            return yeartext
 
        # build citation list cl
             
        cl = []
        i=1
        for ci in self.__db.iter_citations():
            if ci.source_handle in self.source_handles:
#                sc[ci.source_handle].append(ci.handle)
                cl.append(ci.handle)

        # build citations - event dic                       xy
        #(a,b): set([('Citation', 'c4a8c46041e08799b17')]) 
        # event: c4a8c4f95b01e38564a event: Taufe
        #!!     # Nur Taufen !
        ci = defaultdict(list)
        for ev in self.__db.iter_events():
            if ev.type.is_marriage():
                evcithandlelist = ev.get_referenced_citation_handles()   
                for (a,b) in evcithandlelist:
                    if b in cl:
                         ci[b].append(ev.handle)
        cikeys = ci.keys()
        for di in cikeys:
            print ((di), di in cl)
        print (len(cikeys))    
        
        print ("CITA", len(ci.keys()), len(sc.values())   )
 #       print ("SOURCE", len(sc.keys()), len(sc.values()), len(sc[0]) )
                        
        # build citasource dictionary 
        
        sc = defaultdict(list)
        for ci2 in self.__db.iter_citations():
            if ci2.handle in cikeys:
                print("HALLO    ",  ci2, ci2.source_handle)
                sc[ci2.source_handle].append(ci2.handle)

        sckeys = sc.keys()
        for di in sckeys:
            print ((di), sc[di])
        print (len(sckeys), len(sc[di]))  

        # build eventpersonrole dictionary
        # event: c4a8c4f95b01e38564a event: Taufe
        refhandlelist =[]
        pedic ={}
        pedic = defaultdict(list)

        for pe in self.__db.get_person_handles():
            for eventref in self.__db.get_person_from_handle(pe).event_ref_list:
                pedic[eventref.ref].append((eventref.get_role(),pe))

#        #source
#        skeys = sc.keys()
#        skeys.sort(key=lambda x:self._formatlocal_source_text(self.__db.get_source_from_handle(x)))
#        for s in skeys:
        for s in sorted(sc.keys()):
            self._user.step_progress()
            self.doc.start_paragraph("SRC-SourceTitle")
            self.doc.write_text(self._formatlocal_source_text(self.__db.get_source_from_handle(s)))
            self.doc.end_paragraph()       
         
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("   ID: %s") %
                                self.__db.get_source_from_handle(s).gramps_id) 
            self.doc.end_paragraph()  

            # note in sources
            for sourcenotehandle in self.__db.get_source_from_handle(s).get_note_list():
                self.doc.start_paragraph("SRC-NoteDetails")
                self.doc.write_text(_("   Type: %s") %
                                    self.__db.get_note_from_handle(sourcenotehandle).type) 
                self.doc.write_text(_("   N-ID: %s") %
                                    self.__db.get_note_from_handle(sourcenotehandle).gramps_id) 
                self.doc.end_paragraph()

                self.doc.start_paragraph("SRC-NoteText")
                self.doc.write_text(_("   %s") %
                                    self.__db.get_note_from_handle(sourcenotehandle).text) 
                self.doc.end_paragraph()

            self.doc.start_table("EventTable", "SRC-EventTable")
            column_titles = [_("LNr"), _("Source"), _("Date"),_("Person"),_("Parents"),
                             _("Age / Wittness"),_("Text")] 
            self.doc.start_row()
            for title in column_titles:
                self.doc.start_cell("SRC-TableColumn")
                self.doc.start_paragraph("SRC-ColumnTitle")
                self.doc.write_text(title)
                self.doc.end_paragraph()
                self.doc.end_cell()
            self.doc.end_row()              
                
                
            i = 1
            ckeys = sc[s]
            ckeys.sort(key=lambda x:self.__db.get_citation_from_handle(x).page)
            for c in ckeys:                                     
                       # c contains citationhandles      
                self._user.step_progress()
                self.doc.start_row()
                self.doc.start_cell("SRC-TableColumn")   
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%d") %
                                    i)  
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                self.doc.start_cell("SRC-TableColumn")   
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("  %s") %
                                    self.__db.get_citation_from_handle(c).page)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                self.doc.start_cell("SRC-TableColumn")   
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text (_(" %s ") % get_date(self.__db.get_citation_from_handle(c)))
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                self.doc.start_cell("SRC-TableColumn")   
                self.doc.start_paragraph("SRC-SourceDetails")

                for e in ci[c]:
                    event = self.__db.get_event_from_handle(e)
                    self.doc.write_text(_("%s") %
                                  event.get_type())
                    self.doc.write_text(_("   ( %s )") %
                                  event.gramps_id)
                self.doc.end_paragraph()
                self.doc.end_cell()

                # Brautleute

                self.doc.start_cell("SRC-TableColumn")   
                self.doc.start_paragraph("SRC-SourceDetails")
                for e in ci[c]:
                    event = self.__db.get_event_from_handle(e)

                    ref_handles = [x for x in
                               self.database.find_backlink_handles(e)]
    #               print(mi, evt_handle)
                    for (ref_type, ref_handle) in ref_handles:
                        if ref_type == 'Person':
                            continue
                        else:
                            family = self.database.get_family_from_handle(ref_handle)
                            father_handle = family.get_father_handle()
                            mother_handle = family.get_mother_handle()

                            if father_handle:
                                fp = self.database.get_person_from_handle(father_handle)
                                father_name = \
                                    fp.primary_name.get_name()
#                                    self._name_display.display_name(fp.get_primary_name()).lower()
                                father_name = father_name+(_(" [%s]")%fp.gramps_id)
                            else:
                                father_name = _("unknown")


                            if mother_handle:
                                mp = self.database.get_person_from_handle(mother_handle)
                                mother_name = \
                                    mp.primary_name.get_name()
#                                    self._name_display.display_name(fp.get_primary_name()).lower()
                                mother_name = mother_name+(_(" [%s]")%mp.gramps_id)
                            else:
                                mother_name = _("unknown")
                            famo_name = father_name+" "+mother_name
                    self.doc.write_text(_("%s") %
                                  famo_name)

                self.doc.end_paragraph()
                self.doc.end_cell()

                self.doc.end_row()
                i += 1
            self.doc.end_table()                  

#------------------------------------------------------------------------
#
# MarriageregisterOptions
#
#------------------------------------------------------------------------
class MarriageregisterOptions(MenuReportOptions):
    """
    SourcesAllCitationsAndPersonsOptions provides the options 
    for the SourcesAllCitationsAndPersonsReport.
    """
    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)

        
     
    def add_menu_options(self, menu):
        """ Add the options for this report """
        category_name = _("Report Options")
        
        title = StringOption(_('book|Title'), _('Title of the Book') )
        title.set_help(_("Title string for the book."))
        menu.add_option(category_name, "title", title)
        
        subtitle = StringOption(_('Subtitle'), _('Subtitle of the Book') )
        subtitle.set_help(_("Subtitle string for the book."))
        menu.add_option(category_name, "subtitle", subtitle)
        
        dateinfo = time.localtime(time.time())
        #rname = self.__db.get_researcher().get_name()
        rname = "researcher name"
 
        footer_string = _('Copyright %(year)d %(name)s') % {
            'year' : dateinfo[0], 'name' : rname }
        footer = StringOption(_('Footer'), footer_string )
        footer.set_help(_("Footer string for the page."))
        menu.add_option(category_name, "footer", footer)
        
        # Reload filters to pick any new ones
        CustomFilters = None
        from gramps.gen.filters import CustomFilters, GenericFilter

        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Source'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)
        
#        stdoptions.add_name_format_option(menu, category_name)
        
        showperson = BooleanOption(_("Show persons"), True)
        showperson.set_help(_("Whether to show events and persons mentioned in the note"))
        menu.add_option(category_name, "showperson", showperson)

    def make_default_style(self, default_style):
        """
        Make the default output style for the Place report.
        """
        self.default_style = default_style
        self.__report_title_style()
        self.__source_title_style()
        self.__source_details_style()
        self.__citation_title_style()
        self.__column_title_style()
        self.__note_details_style()
        self.__note_text_style()
        self.__section_style()
        self.__event_table_style()
        self.__details_style()
        self.__cell_style()
        self.__table_column_style()
        self.__report_footer_style()

    def __report_title_style(self):
        """
        Define the style used for the report title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)       
        para.set_description(_('The style used for the title of the report.'))
        self.default_style.add_paragraph_style("SRC-ReportTitle", para)

    def __source_title_style(self):
        """
        Define the style used for the source title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=12, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_top_margin(0.75)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for source title.'))
        self.default_style.add_paragraph_style("SRC-SourceTitle", para)
   
    def __report_footer_style(self):
        """
        Define the style used for the report footer
        """        
        
        font = FontStyle()
        font.set_size(8)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_top_border(True)
        para.set_top_margin(ReportUtils.pt2cm(8))
        para.set_description(_('The style used for the footer.'))
        self.default_style.add_paragraph_style('SRC-Footer', para)
     
        
    def __citation_title_style(self):
        """
        Define the style used for the citation title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=12, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(3)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_top_margin(0.75)
        para.set_bottom_margin(0.0)        
        para.set_description(_('The style used for citation title.'))
        self.default_style.add_paragraph_style("SRC-CitationTitle", para)

    def __source_details_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_description(_('The style used for Source details.'))
        self.default_style.add_paragraph_style("SRC-SourceDetails", para)

    def __note_details_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_description(_('The style used for Note details.'))
        self.default_style.add_paragraph_style("SRC-NoteDetails", para)

    def __note_text_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=0.0)
        para.bgcolor = (255,0,0)
        para.set_description(_('The style used for Note Text.'))
        para.set_top_border(True)
        para.set_left_border(True)
        para.set_right_border(True)
        para.set_bottom_border(True)
        self.default_style.add_paragraph_style("SRC-NoteText", para)




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
        self.default_style.add_paragraph_style("SRC-ColumnTitle", para)

    def __section_style(self):
        """
        Define the style used for each section
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, italic=0, bold=0)
        para = ParagraphStyle()
        para.set_font(font)
#        para.set(first_indent=-1.5, lmargin=1.5)
        para.set(first_indent=0.0, lmargin=0.0)

        para.set_top_margin(0.5)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for each section.'))
        self.default_style.add_paragraph_style("SRC-Section", para)

    def __event_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(200)
        table.set_columns(8)
        table.set_column_width(0,  4)
        table.set_column_width(1, 15)
        table.set_column_width(2, 15)
        table.set_column_width(3, 15)
        table.set_column_width(4, 20)
        table.set_column_width(5, 20)
        table.set_column_width(6, 35)
        table.set_column_width(7, 35)
        self.default_style.add_table_style("SRC-EventTable", table)

        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 35)
        table.set_column_width(1, 15)
        table.set_column_width(2, 35)

        self.default_style.add_table_style("SRC-PersonTable", table)


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
        self.default_style.add_cell_style("SRC-Cell", cell)

    def __table_column_style(self):
        """
        Define the style used for event table columns
        """
        cell = TableCellStyle()
        cell.set_bottom_border(1)
        self.default_style.add_cell_style('SRC-TableColumn', cell)
       