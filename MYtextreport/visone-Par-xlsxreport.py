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
from gramps.gen.utils.place import conv_lat_lon
#from gramps.gen.utils.db import get_marriage_or_fallback


import gramps.plugins.lib.libholiday as libholiday

# localization for BirthdayOptions only!!
from gramps.gen.datehandler import displayer as _dd
from gramps.gen.datehandler import get_date
from gramps.gen.display.MYplace import displayer as place_displayer

def _T_(value): # enable deferred translations (see Python docs 22.1.3.4)
    return value
# _T_ is a gramps-defined keyword -- see po/update_po.py and po/genpot.sh

_TITLE0 = _T_("Birthday and Anniversary Report")
_TITLE1 = _T_("My Birthday Report")
_TITLE2 = _T_("Produced with Gramps")


#------------------------------------------------------------------------
#
# Visone-Par-XLSReport
#
#------------------------------------------------------------------------
class VisoneParXLSXReport(Report):
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
        self.addfmglines =menucalc.get_option_by_name('addfmglines').get_value()

#        self.addimages     = menu.get_option_by_name('incphotos').get_value()
        
        filter_option = menucalc.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
#        self.sort = Sort.Sort(self.database)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of source handles
            sourcefilterlist = self.__db.iter_source_handles()
            self.source_handles = self.filter.apply(self.__db, sourcefilterlist)
        else:
            self.source_handles = self.__db.get_source_handles()

        self.pl_format  = menu.get_option_by_name('placeformat').get_value()

    def is_spouse(self, db, orig, other, all_rel=False):
        """
        Determine the spouse relation
        """
        spouse_type = self._get_spouse_type(db, orig, other, all_rel)
        if spouse_type:
            return self.get_partner_relationship_string(spouse_type, 
                        orig.get_gender(), other.get_gender())
        else:
            return None

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

#    def find_place-old(self, place_handle):
#        placename = " "
#        if place_handle:
#            place =  self.__db.get_place_from_handle(place_handle)
#            if place:
#                placename = place.title
#        return placename 


    def find_place(self, event):
        """
#        Use the most recent occupation residence.
#        """
        placetxt = " "
        placetxt = place_displayer.display_event(self.__db, event, self.pl_format)
#        return(placetxt[4:-2])
        return(placetxt)

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

    def find_last_wohnort_from_handle(self, eventhandle, personhandle):
        # ev.. eventhandle, e person handle
        # returns last person or family residence before event
        lpi=0
        mm=0
        lptxt=" "
        lp=[]
        lpdate=[]
        lptype=[]
        for event_ref in self.__db.get_person_from_handle(personhandle).get_event_ref_list():
            if int(event_ref.get_role()) == EventRoleType.PRIMARY:
                event = self.__db.get_event_from_handle(event_ref.ref)
                print("NOW ", event_ref.get_role(), event.get_type())
                if int(event.get_type()) == EventType.RESIDENCE:
                    dat_dif =  self.__db.get_event_from_handle(eventhandle).get_date_object().get_year() - event.get_date_object().get_year()
                    if dat_dif < 0:
                        lpi += 1
                        lpdate.append(dat_dif)
                        lp.append(self.find_place(event))
                        lptype.append(event_ref.get_role())

        for fam_ref in self.__db.get_person_from_handle(personhandle).get_family_handle_list():
            for event_ref in self.__db.get_family_from_handle(fam_ref).get_event_ref_list():
                event = self.__db.get_event_from_handle(event_ref.ref)
                print("NOW ", event_ref.get_role(), event.get_type())
                if int(event.get_type()) == EventType.RESIDENCE:
                    dat_dif =  self.__db.get_event_from_handle(eventhandle).get_date_object().get_year() - event.get_date_object().get_year()
                    if dat_dif < 0:
                        lpi += 1
                        lpdate.append(dat_dif)
                        lp.append(self.find_place(event))
                        lptype.append(event_ref.get_role())
        if len(lpdate)>0:
            mm = max(lpdate)
            lptxt0=lp[lpdate.index(mm)]
        else:
            mm= "MM"
            lptxt0="kein Wohnort"
#        print(self.__db.get_person_from_handle(personhandle).gramps_id)
#        print(mm, lptxt0)
#        print(*lp)
#        print(*lpdate)
#        print(*lptype)
#        RTtxt=' '
#        RTtxt=('-'.join(str(p) for p in lp))
#        RTtxt1=('-'.join(str(p) for p in lpdate))
#        RTtxt2=('-'.join(str(p) for p in lptype))
#        RTtxt=RTtxt+RTtxt2
#        print('-'.join(str(p) for p in lp))
#        print('-'.join(str(p) for p in lpdate))
#        print('-'.join(str(p) for p in lptype))
#        return(RTtxt)
        return (lptxt0)


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
 
       


    def personrelationstring(self, Fam, rolepershandle, primpershandle, primpersAhandle, primpersBhandle):
        if rolepershandle:
            
            # Relationstring
            # For Single Person Events
            
            
            posnotelist = ['F','H','X']
            relation_set = ("nicht verwandt","nv")
