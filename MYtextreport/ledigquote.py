#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008,2011  Gary Burton
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Heinz Brinker
# Copyright (C) 2013-2014  Paul Franklin
# Copyright (C) 2015       Hans Ulrich Frink
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

"""ledigquote Report"""

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
from gramps.gen.proxy import PrivateProxyDb
from gramps.gen.sort import Sort
from gramps.gen.utils.location import get_main_location
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.lib import PlaceType
from gramps.gen.lib import NameType, EventRoleType, EventType
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.config import config
#from gramps.gen.datehandler import get_date

from collections import OrderedDict, defaultdict
from operator import itemgetter

cal = config.get('preferences.calendar-format-report')

class ledigquote(Report):
    """
    ledigquote Report class
    """
    def __init__(self, database, options, user):
        """
        Create the ledigquote Report object produces the ledigquote report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - instance of a gen.user.User class

        This report needs the following parameters (class variables)
        that come in the options class.
        
        places          - List of places to report on.
#        classwidth          - classwidth of report, person or event
        incpriv         - Whether to include private data

        """

        Report.__init__(self, database, options, user)

        self._user = user
        menu = options.menu
        places = menu.get_option_by_name('places').get_value()
        self.classwidth  = menu.get_option_by_name('classwidth').get_value()
        self.incpriv = menu.get_option_by_name('incpriv').get_value()

        self.set_locale(menu.get_option_by_name('trans').get_value())

        name_format = menu.get_option_by_name("name_format").get_value()
        if name_format != 0:
            self._name_display.set_default_format(name_format)
        self._nd = self._name_display
        
        if self.incpriv:
            self.database = database
        else:
            self.database = PrivateProxyDb(database)

        filter_option = menu.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
        self.sort = Sort(self.database)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of place handles
            plist = self.database.iter_place_handles()
            self.place_handles = self.filter.apply(self.database, plist)
        else:
            # Use the place handles selected without a filter
            self.place_handles = self.__get_place_handles(places)

        self.place_handles.sort(key=self.sort.by_place_title_key)
        
    def write_report(self):
        """
        The routine that actually creates the report.
        At this point, the document is opened and ready for writing.
        """
        pdet_list=[]
        # Write the title line. Set in INDEX marker so that this section will be
        # identified as a major category if this is included in a Book report.

        title = self._("Ledigenquote und Verheiratetenanteile ")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)        
        self.doc.start_paragraph("PLC-ReportTitle")
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        self.doc.start_paragraph("PLC-Section")
        self.doc.write_text("Enthält alle Personen, die in diesem Ort geboren oder getauft wurden")
        self.doc.end_paragraph()
        self.doc.start_table("LEQUODETTable", "SRC-LEQUODETTable")
        column_titles = [_("name"), _("Klasse"), _("ID"), _("m/w"), _("birth"), _("death"), _("marriage"), _("date"), _("weitere Heiraten"), _("Alter Tod"), _("Alter Hochzeit"), _("place"), _("LNR") ] 
        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()

        self.__write_data(pdet_list, self.classwidth)

        self.doc.end_table()
        
# Männer Tabelle        
        self.doc.start_paragraph("PLC-Section")
        self.doc.write_text("Ledigenquote und Verheiratetenanteile bei Männern")
        self.doc.end_paragraph()
        self.doc.start_table("LEQUODETTable", "SRC-LEQUODETTable")
        column_titles = [_("cat"), _("ID"), _("m/w"), _("birth"), _("birthclass"),_("death"), _("marriage"), _("date"), _("weitere Heiraten"), _("Alter Tod"), _("Alter Hochzeit"), _("place"), _("LNR") ] 
        i = 0
        self.doc.start_row()
        for title in column_titles:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(title)
            self.doc.end_paragraph()
            self.doc.end_cell()
        self.doc.end_row()

        self.__write_statistics(pdet_list, self.classwidth)

        self.doc.end_table()

    def __write_data(self,pdet_list,clw):
        """
        This procedure writes out each of the families related to the place
        """
        i = 0
        iw = 0
        ifam = 0
        p_set=set()
