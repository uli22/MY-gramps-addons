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
from collections import defaultdict
########################################
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
from gramps.gen.relationship import get_relationship_calculator
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
from gramps.gui.utils import ProgressMeter
#import gramps.plugins.lib.libholiday as libholiday

from gramps.gen.datehandler import displayer as _dd
from gramps.gen.datehandler import get_date
from gramps.gen.display.MYplace import displayer as place_displayer
from gramps.gen.display.name import displayer as name_displayer


def _T_(value): # enable deferred translations (see Python docs 22.1.3.4)
    return value
# _T_ is a gramps-defined keyword -- see po/update_po.py and po/genpot.sh

#------------------------------------------------------------------------
#
# PukReport
#
#------------------------------------------------------------------------
class PukReport(Report):
    """
    This report produces .
    """
    genderlist = ['w','m','u']
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
#        self.showpersons = menu.get_option_by_name('showpersons').get_value()
#        self.addimages     = menu.get_option_by_name('incphotos').get_value()

        menucalc = options.menu
#        self.title_string = menu.get_option_by_name('title').get_value()
#        self.subtitle_string = menu.get_option_by_name('subtitle').get_value()
#        self.footer_string = menu.get_option_by_name('footer').get_value()
        self.showallfamilies =menucalc.get_option_by_name('showallfamilies').get_value()
#        self.addimages     = menu.get_option_by_name('incphotos').get_value()
        
        self.pl_format  = menu.get_option_by_name('placeformat').get_value()


        filter_option = menucalc.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
#        self.sort = Sort.Sort(self.database)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of source handles
            sourcefilterlist = self.__db.iter_source_handles()
            self.source_handles = self.filter.apply(self.__db, sourcefilterlist)
        else:
            self.source_handles = self.__db.get_source_handles()



    def write_report(self):
        """
        Overridden function to generate the report.
        """
        self.progress = ProgressMeter(_("PUK Export"), '')
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
        self.progress.close()

    def find_place(self, place_handle):
        placename = " "
        if place_handle:
            place =  self.__db.get_place_from_handle(place_handle)
            if place:
                placename = place.title
        return placename 

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

    def __format_date(self, date_object):
        if not date_object: return
        d=date_object.get_day()    
        m=date_object.get_month()
        y=date_object.get_year()
        if (d == 0) and (m == 0):
            date_f = (" %s" % y)
        elif (d == 0) and not (m == 0):
            date_f = (" %s/%s" % (m, y))  
        else:       
            date_f = (" %s/%s/%s" % (d, m, y)) 
        return date_f           
        
    def find_occupation(self, person):
        """
        Use the most recent occupation event.
        """
        occupationtxt = " "
        event_refs = person.get_primary_event_ref_list()
        events = [event for event in
                    [self.__db.get_event_from_handle(ref.ref) for ref in event_refs]
                    if event.get_type() == EventType(EventType.OCCUPATION)]
        if len(events) > 0:
            events.sort(key=lambda x: x.get_date_object())
#            print(events[0].get_description())
            occupation = events[-1].get_description()
            if occupation:
                occupationtxt=("%s" % occupation)
        return(occupationtxt)

    def listpersonref(self):

        sc = {'source': 'S_ID',
              'citalist': 'C_ID' }
        stc = {}      
        citation_without_notes = 0
        EMPTY = " "

        def toYear(date):
            yeartext = date.get_year()
            return yeartext         

        def toNbr(text):
            text = text[1:]
            while text[0] == "0":
                text = text[1:]
            return text         


        genderlist = ['F','M','X']
     # build citasource dictionary  and cl list 
        
        sc = defaultdict(list)
        cl = []
        i=1
        for ci in self.__db.iter_citations():
            if ci.source_handle in self.source_handles:
                sc[ci.source_handle].append(ci.handle)
                cl.append(ci.handle)

        # build citations - event dic                       xy
        #(a,b): set([('Citation', 'c4a8c46041e08799b17')]) 
        # event: c4a8c4f95b01e38564a event: Taufe
        ci = defaultdict(list)
        for ev in self.__db.iter_events():
            refhandlelist = ev.get_referenced_handles()   
            for (a,b) in refhandlelist:
                if a == 'Citation':
                    if b in cl:                    #!
                        ci[ev.handle].append(b)
        ci_evkeys = ci.keys()                