# Uli eingefügt wg. Z 389+2
            if Fam == 0:
            
                relation_text = "nicht verwandt"
                relation_set = ("nicht verwandt","nv")
                rel_calc = get_relationship_calculator()
                relation = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpershandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relation:                                      
                    relation_text = relation
                    relation_set = (relation_text,"VE")
#                    print("HIER  ", relation_text)
                    if relation_text[0]=="E":
                        kp = posnotelist[self.__db.get_person_from_handle(primpershandle).gender]+"."
                        kp = kp + posnotelist[self.__db.get_person_from_handle(rolepershandle).gender]
                        relation_set = ("Ehepartner",kp)
                elif self.__db.get_person_from_handle(primpershandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_set = (_("IP "),"")
                elif relation_text == "nicht verwandt":
#    spouse
                    family_list = self.__db.get_person_from_handle(primpershandle).get_family_handle_list()
                    for family_handle in family_list:
                        family = self.__db.get_family_from_handle(family_handle)
                        print("FAMILY   ", family)
                        if family:
                            husband = family.get_father_handle()
                            wife = family.get_mother_handle()
                            if husband and husband != primpershandle:
                                rel_calc = get_relationship_calculator()
                                relation = rel_calc.get_one_relationship(
                                                                        self.__db, 
                                                                        self.__db.get_person_from_handle(husband),
                                                                        self.__db.get_person_from_handle(rolepershandle))
                                if relation:
#                                    relation_text = relation[1]+" || " "F." + relation[1]
                                    rt = "F." + relation[1]
###UUU                                    relation_text = (relation[0],rt)
                                    relation_text = (relation,rt)

#                                    relation_text = _("%s der Mutter" % relation_text)
                            if wife and wife != primpershandle:
                                rel_calc = get_relationship_calculator()
                                relation = rel_calc.get_one_relationship(
                                                                        self.__db, 
                                                                        self.__db.get_person_from_handle(wife),
                                                                        self.__db.get_person_from_handle(rolepershandle))
                                if relation:
                                    rt = "H."+ relation[1]
###UUU                                    relation_text = (relation[0], rt)
                                    relation_text = (relation, rt)
##                            print(relation_text)
            # Relation
            # For Family Events
            
            if Fam == 1:
                
                relation_text = ("nicht verwandt", "")
                relation_textA = ("","")
                relation_textB = ("","")
                
#p-                rel_calc = Relationship.get_relationship_calculator()
                rel_calc = get_relationship_calculator()
                
                relationA = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpersAhandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relationA:
#######                    (BRIDE))
                    t1="BRIDE"+relationA[0]
                    relation_textA = (t1, relationA[1])
                elif self.__db.get_person_from_handle(primpersAhandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_text = (_("IP "),"")

                rel_calc = get_relationship_calculator()
                
                relationB = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpersBhandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relationB:
#######                    relation_textB = _("To groom: %s" % relationB)
                    t1="GROOM"+relationB[0]
                    relation_textB = (t1, relationB[1])

####                    relation_textB = relationB
                elif self.__db.get_person_from_handle(primpersBhandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_text = (_("IP "),"")
                if (relation_textA + relation_textB) !="":
                    rt0 = relation_textA[0] + " " + relation_textB[0]
                    rt1 = relation_textA[1] + " " + relation_textB[1]

                    relation_text = (rt0, rt1)

#            relation_text = relation_text + str(primpersAhandle)+ " "   + str(primpersBhandle)  + " "   + str(rolepershandle)
#            return ((_("%s") % relation_text[0]), (_("%s") % relation_text[1]))
            return (relation_set)
            
    def Vaterzeile(self, ii, ev, b, name, surname, name_id, name_handle):
        #Wenn es einen Vater gibt, dafuer eine Zeile ausgeben
        genderlist = ['w','m','u']
        posnotelist = ['F','H','X']
        fam_handle = self.__db.get_person_from_handle(name_handle).get_main_parents_family_handle()
        FID=" "
        FID_P=" "
        if fam_handle:
            father_handle = self.__db.get_family_from_handle(fam_handle).father_handle
            mother_handle = self.__db.get_family_from_handle(fam_handle).mother_handle
            FID=self.__db.get_family_from_handle(fam_handle).gramps_id
            FID_P=self.__db.get_family_from_handle(fam_handle).gramps_id
            AnzKind= len(self.__db.get_family_from_handle(fam_handle).child_ref_list)
        
            if father_handle is not None:
                
                ii+=1
                self.doc.start_row()
                
                # Primary Role ID 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    name_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
       #         indexdic[name_handle] = None
    
    
                               
                # Person (father) ID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(father_handle).gramps_id) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
     #           indexdic[e] = None
    
                               
                # Event Role
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    "Vater")
                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                # Relation
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
    
                self.doc.write_text(_("%s") %  "Vater")
                self.doc.end_paragraph()  
                self.doc.end_cell()

                # kinshippath
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                kp = posnotelist[self.__db.get_person_from_gramps_id(name_id).gender]+"(H)"
                self.doc.start_paragraph("SRC-SourceDetails")

    
                self.doc.write_text(_("%s") %  kp)
                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                # LNR
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    ii) 
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Gramps ID 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(ev).gramps_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                #Event Type
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(b).get_type())
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Date               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    get_date(self.__db.get_event_from_handle(b)))
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # Event year               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    self.__db.get_event_from_handle(b).get_date_object().get_year())
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # Age primary Person             
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    birth_ref = None
                    birth_ref = self.__db.get_person_from_handle(name_handle).get_birth_ref()
                    birth_date = None
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            if self.__db.get_event_from_handle(b).get_date_object():
                                age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                                self.doc.write_text(_(" %s") %
                                                    age)
                else:  
                    self.doc.write_text(_(" %s") %
                                        "FAM")
                          
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # Age second Person               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(father_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                        if self.__db.get_event_from_handle(b).get_date_object():
                            age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                            self.doc.write_text(_(" %s") %
                                                age)
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # Primary gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    self.doc.write_text(_("%s") %
                                        genderlist[self.__db.get_person_from_handle(name_handle).gender])
