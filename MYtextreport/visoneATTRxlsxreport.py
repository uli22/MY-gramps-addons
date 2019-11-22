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
# Version 3.4
# $Id: PeopleCitationsReport.py 2012-12-30 Frink hansulrich.frink@gmail.com $

"""

Reports/Text Report.

Developed for gramps 3.4.2.1 under win 8 64bit

This report gives an adjescent matrix to be passed to VISONE as csv file.

So e.g. a network of godparents can be examined.

accepted by ms office 2012 

Changelog:

Version 1.0:
- OK  

next steps:

- ATTR file as well.  
- choose char set


"""


#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
#import posixpath
import time
########################################
#######################################
#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------

from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

from gramps.gen.plug.docgen import (FontStyle, ParagraphStyle,
                                    TableStyle, TableCellStyle,
                                    FONT_SERIF, PARA_ALIGN_CENTER,
                                    IndexMark, INDEX_TYPE_TOC)
from gramps.gen.plug.menu import (BooleanOption, StringOption, 
                                  EnumeratedListOption, FilterOption,
                                  EnumeratedListOption)
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.sort import Sort
from gramps.gen.utils.place import conv_lat_lon
from gramps.gen.utils.db import (get_age, get_birth_or_fallback, get_death_or_fallback)


# import gramps.plugins.lib.libholiday as libholiday

# localization for BirthdayOptions only!!
#from gramps.gen.datehandler import displayer as _dd
from gramps.gen.datehandler import get_date
from gramps.gen.display.place import displayer as _pd

def _T_(value): # enable deferred translations (see Python docs 22.1.3.4)
    return value
# _T_ is a gramps-defined keyword -- see po/update_po.py and po/genpot.sh

_TITLE0 = _T_("Birthday and Anniversary Report")
_TITLE1 = _T_("My Birthday Report")
_TITLE2 = _T_("Produced with Gramps")


#------------------------------------------------------------------------
#
# VisoneATTRXLSXReport
#
#------------------------------------------------------------------------
class VisoneATTRXLSXReport(Report):
    """
    This report produces .
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
        self.__db = database
        self._user = user
       
        menu = options.menu
        self.title_string = menu.get_option_by_name('title').get_value()
        self.subtitle_string = menu.get_option_by_name('subtitle').get_value()
        self.footer_string = menu.get_option_by_name('footer').get_value()

        menucalc = options.menu
        self.showallfamilies =menucalc.get_option_by_name('showallfamilies').get_value()
        
        filter_option = menucalc.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
        self.sort = Sort(self.database)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of source handles
            sourcefilterlist = self.__db.iter_source_handles()
            self.source_handles = self.filter.apply(self.__db, sourcefilterlist)
        else:
            self.source_handles = self.__db.get_source_handles()

        self.place_fmt = menu.get_option_by_name("place_format").get_value()

    def write_report(self):
        """
        Overridden function to generate the report.
        """
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
        
        self.listpersonref()
        
        self.doc.start_paragraph('SRC-Footer')
        self.doc.write_text(self.footer_string)
        self.doc.end_paragraph()


        
        
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

    def find_place_lat_lon(self, event):
        """
#        Use the most recent occupation residence.
#        """
        lat = " "
        lon = " "
        place_handle = event.get_place_handle()
        if place_handle:
            place =  self.__db.get_place_from_handle(place_handle)
            if place:
#                lat, lon = conv_lat_lon(place.get_latitude(), place.get_longitude(), format="D.D8")
                lat, lon = conv_lat_lon(place.get_latitude(), place.get_longitude(), format="DEG")
        return(lat, lon)


    def find_clan(self, person_handle):
        # returns a string composed of all surnames of her family  = clanname
        #
        family_list = []
        family_handle = None
        family_list = self.__db.get_person_from_handle(person_handle).get_family_handle_list()
        clanname =""
        if len(family_list) == 0:
            clanname =  self.__db.get_person_from_handle(person_handle).primary_name.get_surname()
        else:
            if self.showallfamilies:
                for fam in family_list:
                    if self.__db.get_family_from_handle(fam).get_father_handle():
                        clanname = clanname + self.__db.get_person_from_handle(self.__db.get_family_from_handle(fam).get_father_handle()).primary_name.get_surname()+" "
            else:
                if self.__db.get_family_from_handle(family_list[0]).get_father_handle():
                    clanname = self.__db.get_person_from_handle(self.__db.get_family_from_handle(family_list[0]).get_father_handle()).primary_name.get_surname()
        return clanname 
 
    def get_date_place(self, event):
        """
        Return the date and place of the given event.
        """
        event_date = ''
        event_place = ''
        event_sort = '%012d' % 0
        if event:
            event_date = get_date(event)
            event_sort = '%012d' % event.get_date_object().get_sort_value()
            handle = event.get_place_handle()
            if handle:
                place = self.__db.get_place_from_handle(handle)