#***********************************************************************
#       # build godparentsdict of all persons
#

        gpdic ={}
        gpdic = defaultdict(list)
        for pe in self.__db.get_person_handles():
            for eventref in self.__db.get_person_from_handle(pe).event_ref_list:
                if not eventref.get_role().is_primary():
                    if eventref.get_role() == "Pate":
                        gpdic[eventref.ref].append((eventref.get_role(),pe))
        gpdickeys = gpdic.keys()

        for i in gpdic.keys():
            print(self.__db.get_event_from_handle(i).get_date_object())
            for (a,b) in gpdic[i]:
                print("TEIL     ",a
                        ,name_displayer.display(self.__db.get_person_from_handle(b))
                        ,self.__db.get_person_from_handle(b).gramps_id)
        print("GPDIC   ",len(gpdickeys))



#***********************************************************************
#       # build family list of all families with familyevent in citation
#
#       a    family handle
#
        famlist =[]
#        famdic = {}
        for fh in self.__db.get_family_handles():
            for eventref in self.__db.get_family_from_handle(fh).event_ref_list:
                if eventref.ref in ci_evkeys:
                    famlist.append(fh)
        # Each family only once
        famlist = list(set(famlist))
#        for fi,f in enumerate(famlist):
#            famdic[f]=fi

#***********************************************************************
#       # build pedic of all persons in families with familyevent in citation
#
#       k    gramps_id
#       v    1...n

        pedic ={}

        self.doc.start_paragraph("SRC-SourceTitle")
        self.doc.write_text(_("Person with Citations"))
        self.doc.end_paragraph()       

        indexlist = list()


        self.doc.start_table("Corpus Attributes", "SRC-VISONETable")
        name_list =["Zeile 1", "Zeile 2"]
        self.progress.set_pass(_('Start Table Corpus'), len(name_list))
        for nl in name_list:
            self.doc.start_row()
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(nl)
            self.doc.end_paragraph()
            self.doc.end_cell()
            self.doc.end_row()                 
        self.doc.end_table()


        self.progress.set_pass(_('Start Table Families'), len(famlist))

        self.doc.start_table("Families", "SRC-VISONETable")
##        column_titles = [_("Prim_ID"), _("Gramps_ID"),  _("Role"), _("Relation"), _("LNr"), _("Ev ID"),_("Event"), _("Date"), _("Year"), _("Age Primary"), _("Age Person"), _("gender Primary"), _("gender Person") , _("Person"),_("Primary"), _("Person birth"), _("Person Clan"),_("Primary Clan"),_("Event Place"),_("FamID"),_("AnzKind")] 
        column_titles = [_("Id"), "Status", "FatherId", "MotherId", "Children", "HUSB_ORD", "WIFE_ORD", _("Fam_ID"), _("Father_ID"), _("Mother_ID"), _("Children_ID")] 

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
        

        fid = 0
        for f in sorted(famlist):
            famidtext = ""
            fathernametxt = ""
            mothernametxt = ""
            fatheridtxt = ""
            motheridtxt = ""
            childtxt = ""
            fatherordertxt = ""
            motherordertxt = ""
            
            family = self.__db.get_family_from_handle(f)
            famidtxt = (" [%s]" % family.gramps_id)
            famreltxt = family.get_relationship()
            if famreltxt == "Verheiratet":
                famreltxt = "M"
            elif famreltxt == "Unverheiratet":
#                print(famreltxt)
                famreltxt = " "