#                                        "m")

                else:
                    self.doc.write_text(_("%s") %
                                        "FAM")
    
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                
                # Person gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    genderlist[self.__db.get_person_from_handle(father_handle).gender])
#                                    "m")

                self.doc.end_paragraph()
                self.doc.end_cell() 

                # Primary Role Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    name)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Person Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(father_handle).primary_name.get_name()) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 

                # Person Last Residence
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                       self.find_last_wohnort_from_handle(ev, father_handle))
                       # ev.. eventhandle, e person handle
                self.doc.end_paragraph()
                self.doc.end_cell() 


                #######################################
                # Birth of second Person               
                self.doc.start_cell("SRC-Cell")
    
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(father_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                        self.doc.write_text(_(" %s") %
                                            get_date(self.__db.get_event_from_handle(birth_ref.ref)))
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                #######################################

    
                # Primary Clan Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    surname)                                         
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Person Clan Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                     self.__db.get_person_from_handle(father_handle).primary_name.get_surname())
    #                self.doc.write_text(_("%s") %
    #                                     self.find_clan(e)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                #Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             self.find_place(self.__db.get_event_from_handle(b)))
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                # FamID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # FamID_P
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID_P) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # AnzKind
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    AnzKind) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                #Latitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if b:
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                self.doc.write_text(_("%s") %
                             lat_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Longitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if b:
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                self.doc.write_text(_("%s") %
                             lon_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                    
    
    #                    # Citation
    #                   self.doc.start_cell("SRC-Cell")
    #                  self.doc.start_paragraph("SRC-SourceDetails")
    #                 self.doc.write_text(_("%s") %
    #                                    ci[ev])
    #               self.doc.end_paragraph()
    #              self.doc.end_cell()
                
                self.doc.end_row()


    def Mutterzeile(self, ii, ev, b, name, surname, name_id, name_handle):
        #Wenn es eine Mutter gibt, dafuer eine Zeile ausgeben
        genderlist = ['w','m','u']
        posnotelist = ['F','H','X']
        fam_handle = self.__db.get_person_from_handle(name_handle).get_main_parents_family_handle()
        FID=" "
        FID_P=" "

        AnzKind=0
        if fam_handle:
            father_handle = self.__db.get_family_from_handle(fam_handle).father_handle
            mother_handle = self.__db.get_family_from_handle(fam_handle).mother_handle
            FID=self.__db.get_family_from_handle(fam_handle).gramps_id
            FID_P=self.__db.get_family_from_handle(fam_handle).gramps_id

            AnzKind= len(self.__db.get_family_from_handle(fam_handle).child_ref_list)

            if mother_handle is not None:
                
                ii+=1
                self.doc.start_row()
                
                # Primary Role ID 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    name_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
       #         indexdic[name_handle] = None
    
    
                               
                # Person (mother) ID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(mother_handle).gramps_id) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
     #           indexdic[e] = None
    
                               
                # Event Role
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    "Mutter")
                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                # Relation
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
    
                self.doc.write_text(_("%s") %  "Mutter")
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # kinshippath
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                kp = posnotelist[self.__db.get_person_from_gramps_id(name_id).gender]+"(F)"
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %  kp)
#                self.doc.write_text(_("%s") %  "LEER-Mutter")
                self.doc.end_paragraph()  
                self.doc.end_cell()

                # LNR
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    ii) 
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Gramps ID 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(ev).gramps_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                #Event Type
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(b).get_type())
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Date               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    get_date(self.__db.get_event_from_handle(b)))
                self.doc.end_paragraph()  
                self.doc.end_cell()

                # Event year               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_(" %s") %
                                    self.__db.get_event_from_handle(b).get_date_object().get_year())
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # Age primary Person             
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    birth_ref = None
                    birth_ref = self.__db.get_person_from_handle(name_handle).get_birth_ref()
                    birth_date = None
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            if self.__db.get_event_from_handle(b).get_date_object():
                                age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                                self.doc.write_text(_(" %s") %
                                                    age)
                else:  
                    self.doc.write_text(_(" %s") %
                                        "FAM")
                          
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # Age second Person               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(mother_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                        if self.__db.get_event_from_handle(b).get_date_object():
                            age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                            self.doc.write_text(_(" %s") %
                                                age)
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # Primary gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    self.doc.write_text(_("%s") %
                                        genderlist[self.__db.get_person_from_handle(name_handle).gender])