#                event_place = place.get_title()
                event_place = _pd.display_event(self.__db, event, fmt=self.place_fmt)

        return (event_date, event_sort, event_place)      

    def find_place(self, event):
        """
#        Use the most recent occupation residence.
#        """
        placetxt = " "
        placetxt = _pd.display_event(self.__db, event, self.pl_format)
        return(placetxt[4:-2])

    def listpersonref(self):
    
        sc = {'source': 'S_ID',
              'citalist': 'C_ID' }
        stc = {}      
        citation_without_notes = 0
        EMPTY = " "

        def toYear(date):
            yeartext = date.get_year()
            return yeartext

        genderlist = ['w','m','u']
       
        self.doc.start_paragraph("SRC-SourceTitle")
        self.doc.write_text(_("Person with Citations"))
        self.doc.end_paragraph()       

       
        self.doc.start_table("VISONETable", "SRC-VISONETable")
        column_titles = [_("Gramps_ID"), _("Gramps_ID"),  _("LNr"), _("Birthdate"), _("Deathdate"),_("Birthyear"), _("Deathyear"), _("Age on Death"), _("gender"), _("Name"), _("Surname"),_("LabelID"),_("LabelGT"),_("Clan"),_("Birth Place"),_("Death Place"),_("Birth Country"),_("Death Country"),_("Birth Lat"),_("Birth Lon")] 
        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()                 
        i=0 
        ii=0
        
        pe_list =[]
        for pe in self.__db.get_person_handles():
            pe_index = [ self.__db.get_person_from_handle(pe).gramps_id, pe]
            pe_list.append(pe_index)

        with self._user.progress(_("VIS ATTR Report"), 
                                  _("Generating report"), 
                                  len(pe_list)) as step:
    
            for pedet in sorted(pe_list,  key=lambda t: (t[1])):
    #        for pe in self.__db.get_person_handles(sort_handles=True):
                i += 1
                # increment progress bar
                step()