#                print("FAM    ",famreltxt)
            elif famreltxt == "Unbekannt":
                famreltxt = " "
            if family.get_father_handle():
                fathernametxt = fathernametxt + self.__db.get_person_from_handle(family.get_father_handle()).primary_name.get_name()
                famhandlelist = self.__db.get_person_from_handle(family.get_father_handle()).get_family_handle_list()
                fatherordertxt = ("%s" % len(famhandlelist))
                fatheridtxt = self.__db.get_person_from_handle(family.get_father_handle()).gramps_id
                indexlist.append(fatheridtxt)
                fatheridtxt = toNbr(fatheridtxt)

            if family.get_mother_handle():
                mothernametxt = mothernametxt + self.__db.get_person_from_handle(family.get_mother_handle()).primary_name.get_name()
                famhandlelist = self.__db.get_person_from_handle(family.get_mother_handle()).get_family_handle_list()
                motheridtxt = self.__db.get_person_from_handle(family.get_mother_handle()).gramps_id
                motherordertxt = ("%s" % len(famhandlelist))
                indexlist.append(motheridtxt)
                motheridtxt = toNbr(motheridtxt)
                # BUG only count not order
            childtxt =""
            for ch in family.get_child_ref_list():
                child = self.__db.get_person_from_handle(ch.ref)
                if child:
                    childtxt1 = child.get_gramps_id()
                    childtxt1 = childtxt1 + ";"
                    indexlist.append(child.get_gramps_id())
                    childtxt1 = toNbr(childtxt1)
                    childtxt = childtxt + childtxt1
            fid += 1
            line = []
            line.append(fid)
            line.append(famreltxt)
            line.append(fatheridtxt)
            line.append(motheridtxt)
            line.append(childtxt)
            line.append(fatherordertxt)
            line.append(motherordertxt) 
            line.append(famidtxt)
            line.append(fathernametxt)
            line.append(mothernametxt)


            self.doc.start_row()
            for l in line:
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    l)
                self.doc.end_paragraph()
                self.doc.end_cell()
            self.doc.end_row()
            self.progress.step()

        self.doc.end_table()

        self.doc.start_table("Individuals", "SRC-VISONETable")
        column_titles = [_("Id"), "Name", "Gender", "ORD", "BIRT_DATE", "BIRT_PLACE", "DEAT_DATE", "DEAT_PLACE", "OCCU", "PersonID2"]
#   Id	Name	Gender	ORD	BIRT_DATE	Rolle	PersonID2


        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()                 


        l = len(indexlist)
        indexlist = list(set(indexlist))

        self.progress.set_pass(_('Start Table Individuals'), len(indexlist))

#        for m in indexlist:
#            print(m)
        pi = 1
        for il in indexlist:
            self.doc.start_row()
            person = self.__db.get_person_from_gramps_id(il)
            

# Id
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                toNbr(il))
            self.doc.end_paragraph()
            self.doc.end_cell()

# Name
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                person.primary_name.get_gedcom_name())
            self.doc.end_paragraph()
            self.doc.end_cell()

# Gender
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                    genderlist[person.get_gender()])
            self.doc.end_paragraph()
            self.doc.end_cell()

# Ord
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                " ")
#                                person.primary_name.get_name())
            self.doc.end_paragraph()
            self.doc.end_cell()

# Birth Date
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            birth_ref = person.get_birth_ref()
            birth_date = None
            birthtxt = " "
            birthplacetxt = " "
            if birth_ref:
                birthtxt = self.__format_date(self.__db.get_event_from_handle(birth_ref.ref).get_date_object())
#                birthplacetxt = self.find_place(self.__db.get_event_from_handle(birth_ref.ref).place)
                birthplacetxt = place_displayer.display_event(self.__db, self.__db.get_event_from_handle(birth_ref.ref), self.pl_format)

            self.doc.write_text(_("%s") %
                                birthtxt)
            self.doc.end_paragraph()
            self.doc.end_cell()
            


# Place of Event
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                         birthplacetxt[4:-2])
            self.doc.end_paragraph()
            self.doc.end_cell()

# Death Date
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            death_ref = person.get_death_ref()
            death_date = None
            deathtxt = " "
            deathplacetxt = " "
            if death_ref:
                deathtxt = self.__format_date(self.__db.get_event_from_handle(death_ref.ref).get_date_object())
                deathplacetxt = place_displayer.display_event(self.__db, self.__db.get_event_from_handle(death_ref.ref), self.pl_format)
            self.doc.write_text(_("%s") %
                                deathtxt)
            self.doc.end_paragraph()
            self.doc.end_cell()