#                    self.doc.write_text(_("%i") %
#                                        self.__db.get_person_from_handle(name_handle).gender)

                else:
                    self.doc.write_text(_("%s") %
                                        "FAM")
    
                self.doc.end_paragraph()
                self.doc.end_cell() 
    

                # Person gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    genderlist[self.__db.get_person_from_handle(mother_handle).gender])
#                                    "w")
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # Primary Role Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    name)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Person Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(mother_handle).primary_name.get_name()) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # Person Last Adress
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                       self.find_last_wohnort_from_handle(ev, mother_handle))
                       # ev.. eventhandle, e person handle
                self.doc.end_paragraph()
                self.doc.end_cell() 


                #######################################
                # Birth of second Person               
                self.doc.start_cell("SRC-Cell")
    
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(mother_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                        self.doc.write_text(_(" %s") %
                                            get_date(self.__db.get_event_from_handle(birth_ref.ref)))
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                #######################################
    
                # Primary Clan Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    surname)                                         
                self.doc.end_paragraph()
                self.doc.end_cell()

                # Person Clan Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                     self.__db.get_person_from_handle(mother_handle).primary_name.get_surname())
    #                self.doc.write_text(_("%s") %
    #                                     self.find_clan(e)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
    
                #Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             self.find_place(self.__db.get_event_from_handle(b)))
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # FamID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                                           
                # FamID_P
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID_P) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                                           
                # AnzKind
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    AnzKind) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
    #                    # Citation
    #                   self.doc.start_cell("SRC-Cell")
    #                  self.doc.start_paragraph("SRC-SourceDetails")
    #                 self.doc.write_text(_("%s") %
    #                                    ci[ev])
    #               self.doc.end_paragraph()
    #              self.doc.end_cell()

                #Latitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if b:
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                self.doc.write_text(_("%s") %
                             lat_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Longitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             lon_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                    
                
                self.doc.end_row()

    def Couplezeile(self, ii, ev, b, name, surname, name_id, name_handle):
        #Wenn es einen Partner gibt, dafuer eine Zeile ausgeben
        genderlist = ['w','m','u']
        posnotelist = ['F','H','X']
#UUUUUUU
        fam_handle = self.__db.get_person_from_handle(name_handle).get_main_parents_family_handle()
        FID=" "
        FID_P=" """
        AnzKind=0

        if fam_handle:
            father_handle = self.__db.get_family_from_handle(fam_handle).father_handle
            mother_handle = self.__db.get_family_from_handle(fam_handle).mother_handle
            family =self.__db.get_family_from_handle(fam_handle)
            FID=self.__db.get_family_from_handle(fam_handle).gramps_id
            FID_P=self.__db.get_family_from_handle(fam_handle).gramps_id

#M            marriage = get_marriage_or_fallback(self.__db, family)
            AnzKind= len(self.__db.get_family_from_handle(fam_handle).child_ref_list)


            if (father_handle is not None) and (mother_handle is not None):
                
                ii+=1
                self.doc.start_row()
                
                # Primary Role ID (father))
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(father_handle).gramps_id) 
#                                    name_id)
                self.doc.end_paragraph()
                self.doc.end_cell()
       #         indexdic[name_handle] = None
    
    
                               
                # Person (mother) ID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(mother_handle).gramps_id) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
     #           indexdic[e] = None
    
                               
                # Event Role
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if self.__db.get_person_from_handle(father_handle).gender==0:
                    self.doc.write_text(_("%s") %
                                    "bride")
                elif self.__db.get_person_from_handle(father_handle).gender==1:
                    self.doc.write_text(_("%s") %
                                    "groom")

                self.doc.end_paragraph()  
                self.doc.end_cell()
    
                # Relation
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
    
                self.doc.write_text(_("%s") %  "Partner")
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # kinshippath
    #                   relation_text = "nicht verwandt"
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if self.__db.get_person_from_handle(father_handle).gender==0:
                    self.doc.write_text(_("%s") %
                                    "M.H")
                elif self.__db.get_person_from_handle(father_handle).gender==1:
                    self.doc.write_text(_("%s") %
                                    "H.M")
                self.doc.end_paragraph()  
                self.doc.end_cell()

                # LNR
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    ii) 
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Gramps ID (marriage)
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                
#                if marriage:
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(ev).gramps_id)
#                else:
#                    self.doc.write_text(_("%s") %
#                                "")
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                #Event Type
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(ev).get_type())
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Event Date               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    get_date(self.__db.get_event_from_handle(ev)))
                self.doc.end_paragraph()  
                self.doc.end_cell()

                # Event year               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_event_from_handle(ev).get_date_object().get_year())
                self.doc.end_paragraph()  
                self.doc.end_cell()
                
                # Age primary Person             
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    birth_ref = None
                    birth_ref = self.__db.get_person_from_handle(father_handle).get_birth_ref()
                    birth_date = None
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            if self.__db.get_event_from_handle(ev):
                                age = self.__db.get_event_from_handle(ev).get_date_object().get_year() - birth_date.get_year()
                                self.doc.write_text(_(" %s") %
                                                age)