#        pdet_list=[]
        QUAL_ESTIMATED = 1
        gender_dict ={0:"w",1:"m", 2:"u"}


        for person in self.database.iter_people():
            birth_event = get_birth_or_fallback(self.database, person)
            b_year = 0
            alt_tod = 0
            b_role = "ROLLE"
            if birth_event:
                if birth_event.get_place_handle() in self.place_handles:
                    birth_obj = birth_event.get_date_object()
                    if birth_obj.get_quality() is not QUAL_ESTIMATED:
                        place_d = place_displayer.display_event(self.database, birth_event)                             
                        person_name = person.get_primary_name().get_surname()
                        person_ID = person.get_gramps_id()
                        gender = gender_dict[person.get_gender()]

                        m_date = self._get_date(birth_obj)
        #                if birth_obj.get_quality() is not QUAL_ESTIMATED:
                        b_year = int(birth_obj.get_year())
          #              b_role = "ROLLE "+ str(birth_event.role)
        #                    b_place = 
                        death_event = get_death_or_fallback(self.database, person)
                        d_year = 0
                        if death_event:
                            death_obj = death_event.get_date_object()
            #                if death_obj.get_quality() is not QUAL_ESTIMATED:
                            d_year = death_obj.get_year() 
                            alt_tod = d_year - b_year
                        m_year = 0    
    
                        alt_marr = 0
    
                        m_list=[]
    #                    m_date = ""
                        m_wm = "WEIT"
                        for family_handle in person.get_family_handle_list():
    #                        print(family_handle)
                            family = self.database.get_family_from_handle(family_handle)
            
                            for fam_event_ref in family.get_event_ref_list():
    #                            print(fam_event_ref)
                                if fam_event_ref:
                                    fam_event = self.database.get_event_from_handle(fam_event_ref.ref)
                                    if fam_event.type == EventType.MARRIAGE:
                                        print(fam_event.type)
                                        m_list.append(fam_event.get_date_object().get_year())
    #                                    print(fam_event.get_date_object().get_year())
    #                                    m_year = fam_event.get_date_object().get_year()
                        if len(m_list)>0:
                            m_year = min(m_list)
                            alt_marr = m_year - b_year
    #                    else:
    #                        m_year = 0    
                        for m in m_list:
                            m_wm = m_wm+" "+str(m)               
                        
                
        #                person_details = [ person, person_name, person_ID, gender, b_year, d_year, m_year, b_role, m_date, diff,place_d]
                        person_details = [ person, person_name, person_ID, gender, b_year, d_year, m_year, m_date, m_wm, alt_tod, alt_marr, place_d]
        
                        pdet_list.append(person_details)
        i=1
        for pn in pdet_list:
            self.doc.start_row()
  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            ST = "PN"+ str(pn[0])
#            self.doc.write_text(_("%s") % ST)
#    #        self.doc.write_text(_("Hallo0"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[1])
      #      self.doc.write_text(_("Hallo1"))
            self.doc.end_paragraph()
            self.doc.end_cell()
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
           
            Klasse = int(int(pn[4])/clw)*clw
            self.doc.write_text(_("%s") % Klasse)
            self.doc.end_paragraph()
            self.doc.end_cell()
    
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[2])
       #     self.doc.write_text(_("Hallo2"))
            self.doc.end_paragraph()
            self.doc.end_cell()
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[3])
        #    self.doc.write_text(_("Hallo3"))
            self.doc.end_paragraph()
            self.doc.end_cell()
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[4])
         #   self.doc.write_text(_("Hallo4"))
            self.doc.end_paragraph()
            self.doc.end_cell()
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[5])
 #           self.doc.write_text(_("Hallo5"))
            self.doc.end_paragraph()
            self.doc.end_cell()
  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[6])
  #          self.doc.write_text(_("Hallo6"))
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[7])
  #          self.doc.write_text(_("Hallo7"))
            self.doc.end_paragraph()
            self.doc.end_cell()

  
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[8])
  #          self.doc.write_text(_("Hallo8"))
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[9])
  #          self.doc.write_text(_("Hallo9"))
            self.doc.end_paragraph()
            self.doc.end_cell()

            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
