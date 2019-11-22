#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008,2011  Gary Burton
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Heinz Brinker
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

# $Id: PlaceReport.py 18651 2011-12-24 19:08:19Z paul-franklin $

"""Place Report"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import datetime, time
from collections import defaultdict
#######################################
#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------

from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.const import URL_HOMEPAGE
from gramps.gen.errors import ReportError
from gramps.gen.lib import NameType, EventType, EventRoleType, Name, Date, Person, Surname

from gramps.gen.lib.date import gregorian
#from gramps.gen.relationship import get_relationship_calculator
from gramps.gen.plug.docgen import (FontStyle, ParagraphStyle, GraphicsStyle,
                                    TableStyle, TableCellStyle,
                                    FONT_SERIF, PARA_ALIGN_RIGHT,
                                    PARA_ALIGN_LEFT, PARA_ALIGN_CENTER,
                                    IndexMark, INDEX_TYPE_TOC)
from gramps.gen.plug.menu import (BooleanOption, StringOption, NumberOption, 
                                  EnumeratedListOption, FilterOption, MediaOption,
                                  PersonOption, PlaceListOption, EnumeratedListOption,)
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.utils.string import conf_strings
from gramps.gen.sort import Sort
from gramps.gen.proxy import PrivateProxyDb
from gramps.gen.utils.location import get_main_location

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

#######################################

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
#from gen.plug.menu import FilterOption, PlaceListOption, EnumeratedListOption, \
#                          BooleanOption
#from gen.plug.report import Report
#from gen.plug.report import MenuReportOptions
#from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, TableStyle,
#                            TableCellStyle, FONT_SANS_SERIF, FONT_SERIF, 
#                            INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
#from gen.proxy import PrivateProxyDb   
#from gen.lib import EventRoleType, EventType, Person   
#import DateHandler
#import Sort
#from gen.display.name import displayer as _nd

def StatTree():
        return defaultdict(StatTree)    


class PeopleStatBuDReport(Report):
    """
    Place Report class
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
        incpriv         - Whether to include private data

        """

        Report.__init__(self, database, options, user)

        self._user = user
        menu = options.menu
        places = menu.get_option_by_name('places').get_value()
        self.incpriv = menu.get_option_by_name('incpriv').get_value()

        if self.incpriv:
            self.__db = database
        else:
            self.__db = PrivateProxyDb(database)


        filter_option = menu.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
        self.sort = Sort(self.__db)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of place handles
            plist = self.__db.iter_place_handles()
            self.place_handles = self.filter.apply(self.__db, plist)
        else:
            # Use the place handles selected without a filter
            self.place_handles = self.__get_place_handles(places)

        self.place_handles.sort(key=self.sort.by_place_title_key)

    def write_report(self):
        """
        The routine the actually creates the report. At this point, the document
        is opened and ready for writing.
        """

        # Write the title line. Set in INDEX marker so that this section will be
        # identified as a major category if this is included in a Book report.

        title = _("Place Report")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)        
        self.doc.start_paragraph("PLC-ReportTitle")
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()
        self.__write_all_places()
        self.count_data()

    def __write_all_places(self):
        """
        This procedure writes out each of the selected places.
        """
        place_nbr = 1

        self._user.begin_progress(_("Place Report"), 
                                  _("Generating report"), 
                                  len(self.place_handles))
        
        for handle in self.place_handles:
            self.__write_place(handle, place_nbr)
            place_nbr += 1
            # increment progress bar
            self._user.step_progress()
            
        self._user.end_progress()
        
    def count_data(self):
        """
        This procedure counts the data
        """

#***********************************************************************
#        # build Stat dictionary using recursive function tree()
#        # Stat[Place_handle][Year][EVT][Gender][CNT]
#               
#       Place_handle    place handle    self.__db.get_event_from_handle(eventref.ref).get_place_handle()
#       Year            self__db.get_event_from_handle(eventref.ref).get_date_object().get_year()
#       EVT             'BIRTH' etc.
#       Gender          ['m' 'w' 'u']                                  
#       CT              int
#

        genderlist = ['m','w','u']
              
        BIRTH = 'Birth'
        BAPT  = 'Bapt'
        DEATH = 'Death'
        BURR  = 'Burrial'
        CONFIRMATION = 'Confirmation'
        MARRIAGE = 'Marriage'
        
        sorttabledict ={'m':0,'w':1,'u':2,'ztotal':3}
        
        self._user.begin_progress(_("Place Stat Report"), 
                                  _("Generating report"), 
                                  100)
                                  
#                                  len(self.place_handles))

        Stat = StatTree()
        CT = 0
                
        for pe in self.__db.iter_people():
            EVT = BAPT
            for eventref in pe.event_ref_list:
                CT +=1
                if not eventref:
                    continue
                elif eventref.role != EventRoleType.PRIMARY:
                    # Only match primaries, no witnesses
                    continue
                if self.__db.get_event_from_handle(eventref.ref).get_date_object():
                    if self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.BAPTISM:
                        EVT = BAPT
#                       continue
                    elif self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.BIRTH:
                        if EVT == BAPT:
                            continue
                        else:
                            EVT = BIRTH
                            continue
                    elif self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.BURIAL:
                        EVT = BURR
                    elif self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.DEATH:
                        if EVT == BURR:
                            continue
                        else:
                            EVT = DEATH
                            continue
                    else:
                        continue    
                    Stat[self.__db.get_event_from_handle(eventref.ref).get_place_handle()][self.__db.get_event_from_handle(eventref.ref).get_date_object().get_year()][EVT][genderlist[pe.get_gender()]][CT] = "CNT"
                    
                # increment progress bar
                self._user.step_progress()

        self.doc.start_table("PersonRoleEventTable", "SRC-PersonEventRoleTable")
        column_titles = [_("year"), _("count"), _("m"), _("w"), _("u"),("total"), _("count"), _("m"), _("w"), _("u"),("total"), _("count"), _("m"), _("w"), _("u"),("total")] 
        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()
        
        Anzk = 0
        Sumv = 0    
        
        self.doc.start_row()
        
        self.doc.start_cell("SRC-TableColumn")
        self.doc.start_paragraph("SRC-ColumnTitle")
#        self.doc.write_text(_("Anzahl Elemente in Stat [ORTE]: %s") %
#                                    len(Stat)) 
        self.doc.write_text(_("[ORTE]: %s") %
                                    len(Stat)) 
        self.doc.end_paragraph()
        self.doc.end_cell()     
        
        self.doc.end_row()

#       Orte schreiben
# 
#####   self.place_handles

        StKeys  = Stat.keys()
#        for h in StKeys:
        for h in self.place_handles:

            self.doc.start_row()
     
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            try:
#                self.doc.write_text(_("Anzahl Elemente in Stat.keys: %s") %
                self.doc.write_text(_("Place: %s") %
                                        self.__db.get_place_from_handle(h).title)
            except:
#                self.doc.write_text(_("Anzahl Elemente in Stat.keys: %s") %
                self.doc.write_text(_("Place: %s") %
                                        "ohne Bezeichnung")
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("Anzahl jahr in Stat[i]: %s") %
#                                            len(Stat[h].keys())) 
            self.doc.write_text(_("%s") %
                                            len(Stat[h].keys())) 

            self.doc.end_paragraph()
            self.doc.end_cell()

            
            self.doc.end_row()

#       Jahre schreiben
#            
            for i in sorted(Stat[h].keys()):
                self.doc.start_row()
     
                self.doc.start_cell("SRC-TableColumn")
                self.doc.start_paragraph("SRC-ColumnTitle")
#                self.doc.write_text(_("Jahr in Stat[i]: %s") %
                self.doc.write_text(_("%s") %
                                            i) 
                self.doc.end_paragraph()
                self.doc.end_cell()
                
#       Init sumyear
                sumyeardic = {'m':'0' ,'w':'0', 'u':'0', 'ztotal':'0'}
                rowdic = {'m':'0' ,'w':'0', 'u':'0','ztotal':'0' }

#       Ereignisse schreiben
# 
                baptdru = 0
                burrdru = 0
                gesdru = 0
                for k in sorted(Stat[h][i].keys()):
#                    write BAPT or BURRIED
#                    self.doc.start_row()
      ##write BAPT              
                    if (baptdru == 0) and (burrdru == 0) and (k == BAPT):
                         rsum = 0
                         for gl in genderlist:
                             for l in Stat[h][i][k].keys():
                                 if l == gl:
                                     rowdic[gl] = str(len(Stat[h][i][k][l].keys()))
                                     rsum = rsum + len(Stat[h][i][k][l].keys())
                                     # increment progress bar
                                     self._user.step_progress()
                                 else:
                                     continue
                         rowdic['ztotal'] = str(rsum)             
                         sumyeardic = rowdic.copy( )
                         
                         
                         self.doc.start_cell("SRC-TableColumn")
                         self.doc.start_paragraph("SRC-ColumnTitle")
      #                   self.doc.write_text(_("Ereignis pro Jahr in Stat[h][k]: %s") %
                         self.doc.write_text(_("%s") %
                                                    k) 
                         self.doc.end_paragraph()
                         self.doc.end_cell()
      
                      
                         for gl in sorted(rowdic.keys(),key=sorttabledict.__getitem__):
                             self.doc.start_cell("SRC-TableColumn")
                             self.doc.start_paragraph("SRC-ColumnTitle")
                             self.doc.write_text(_("%s") %
                                                            rowdic[gl])
#                             self.doc.write_text(_("%s") %
 #                                                           gl)
                             self.doc.end_paragraph()
                             self.doc.end_cell()
                          # increment progress bar
                         self._user.step_progress()
                         baptdru = 1
                         gesdru += 1
                        
                    if (baptdru == 0) and (burrdru == 0) and (k == BURR):

                        ##Write LEER           
                        for ec in range(0,5):
                            self.doc.start_cell("SRC-TableColumn")
                            self.doc.start_paragraph("SRC-ColumnTitle")
                            self.doc.write_text(_("    "))
#                            self.doc.write_text(_("LEER %s") %
#                                                           len(Stat[h][i][k].keys()))

                            self.doc.end_paragraph()
                            self.doc.end_cell()
                        baptdru = 1    
  
#   ##write BURR
                    if (baptdru == 1) and (burrdru == 0) and (k == BURR):

                        rsum = 0
                        for gl in genderlist:
                            for l in Stat[h][i][k].keys():
                                if l == gl:
                                    rowdic[gl] = str(len(Stat[h][i][k][l].keys()))
                                    rsum = rsum + len(Stat[h][i][k][l].keys())
                                    # increment progress bar
                                    self._user.step_progress()
                                else:
                                    continue
                        rowdic['ztotal'] = str(rsum)             
#4.1                      for gl in sorted(rowdic.iterkeys(),key=sorttabledict.__getitem__):
                        for gl in sorted(rowdic.keys(),key=sorttabledict.__getitem__):
                             sumyeardic[gl]=str(int(sumyeardic[gl])-int(rowdic[gl]))

                        self.doc.start_cell("SRC-TableColumn")
                        self.doc.start_paragraph("SRC-ColumnTitle")
    #                    self.doc.write_text(_("Ereignis pro Jahr in Stat[h][k]: %s") %
                        self.doc.write_text(_("%s") %
                                                   k) 
                        self.doc.end_paragraph()
                        self.doc.end_cell()

                    
#4.1                        for gl in sorted(rowdic.iterkeys(),key=sorttabledict.__getitem__):
                        for gl in sorted(rowdic.keys(),key=sorttabledict.__getitem__):
                            self.doc.start_cell("SRC-TableColumn")
                            self.doc.start_paragraph("SRC-ColumnTitle")
                            self.doc.write_text(_("%s") %
                                                           rowdic[gl])
#                            self.doc.write_text(_("%s") %
 #                                                           gl)
                            self.doc.end_paragraph()
                            self.doc.end_cell()
                        # increment progress bar
                        self._user.step_progress()
                        burrdru = 1
                        gesdru = 2

                if (gesdru == 1):
                    ##Write LEER           
                    for ec in range(0,5):
                        self.doc.start_cell("SRC-TableColumn")
                        self.doc.start_paragraph("SRC-ColumnTitle")
                        self.doc.write_text(_("    "))
#                            self.doc.write_text(_("LEER %s") %
#                                                           len(Stat[h][i][k].keys()))


                        self.doc.end_paragraph()
                        self.doc.end_cell()
                    burrdru = 1


    ##write ZTOTAL
                   
                self.doc.start_cell("SRC-TableColumn")
                self.doc.start_paragraph("SRC-ColumnTitle")
                self.doc.write_text(_("ZTOTAL %s") %
                                               gesdru)
                self.doc.end_paragraph()
                self.doc.end_cell()

#4.1                for gl in sorted(sumyeardic.iterkeys(),key=sorttabledict.__getitem__):
                for gl in sorted(sumyeardic.keys(),key=sorttabledict.__getitem__):
                    self.doc.start_cell("SRC-TableColumn")
                    self.doc.start_paragraph("SRC-ColumnTitle")
                    self.doc.write_text(_("%s") %
                                                   sumyeardic[gl])
 #                   self.doc.write_text(_("%s") %
 #                                                           gl)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                self.doc.end_row()
               
           
                      
               #########################################################################
                                                     
        self.doc.end_table()
            
        self._user.end_progress()


        self.doc.start_table("RoleStatisticTable", "SRC-StatTable")
        stat_column_titles = [_("Relation"), _("count"), _("Percent")] 
        i = 0
        self.doc.start_row()
        for title in stat_column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()          
        
        self.doc.end_table()

               
 
    def __write_place(self, handle, place_nbr):
        """
        This procedure writes out the details of a single place
        """
        place = self.__db.get_place_from_handle(handle)
#p        location = place.get_main_location()
#        location = get_main_location(self.__db, place)
#
#        place_details = [_("Gramps ID: %s ") % place.get_gramps_id(),
#                         _("Street: %s ") % location.get_street(),
#                         _("Parish: %s ") % location.get_parish(),
#                         _("Locality: %s ") % location.get_locality(),
#                         _("City: %s ") % location.get_city(),
#                         _("County: %s ") % location.get_county(),
#                         _("State: %s") % location.get_state(),
#                         _("Country: %s ") % location.get_country()]
        self.doc.start_paragraph("PLC-PlaceTitle")
        self.doc.write_text(("%(nbr)s. %(place)s") % 
                                {'nbr' : place_nbr,
                                 'place' : place.get_title()})
        self.doc.end_paragraph()
        
        
        
    def __get_place_handles(self, places):
        """
        This procedure converts a string of place GIDs to a list of handles
        """
        place_handles = [] 
        for place_gid in places.split():
            place = self.__db.get_place_from_gramps_id(place_gid)
            if place is not None:
                #place can be None if option is gid of other fam tree
                place_handles.append(place.get_handle())

        return place_handles
    
#------------------------------------------------------------------------
#
# PeopleStatBuDOptions
#
#------------------------------------------------------------------------
class PeopleStatBuDOptions(MenuReportOptions):

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

        # Reload filters to pick any new ones
        CustomFilters = None
#p        from Filters import CustomFilters, GenericFilter
        from gramps.gen.filters import CustomFilters, GenericFilter
        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Place'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)

        places = PlaceListOption(_("Select places individually"))
        places.set_help(_("List of places to report on"))
        menu.add_option(category_name, "places", places)

        center = EnumeratedListOption(_("Center on"), "Event")
        center.set_items([
                ("Event",   _("Event")),
                ("Person", _("Person"))])
        center.set_help(_("If report is event or person centered"))
        menu.add_option(category_name, "center", center)

        incpriv = BooleanOption(_("Include private data"), True)
        incpriv.set_help(_("Whether to include private data"))
        menu.add_option(category_name, "incpriv", incpriv)

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
        self.__stat_table_style()


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
        self.default_style.add_paragraph_style("SRC-ColumnTitle", para)

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

    def __stat_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 35)
        table.set_column_width(1, 15)
        table.set_column_width(2, 15)

        self.default_style.add_table_style("SRC-StatTable", table)

    def __event_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 35)
        table.set_column_width(1, 15)
        table.set_column_width(2, 35)

        self.default_style.add_table_style("SRC-EventTable", table)
        
        table = TableStyle()
        table.set_width(100)
        table.set_columns(9)
        table.set_column_width(0, 5)
        table.set_column_width(1, 6)
        table.set_column_width(2, 8)
        table.set_column_width(3, 12)
        table.set_column_width(4, 25)
        table.set_column_width(5, 6)
        table.set_column_width(6, 25)
        table.set_column_width(7, 6)
        table.set_column_width(8, 10)
        table.set_column_width(7, 5)

        self.default_style.add_table_style("SRC-PersonEventRoleTable", table)      
            
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
        self.default_style.add_cell_style("PLC-Cell", cell)

    def __table_column_style(self):
        """
        Define the style used for event table columns
        """
        cell = TableCellStyle()
        cell.set_bottom_border(1)
        self.default_style.add_cell_style('PLC-TableColumn', cell)
        

        