#                            self.doc.write_text(_(" %s") %
#                                                birth_date)

                else:  
                    self.doc.write_text(_(" %s") %
                                        "FAM")
                          
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # Age second Person               
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(mother_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                       if self.__db.get_event_from_handle(ev):
                           age = self.__db.get_event_from_handle(ev).get_date_object().get_year() - birth_date.get_year()
                           self.doc.write_text(_(" %s") %
                                                age)

#                        if marriage:
#                            age = marriage.get_date_object().get_year() - birth_date.get_year()
#                            self.doc.write_text(_(" %s") %
#                                            age)
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                # Primary gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                if name_handle:
                    self.doc.write_text(_("%s") %
                                        genderlist[self.__db.get_person_from_handle(father_handle).gender])
#                    self.doc.write_text(_("%i") %
#                                        self.__db.get_person_from_handle(name_handle).gender)

                else:
                    self.doc.write_text(_("%s") %
                                        "FAM")
    
                self.doc.end_paragraph()
                self.doc.end_cell() 
    

                # Person gender
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    genderlist[self.__db.get_person_from_handle(mother_handle).gender])
#                                    "w")
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                # Primary Role Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(father_handle).primary_name.get_name()) 
#                                    name)
                self.doc.end_paragraph()
                self.doc.end_cell()
    
                # Person Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    self.__db.get_person_from_handle(mother_handle).primary_name.get_name()) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 

                # Person Last Residence
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                       self.find_last_wohnort_from_handle(ev, mother_handle))
                       # ev.. eventhandle, e person handle
                self.doc.end_paragraph()
                self.doc.end_cell() 


                #######################################
                # Birth of second Person               
                self.doc.start_cell("SRC-Cell")
    
                self.doc.start_paragraph("SRC-SourceDetails")
                birth_ref = None
                birth_ref = self.__db.get_person_from_handle(mother_handle).get_birth_ref()
                birth_date = None
                if birth_ref:
                    birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                    if birth_date:
                        self.doc.write_text(_(" %s") %
                                            get_date(self.__db.get_event_from_handle(birth_ref.ref)))
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
                #######################################
    
                # Primary Clan Name 
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                     self.__db.get_person_from_handle(father_handle).primary_name.get_surname())
#                                    surname)                                         
                self.doc.end_paragraph()
                self.doc.end_cell()

                # Person Clan Name
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                     self.__db.get_person_from_handle(mother_handle).primary_name.get_surname())
    #               self.doc.write_text(_("%s") %
    #                                     self.find_clan(e)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
    
    