#            diff= pn[6] - pn[4]
            self.doc.write_text(_("%s") % pn[10])
#            self.doc.write_text(diff)
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % pn[11])
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % i)
 #           self.doc.write_text(i)
  #          self.doc.write_text(_("LNR"))
            self.doc.end_paragraph()
            self.doc.end_cell()
            i +=1


            self.doc.end_row()

#########################
    def __write_statistics(self,list,clw):
        """
        This procedure writes out each of the families related to the place
        """
# build classes
        #year_list = list(pdet_list[4])
#        print(min(list[4]))
        start = 1640
        grownup = 18
        byear_list=[]
        dyear_list=[]
        myear_list=[]
        for ldi in list:
            byear_list.append(int(ldi[4]))
            dyear_list.append(int(ldi[5]))
            myear_list.append(int(ldi[6]))
#            print(ldi[4], ldi[5], ldi[6])
#        for l in byear_list:
#            print(l)
#        print(min(byear_list),max(byear_list),len(byear_list))
#        print(min(dyear_list),max(dyear_list),len(dyear_list))
#        print(min(myear_list),max(myear_list),len(myear_list))
#        for l4 in list:
#            print(l4[4])
#        print(min(byear_list),max(byear_list),len(byear_list))

        schr =[]
        anz_birth =defaultdict(int)
        anz_death =defaultdict(int)
        anz_grownup =defaultdict(int)
        anz_married=defaultdict(int)
        anz_notmarried=defaultdict(int)
        anz_2529married=defaultdict(int)
        anz_2529=defaultdict(int)
        ant_2529=defaultdict(int)
        anz_45=defaultdict(int)
        ant_45=defaultdict(int)
        anz_45married=defaultdict(int)
        anz_20=defaultdict(int)
        ant_20=defaultdict(int)
        anz_20married=defaultdict(int)


        anz_ind=defaultdict(int)
        
        
        s = start
        print(clw)
        while (s < max(byear_list)and (s < 2100)):
            s+=int(clw)
            schr.append(s)
        for i,si in enumerate(schr):
            print("Jahr",i, si)
            
# person_details = [ person, person_name, person_ID, gender, b_year, d_year, m_year, m_date, m_wm, alt_tod, alt_marr, place_d]
#                     0         1           2         3       4        5       6       7       8     9        10       11    
# pdet_list.append(person_details)             

        for by in sorted(list, key = itemgetter(4,5)):
            if by[4]>start:
                ind = int(int(by[4])/clw)*clw
                print("CODE ", by[4], ind)
                anz_ind[ind]=ind

#anz geb
                anz_birth[ind]+=1
# dav tot
                if by[5]>0:
                    anz_death[ind]+=1   
# sicher nicht verheiratet
                    if by[10]==0:   
                        anz_notmarried[ind]+=1       

# erwachsenenalter ereicht
                if by[9]>=grownup:   
                    anz_grownup[ind]+=1
# verheiratet                           
                if by[10]>=0:   
                    anz_married[ind]+=1       
# Anteil Verheirateter bei 25-27jg
                if (by[5]>24) or (by[5] ==0 and by[10]<30):
                    anz_2529[ind]+=1
                    if (by[10]<30)and (by[10]>0):   
                        anz_2529married[ind]+=1

# Anteil Verheirateter bei >45jg
                if (by[5]>44) or (by[5] ==0 and by[10]<45):
                    anz_45[ind]+=1
                    if (by[10]<46)and (by[10]>0):   
                        anz_45married[ind]+=1
                        
# Anteil Verheirateter bei 20jg
                if (by[5]>44) or (by[5] ==0 and by[10]<21):
                    anz_20[ind]+=1
                    if (by[10]<21)and (by[10]>0):   
                        anz_20married[ind]+=1
                        



        for q in anz_2529married:
            print(q, anz_2529married[q], anz_2529[q], anz_2529married[q]/anz_2529[q], q / anz_2529[q])               
  #          ant_2529married = q / anz_2529[q]