# Place of Event
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                         deathplacetxt[4:-2])
            self.doc.end_paragraph()
            self.doc.end_cell()


# Occupation
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                         self.find_occupation(person))
            self.doc.end_paragraph()
            self.doc.end_cell()


# Person_ID
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                il)
            self.doc.end_paragraph()
            self.doc.end_cell()


            self.doc.end_row()
            pi += 1

        print (l,len(indexlist))
        self.progress.step()
        self.doc.end_table()

        self.progress.set_pass(_('Start Table Relation'), len(indexlist))

        self.doc.start_table("Relation", "SRC-VISONETable")
        column_titles = [_("Id"), "Name", "Candidate", "Godparent", "#DATE"]
#_("Id"), "Name", "Candidate", "Godparent", "#DATE"
#
#
        self.doc.start_row()
        self.doc.start_cell("SRC-TableColumn")
        self.doc.start_paragraph("SRC-ColumnTitle")
        self.doc.write_text("Patenschaften")
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
#
        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()


        l = len(indexlist)
        indexlist = list(set(indexlist))
#        for m in indexlist:
#            print(m)
        pi = 1
        for il in indexlist:
            person = self.__db.get_person_from_gramps_id(il)
            for eventref in person.get_event_ref_list():
                event = self.__db.get_event_from_handle(eventref.ref)
##                if event and event.type.is_baptism():
                if event.type.is_baptism():

                    self.doc.start_row()
# EventId
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        toNbr(event.gramps_id))
                    self.doc.end_paragraph()
                    self.doc.end_cell()

# Name
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("Bapt %s") %
                                        event.get_description())
                    self.doc.end_paragraph()
                    self.doc.end_cell()

# Candidate
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        toNbr(il))
                    self.doc.end_paragraph()
                    self.doc.end_cell()

# Godparents


                    patentxt =""
                    for i in gpdickeys:
                        if self.__db.get_event_from_handle(i).gramps_id == event.gramps_id:
                            for (a,b) in gpdic[i]:
                                patentxt = patentxt + toNbr(self.__db.get_person_from_handle(b).gramps_id) +";"

                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        patentxt)
                    self.doc.end_paragraph()
                    self.doc.end_cell()


# Date
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_(" %s") %
                                 self.__format_date(event.get_date_object()))
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                    self.doc.end_row()
                    pi += 1
            self.progress.step()
        print (l,len(indexlist))
        self.doc.end_table()



#------------------------------------------------------------------------
#
# PukReportOptions
#
#------------------------------------------------------------------------
class PukReportOptions(MenuReportOptions):
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
        from gramps.gen.filters import CustomFilters, GenericFilter
        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Source'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)
        
#        opt = FilterOption(_("Select Person filter"), 0)
#        opt.set_help(_("Select places using a person filter"))
#        filter_list = []
#        filter_list.append(GenericFilter())
#        filter_list.extend(CustomFilters.get_filters('Person'))

#        opt.set_filters(filter_list)
#        menu.add_option(category_name, "filter", opt)


        showallfamilies = BooleanOption(_("Show surnames of all famiies in clans"), True)
        showallfamilies.set_help(_("Whether to show the names of all families as surname"))
        menu.add_option(category_name, "showallfamilies", showallfamilies)

        placeformat = EnumeratedListOption(_("Place Format"), "Default")
        placeformat.set_items([
                ("default",   _("Default")),
                ("first",   _("First")),
                ("firstplace",   _("Firstplace")),
                ("firstplace-country",   _("Firstplace-Country")),
                ("country",   _("Country")),
                ("long", _("Long"))])
        placeformat.set_help(_("If Placename is given long or short"))
        menu.add_option(category_name, "placeformat", placeformat)


#        incphotos = BooleanOption(_("Include Photos"), True)
#        incphotos.set_help(_("Whether to show photos mentioned in the citation"))
#        menu.add_option(category_name, "incphotos", incphotos)
    
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
        
        

      