#                #Place of Event
##              marriage is difficult: replaced by event
#
#                self.doc.start_cell("SRC-Cell")
#                self.doc.start_paragraph("SRC-SourceDetails")
#    #            self.doc.write_text(_("%s") %
#    #                               self.find_place(get_marriage_or_fallback(self.__db, family)))
#
#########                             self.find_place(self.__db.get_event_from_handle(b)))
#                if marriage:
#                    self.doc.write_text(_("%s") %
#                                    self.find_place(marriage))
#                else:
#                    self.doc.write_text(_("%s") %
#                                    "")
#
#                self.doc.end_paragraph()
#                self.doc.end_cell()
    

                #Place of Event
##               by event

                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             self.find_place(self.__db.get_event_from_handle(ev)))
                self.doc.end_paragraph()
                self.doc.end_cell()
    

                # FamID
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                     
                # FamID_P
                family_handle = self.__db.get_person_from_handle(mother_handle).get_main_parents_family_handle()
                if family_handle:
                    FID_P = self.__db.get_family_from_handle(family_handle).gramps_id
                else:
                    FID_P = "NV"
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    FID_P) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                                                        
                # AnzKind
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                                    AnzKind) 
    #                                    (d)) 
                self.doc.end_paragraph()
                self.doc.end_cell() 
                
                #Latitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                lat_txt =""
                lon_txt =""
                if b:
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                self.doc.write_text(_("%s") %
                             lat_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                #Longitude of Place of Event
                self.doc.start_cell("SRC-Cell")
                self.doc.start_paragraph("SRC-SourceDetails")
                self.doc.write_text(_("%s") %
                             lon_txt)
                self.doc.end_paragraph()
                self.doc.end_cell()
                    
    
    #                    # Citation
    #                   self.doc.start_cell("SRC-Cell")
    #                  self.doc.start_paragraph("SRC-SourceDetails")
    #                 self.doc.write_text(_("%s") %
    #                                    ci[ev])
    #               self.doc.end_paragraph()
    #              self.doc.end_cell()
                
                self.doc.end_row()


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

        # build eventfamily dictionary
        # event: c4a8c4f95b01e38564a event: Taufe
        refhandlelist =[]
        fedic ={}
        fedic = defaultdict(set)

        for fh in self.__db.get_family_handles():
            for eventref in self.__db.get_family_from_handle(fh).event_ref_list:
                if eventref.ref in ci_evkeys:
                    family = self.__db.get_family_from_handle(eventref.ref)
                    fedic[eventref.ref].add((self.__db.get_family_from_handle(fh).mother_handle,self.__db.get_family_from_handle(fh).father_handle,fh ))

        fedickeys =fedic.keys()

#***********************************************************************
#        # build eventperson dictionary
#        # event: c4a8c4f95b01e38564a event: Taufe
#
#       a    date sort value
#       b    event handle
#       c    role
#       d    name
#       e    pe
#
        evdic ={}
        evdic = defaultdict(list)

        for pe in self.__db.get_person_handles(sort_handles=True):
            for eventref in self.__db.get_person_from_handle(pe).event_ref_list:
                if eventref.ref in ci_evkeys:
                    evdic[eventref.ref].append((self.__db.get_event_from_handle(eventref.ref).get_date_object().get_sort_value(),eventref.ref,eventref.get_role(),self.__db.get_person_from_handle(pe).primary_name.get_name(),pe))
#                    print (self.__db.get_event_from_handle(eventref.ref).get_type())



        self.doc.start_paragraph("SRC-SourceTitle")
        self.doc.write_text(_("Person with Citations"))
        self.doc.end_paragraph()       

        indexdic = {}
        indexdic = defaultdict()

        evkeys = sorted(evdic.keys())
#4.1        evkeys.sort
        
        self.doc.start_table("VISONETable", "SRC-VISONETable")
        column_titles = [_("Prim_ID"), _("Gramps_ID"),  _("Role"), _("Relation"), _("Kinship Path prim ->pers"), _("LNr"), _("Ev ID"),_("Event"), _("Date"), _("Year"), _("Age Primary"), _("Age Person"), _("gender Primary"), _("gender Person"),_("Primary") , _("Person"), _("Person residence"), _("Person birth"), _("Person Clan"),_("Primary Clan"),_("Event Place"),_("FamID"),_("FamID_P"),_("AnzKind"),_("Latitude"),_("Longitude")] 
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
        

        for ev in evkeys:
            primarypersonAhandle = ev
            primarypersonBhandle = ev      

            name = "LEER"
            name_id = "LEER"
            FamilyText = "LEERFAM"
            name_handle = 0

            #Primary suchen
            for (a,b,c,d,e) in evdic[ev]:
                if c == EventRoleType.PRIMARY:
                     Fam = 0
                     name = d
                     FID = " "
                     FID_P=" "

                     AnzKind = 0
                     surname = self.__db.get_person_from_handle(e).primary_name.get_surname()
                     name_id = self.__db.get_person_from_handle(e).gramps_id
                     
                     fam_handle = self.__db.get_person_from_handle(e).get_main_parents_family_handle()
                     if fam_handle:
                         FID=self.__db.get_family_from_handle(fam_handle).gramps_id
                         AnzKind= len(self.__db.get_family_from_handle(fam_handle).child_ref_list)

                     name_handle = e
                     FamilyText = "FAMILY"
                     if self.addfmglines:
                         self.Vaterzeile(ii, ev, b, name, surname, name_id, name_handle)
                         ii+=1
                         self.Mutterzeile(ii, ev, b, name, surname, name_id, name_handle)
                         ii+=1
                         self.Couplezeile(ii, ev, b, name, surname, name_id, name_handle)
                         ii+=1

                elif c != EventRoleType.PRIMARY:
                    # if it is a familyevent
                    for k in fedickeys:                         
                        if ev == k:
                            for (a,b,c) in fedic[k]:
                                Fam = 1
                                self.FamilyText = (_("%s") %
                                                self.__db.get_event_from_handle(ev).get_type())
                                self.FamilyText = self.FamilyText +(_(" Eheleute: "))
                                try:
                                    self.FamilyText = self.FamilyText + (_(" %s ") % self.__db.get_person_from_handle(b).primary_name.get_name())
                                    self.FamilyText = self.FamilyText + (_(" %s") % self.__db.get_person_from_handle(b).gramps_id)
                                    # Bei Fam ereignis Vater als prim Person
                                    name_id = self.__db.get_person_from_handle(b).gramps_id
                                    name_handle = b
                                    self.surnameText = (_(" %s ") %  self.__db.get_person_from_handle(b).primary_name.get_surname())
                                    primarypersonBhandle = b             
                                except:
                                    self.FamilyText = self.FamilyText + (_("unknown"))                                           
                                try:
                                    self.FamilyText = self.FamilyText + (_(" and %s ") %  self.__db.get_person_from_handle(a).primary_name.get_name())
                                    self.surnameText = self.surnameText + (_(" and %s ") %  self.__db.get_person_from_handle(a).primary_name.get_surname())
                                    primarypersonAhandle = a  
                                except:
                                    self.FamilyText = self.FamilyText + (_("and unknown"))                                           
                                name = self.FamilyText
                                surname = self.surnameText             
                else:
                    continue     
                   
            for (a,b,c,d,e) in evdic[ev]:
                if c == EventRoleType.PRIMARY:
                    continue
                elif c != EventRoleType.PRIMARY:     
                    
                    ii+=1
                    self.doc.start_row()
                    
                    # Primary Role ID 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        name_id)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                    indexdic[name_handle] = None


                                   
                    # Person ID
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        self.__db.get_person_from_handle(e).gramps_id) 
    #                                    (d)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
                    indexdic[e] = None

                                   
                    # Event Role
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        c)
                    self.doc.end_paragraph()  
                    self.doc.end_cell()
    
                    # Relation
 #                   relation_text = "nicht verwandt"
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")

                    (rta,rtb) = self.personrelationstring(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle)