#            print(q)    

        print("q", " anz_birth[q]", "anz_2529married[q]", "anz_2529[q]", "anz_2529married[q]/anz_2529[q]", "q / anz_2529[q]")    
        for q in anz_birth:
            print(q, anz_birth[q], anz_2529married[q], anz_2529[q], anz_2529married[q]/anz_2529[q], q / anz_2529[q])               
  

                                   

#        for i,si in enumerate(anz_birth):
#            print(i, si)
#        print (anz_birth.items())   

        title_stat = ["Jahr", "Geburten", "davon mit Sterbedatum", "Erwachsenenalter erreicht", "je verheiratet", "sicher ledig", "Verheiratetenanteil bei 25-30 jährigen Männern", "Verheiratetenanteil bei Männern über 45 Jahren", "Ledigenquote der über 45jährigen", "Ledigenquote der über 20jährigen"]
        
        self.doc.start_row()
        for t in title_stat:
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(t)
            self.doc.end_paragraph()
            self.doc.end_cell() 
        self.doc.end_row()
        
        for k in sorted(anz_birth.keys()):
            self.doc.start_row()
#            print(k, anz_birth[k])        
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % k)
            self.doc.end_paragraph()
            self.doc.end_cell()
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % anz_birth[k])
            self.doc.end_paragraph()
            self.doc.end_cell()

            
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % anz_ind[k])
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % anz_death[k])
            self.doc.end_paragraph()
            self.doc.end_cell()

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % anz_grownup[k])
            self.doc.end_paragraph()
            self.doc.end_cell()
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % anz_married[k])
            self.doc.end_paragraph()
            self.doc.end_cell()
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            self.doc.write_text(_("%s") % anz_notmarried[k])
            self.doc.end_paragraph()
            self.doc.end_cell()
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            Pro25 = anz_2529married[k]*100/ anz_2529[k]
            self.doc.write_text(_("%.2f") % Pro25)            
            self.doc.end_paragraph()
            self.doc.end_cell()            

            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            Pro45 = anz_45married[k]*100/ anz_45[k]
            self.doc.write_text(_("%.2f") % Pro45)            
            self.doc.end_paragraph()
            self.doc.end_cell()    
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            led45 = 100-(anz_45married[k]*100/ anz_45[k])
            self.doc.write_text(_("%.2f") % led45)            
            self.doc.end_paragraph()
            self.doc.end_cell()    
            
            self.doc.start_cell("SRC-TableColumn")
            self.doc.start_paragraph("SRC-ColumnTitle")
            led20 = 100-anz_20married[k]*100/ anz_45[k]
            self.doc.write_text(_("%.2f") % led20)            
            self.doc.end_paragraph()
            self.doc.end_cell()    
            
            
                    
            self.doc.end_row()

                

        #cm=min()