#                print (i, pedet)
                person =  self.__db.get_person_from_handle(pedet[1])
                birth = get_birth_or_fallback(self.__db, person) 
                birth_date, birth_sort, birth_place = self.get_date_place(birth)
                #birth_country = _pd.display_event(self.__db, birth, fmt=self.place_fmt)
                birth_country = _pd.display_event(self.__db, birth, fmt=6)
                #print(birth_country)

                death = get_death_or_fallback(self.__db, person)
                death_date, death_sort, death_place = self.get_date_place(death)
                death_country = _pd.display_event(self.__db, death, fmt=6)

                print(death_country)
                #print('formats        ', _pd.get_formats().levels)
                for l in _pd.get_formats():
                    print(l.name, l.levels)

                age = get_age(self.__db, person)   
                birth_year = ""
                death_year = ""
                    
                if birth:
                    birth_year = birth.get_date_object().get_year()
                if death:    
                    death_year = death.get_date_object().get_year() 
                    
                self.doc.start_row()
                
                # Person ID 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    person.gramps_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                # Person ID   2nd time
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    person.gramps_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
                                       
                # LNR
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    i) 
                self.doc.end_paragraph()
                self.doc.end_cell()
            
                # Birth Date               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                birth = get_birth_or_fallback(self.__db, person)
                self.doc.write_text(_(" %s") %            
                                    birth_date)
                self.doc.end_paragraph()  
                self.doc.end_cell()
     
                # Death Date               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    death_date)
                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                # Birth year               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    birth_year)
                self.doc.end_paragraph()  
                self.doc.end_cell()
     
                # Death year               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    death_year)
                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                
                # Age on death             
                self.doc.start_cell("SRC-TableColumn")  
                self.doc.start_paragraph("SRC-SourceDetails")
                if age:
                    if age[0]>0:
                        self.doc.write_text(_("%s") %
                                                        age[0])
                    else:
                        if age[1]>0:                                    
                            self.doc.write_text(_("%s M.") %
                                                        age[1])
                        else:                                   
                            if age[2]>0:                                    
                                self.doc.write_text(_("%s T.") %
                                                            age[2])                                                        
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
    
                # Person gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                        genderlist[person.gender])
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # Person Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    person.get_primary_name().get_regular_name())
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Person Surname, givenname 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    person.get_primary_name().get_name())
                self.doc.end_paragraph()
                self.doc.end_cell()

                # Label Name (ID) 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                label =""
                label = _(" %s") % person.get_primary_name().get_regular_name()
                label = label + _(" [%s]") % person.gramps_id
                self.doc.write_text(_("%s") %
                                    label)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
    
                # Label Name (geb-to) 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                label =""
                label = _(" %s") % person.get_primary_name().get_regular_name()
                label = label + _(" (%s") % birth_year
                label = label + _("-%s)") % death_year
                if label[-3:] == "(-)":
                    label =label[:-3]
                self.doc.write_text(_("%s") %
                                    label)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
    
                # Clan Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                             self.find_clan(pe)) 
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                #Place of birth
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             birth_place)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Place of death
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             death_place)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                
    
                #Country of birth
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             birth_country)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Country of death
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             death_country)
#                             death_country[4:])
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Latitude of Place of Birth
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if birth:
                    lat_txt, lon_txt = self.find_place_lat_lon(birth)
                self.doc.write_text(_("%s") %
                             lat_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Longitude of Place of Birth
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if birth:
                    lat_txt, lon_txt = self.find_place_lat_lon(birth)
                self.doc.write_text(_("%s") %
                             lon_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()

    
    
                self.doc.end_row()
                        
            self.doc.end_table()
#######################

#------------------------------------------------------------------------
#
# VisoneATTRXLSXReportOptions
#
#------------------------------------------------------------------------
class VisoneATTRXLSXReportOptions(MenuReportOptions):
    """
    SourcesCitationsAndPersonsOptions provides the options 
    for the SourcesCitationsAndPersonsReport.
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
#p-        from Filters import CustomFilters, GenericFilter
        from gramps.gen.filters import CustomFilters, GenericFilter

#        opt = FilterOption(_("Select using filter"), 0)
#        opt.set_help(_("Select places using a filter"))
#        filter_list = []
#        filter_list.append(GenericFilter())
#        filter_list.extend(CustomFilters.get_filters('Source'))
#        opt.set_filters(filter_list)
#        menu.add_option(category_name, "filter", opt)
#        
#        showpersons = BooleanOption(_("Show persons"), True)
#        showpersons.set_help(_("Whether to show events and persons mentioned in the note"))
#        menu.add_option(category_name, "showpersons", showpersons)
#
#        incphotos = BooleanOption(_("Include Photos"), True)
#        incphotos.set_help(_("Whether to show photos mentioned in the citation"))
#        menu.add_option(category_name, "incphotos", incphotos)
                

        category_name = _("Calc Options")
        
        # Reload filters to pick any new ones
        CustomFilters = None
#p-        from Filters import CustomFilters, GenericFilter
        from gramps.gen.filters import CustomFilters, GenericFilter
        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Source'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)
        
        showallfamilies = BooleanOption(_("Show surnames of all famiies in clans"), True)
        showallfamilies.set_help(_("Whether to show the names of all families as surname"))
        menu.add_option(category_name, "showallfamilies", showallfamilies)
        
        #        self.pl_format  = menu.get_option_by_name('placeformat').get_value()

        #places = PlaceListOption(_("Select places individually"))
        #places.set_help(_("List of places to report on"))
        #menu.add_option(category_name, "places", places)

        stdoptions.add_place_format_option(menu, category_name)

#        incphotos = BooleanOption(_("Include Photos"), True)
#        incphotos.set_help(_("Whether to show photos mentioned in the citation"))
#        menu.add_option(category_name, "incphotos", incphotos)

        #placeformat = EnumeratedListOption(_("Place Format"), "Default")
        #placeformat.set_items([
        #        ("default",   _("Default")),
        #        ("first",   _("First")),
        #        ("firstplace",   _("Firstplace")),
        #        ("firstplace-country",   _("Firstplace-Country")),
        #        ("country",   _("Country")),
        #        ("long", _("Long"))])
        #placeformat.set_help(_("If Placename is given long or short"))
        #menu.add_option(category_name, "placeformat", placeformat)

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
        self.__column_title_head_style()
        self.__section_style()
        self.__VISONE_table_style()
        self.__details_style()
        self.__cell_style()
        self.__table_column_style()
        self.__report_footer_style()


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

    def __column_title_head_style(self):
        """
        Define the style used for the event table column title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(3)
        para.set(first_indent=0.0, lmargin=0.0)
        para.set_description(_('The style used for a column title incl headerlevel.'))
        self.default_style.add_paragraph_style("SRC-ColumnTitleHead", para)


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

    def __VISONE_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(14)
        table.set_column_width(0, 5)
        table.set_column_width(1, 5)
        table.set_column_width(2, 8)
        table.set_column_width(3, 12)
        table.set_column_width(4, 5)
        table.set_column_width(5, 6)
        table.set_column_width(6, 6)
        table.set_column_width(7, 20)
        table.set_column_width(8, 20)
        table.set_column_width(7, 20)
        table.set_column_width(8, 5)
        table.set_column_width(9, 5)
        table.set_column_width(10, 5)
        table.set_column_width(11, 5)
        table.set_column_width(12, 5)
        table.set_column_width(12, 5)
        table.set_column_width(14, 5)

        self.default_style.add_table_style("SRC-VISONETable", table)          

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
        
        

      