###                    print((rta,rtb),rta)
                    self.doc.write_text(_("%s") %
#                        self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle))
                        rta)
                    self.doc.end_paragraph()  
                    self.doc.end_cell()

                                        # Kinship Path
 #                   relation_text = "nicht verwandt"
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")

                    self.doc.write_text(_("%s") %
#                        self.personrelationstring(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle))
                        rtb)
                    self.doc.end_paragraph()  
                    self.doc.end_cell()


                    # LNR
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        ii) 
                    self.doc.end_paragraph()
                    self.doc.end_cell()
        
                    # Event Gramps ID 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        self.__db.get_event_from_handle(ev).gramps_id)
                    self.doc.end_paragraph()
                    self.doc.end_cell()

                    #Event Type
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        self.__db.get_event_from_handle(b).get_type())
                    self.doc.end_paragraph()
                    self.doc.end_cell()
    
                    # Event Date               
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_(" %s") %
                                        get_date(self.__db.get_event_from_handle(b)))
                    self.doc.end_paragraph()  
                    self.doc.end_cell()

                    # Event year               
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_(" %s") %
                                        self.__db.get_event_from_handle(b).get_date_object().get_year())
                    self.doc.end_paragraph()  
                    self.doc.end_cell()

                    # Age primary Person             
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    if name_handle:
                        birth_ref = None
                        birth_ref = self.__db.get_person_from_handle(name_handle).get_birth_ref()
                        birth_date = None
                        if birth_ref:
                            birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                            if birth_date:
                                if self.__db.get_event_from_handle(b).get_date_object():
                                    age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                                    self.doc.write_text(_(" %s") %
                                                        age)