#        i=1
#        for pn in pdet_list:
#            self.doc.start_row()
#  
##            self.doc.start_cell("SRC-TableColumn")
##            self.doc.start_paragraph("SRC-ColumnTitle")
##            ST = "PN"+ str(pn[0])
##            self.doc.write_text(_("%s") % ST)
##    #        self.doc.write_text(_("Hallo0"))
##            self.doc.end_paragraph()
##            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[1])
#      #      self.doc.write_text(_("Hallo1"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[2])
#       #     self.doc.write_text(_("Hallo2"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[3])
#        #    self.doc.write_text(_("Hallo3"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[4])
#         #   self.doc.write_text(_("Hallo4"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[5])
# #           self.doc.write_text(_("Hallo5"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#  
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[6])
#  #          self.doc.write_text(_("Hallo6"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[7])
#  #          self.doc.write_text(_("Hallo7"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[8])
#  #          self.doc.write_text(_("Hallo8"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
#            self.doc.write_text(_("%s") % pn[9])
#  #          self.doc.write_text(_("Hallo9"))
#            self.doc.end_paragraph()
#            self.doc.end_cell()
#
#            
#            self.doc.start_cell("SRC-TableColumn")
#            self.doc.start_paragraph("SRC-ColumnTitle")
##            diff= pn[6] - pn[4]
#            self.doc.write_text(_("%s") % pn[10])
##            self.doc.write_text(diff)
#            self.doc.end_paragraph()
 #           self.doc.end_cell()
 #
 #           self.doc.start_cell("SRC-TableColumn")
 #           self.doc.start_paragraph("SRC-ColumnTitle")
 #           self.doc.write_text(_("%s") % pn[11])
 #           self.doc.end_paragraph()
 #           self.doc.end_cell()
 #
 #           self.doc.start_cell("SRC-TableColumn")
 #           self.doc.start_paragraph("SRC-ColumnTitle")
 #           self.doc.write_text(_("%s") % i)
 ##           self.doc.write_text(i)
 # #          self.doc.write_text(_("LNR"))
 #           self.doc.end_paragraph()
  #          self.doc.end_cell()
  #          i +=1
  #
  #
  #          self.doc.end_row()
  #
#########################
            
    def __format_date(self, date_object):
        if not date_object: return
        d=date_object.get_day()    
        m=date_object.get_month()
        y=date_object.get_year()
        if (d == 0) and (m == 0):
            date_f = (" %s" % y)
        elif (d == 0) and not (m == 0):
            date_f = (" %s.%s" % (m, y))  
        else:       
            date_f = (" %s.%s.%s" % (d, m, y)) 
        return date_f           
        

        
    def __get_place_handles(self, places):
        """
        This procedure converts a string of place GIDs to a list of handles
        """
        place_handles = [] 
        for place_gid in places.split():
            place = self.database.get_place_from_gramps_id(place_gid)
            if place is not None:
                place_handles.append(place.get_handle())

        return place_handles
    
#------------------------------------------------------------------------
#
# ledigquoteOptions
#
#------------------------------------------------------------------------
class ledigquoteOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, database):
        MenuReportOptions.__init__(self, name, database)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the place report.
        """
        category_name = _("Report Options")

        # Reload filters to pick any new ones
        CustomFilters = None
        from gramps.gen.filters import CustomFilters, GenericFilter

        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Place'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)

        stdoptions.add_name_format_option(menu, category_name)

        places = PlaceListOption(_("Select places individually"))
        places.set_help(_("List of places to report on"))
        menu.add_option(category_name, "places", places)

#        classwidth = EnumeratedListOption(_("Class wdith"), "classwidth")
        classwidth = EnumeratedListOption(_("Class wdith"), 10)

        classwidth.set_items([
                (10, _("10 Years")),
                (20, _("20 Years")),
                (40, _("40 Years")),
                (50, _("50 Years"))])
        classwidth.set_help(_("classwidth fpr Analysis"))
        menu.add_option(category_name, "classwidth", classwidth)

        incpriv = BooleanOption(_("Include private data"), True)
        incpriv.set_help(_("Whether to include private data"))
        menu.add_option(category_name, "incpriv", incpriv)
         
        stdoptions.add_localization_option(menu, category_name)

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
        self.__LEQUODET_table_style()
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
        self.default_style.add_paragraph_style("PLC-ReportTitle", para)

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
        self.default_style.add_paragraph_style("PLC-SourceDetails", para)

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
        self.default_style.add_paragraph_style("PLC-Section", para)

    def __LEQUODET_table_style(self):
        """
        Define the style used for event table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(14)
        table.set_column_width(0, 8)
        table.set_column_width(1, 3)
        table.set_column_width(2, 6)
        table.set_column_width(3, 6)
        table.set_column_width(4, 6)
        table.set_column_width(5, 6)
        table.set_column_width(6, 6)
        table.set_column_width(7, 12)
        table.set_column_width(8, 6)
        table.set_column_width(9, 30)
        table.set_column_width(10, 5)

        self.default_style.add_table_style("SRC-LEQUODETTable", table)          

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
        