#                                self.doc.write_text(_(" %s") %
#                                                birth_date)
#                                self.doc.write_text(_(" %s") %
#                                                self.__db.get_event_from_handle(b).get_date_object())
                    else:  
                        self.doc.write_text(_(" %s") %
                                            "FAM")
                              
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
                    
                    # Age second Person               
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    birth_ref = None
                    birth_ref = self.__db.get_person_from_handle(e).get_birth_ref()
                    birth_date = None
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            if self.__db.get_event_from_handle(b).get_date_object():
                                age =  self.__db.get_event_from_handle(b).get_date_object().get_year() - birth_date.get_year()
                                self.doc.write_text(_(" %s") %
                                                    age)
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
                    
                    # Primary gender
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    if name_handle:
                        self.doc.write_text(_("%s") %
                                            genderlist[self.__db.get_person_from_handle(name_handle).gender])
                    else:
                        self.doc.write_text(_("%s") %
                                            "FAM")
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    # Person gender
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        genderlist[self.__db.get_person_from_handle(e).gender])
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    # Primary Role Name 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        name)
                    self.doc.end_paragraph()
                    self.doc.end_cell()

                    # Person Name
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
    #                                    self.__db.get_person_from_handle(d).primary_name.get_name()) 
                                        (d)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    # Person Last Residence
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                           self.find_last_wohnort_from_handle(ev, e))
                           # ev.. eventhandle, e person handle
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    # Birth of second Person               
                    self.doc.start_cell("SRC-Cell")

                    self.doc.start_paragraph("SRC-SourceDetails")
                    birth_ref = None
                    birth_ref = self.__db.get_person_from_handle(e).get_birth_ref()
                    birth_date = None
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            self.doc.write_text(_(" %s") %
                                                get_date(self.__db.get_event_from_handle(birth_ref.ref)))
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    #######################################

                    # Primary Clan Name 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                         self.find_clan(e)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell()

                    # Person Clan Name
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
#                    self.doc.write_text(_("%s") %
#                                         self.__db.get_person_from_handle(e).primary_name.get_surname())
                    self.doc.write_text(_("%s") %
                                        surname)
                    self.doc.end_paragraph()
                    self.doc.end_cell() 


                    #Place of Event
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                 self.find_place(self.__db.get_event_from_handle(ev)))
                    self.doc.end_paragraph()
                    self.doc.end_cell()
    
                    # FamID
#                    FID = "HI_FID"
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        FID) 
        #                                    (d)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
            
                    # FamID_P
#                    FID_H = "HI_FID"
                    family_handle = self.__db.get_person_from_handle(e).get_main_parents_family_handle()
                    if family_handle:
                        FID_P = self.__db.get_family_from_handle(family_handle).gramps_id
                    else:
                        FID_P = "NV"

                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        FID_P) 
        #                                    (d)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
                    
                    # AnzKind
                    AnzKind = 1000
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        AnzKind) 
        #                                    (d)) 
                    self.doc.end_paragraph()
                    self.doc.end_cell()              
                    
                    
                    #Latitude of Place of Event
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    lat_txt =""
                    lon_txt =""
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                    self.doc.write_text(_("%s") %
                                 lat_txt)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                    
                    #Longitude of Place of Event
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    lat_txt =""
                    lon_txt =""
                    lat_txt, lon_txt = self.find_place_lat_lon(self.__db.get_event_from_handle(ev))
                    self.doc.write_text(_("%s") %
                                 lon_txt)
                    self.doc.end_paragraph()
                    self.doc.end_cell()                                                             
       
#                    # Citation
 #                   self.doc.start_cell("SRC-Cell")
  #                  self.doc.start_paragraph("SRC-SourceDetails")
   #                 self.doc.write_text(_("%s") %
    #                                    ci[ev])
     #               self.doc.end_paragraph()
      #              self.doc.end_cell()
                    
                    self.doc.end_row()

        self.doc.end_table()
       


#------------------------------------------------------------------------
#
# VisoneParXLSReportOptions
#
#------------------------------------------------------------------------
class VisoneParXLSXReportOptions(MenuReportOptions):
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

#        incphotos = BooleanOption(_("Include Photos"), True)
#        incphotos.set_help(_("Whether to show photos mentioned in the citation"))
#        menu.add_option(category_name, "incphotos", incphotos)
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
        
        addfmglines = BooleanOption(_("Add Line for Father, Mother and groom"), False)
        addfmglines.set_help(_("Whether to add Line for Father, Mother and groom"))
        menu.add_option(category_name, "addfmglines", addfmglines)

    
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
        
        

      