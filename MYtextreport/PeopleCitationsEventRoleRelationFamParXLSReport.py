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
# Version 2.6
# $Id: PeopleCitationsReport.py 2012-12-30 Frink hansulrich.frink@gmail.com $

"""
Reports/Text Report.

Developed for gramps 3.4.2.1 under win 8 64bit

This report lists all the citations and their notes in the database. so it 
is possible to have all the copies made from e.g. parish books together grouped 
by source and ordered by citation.page.

I needed such a report after I changed recording notes and media with the
citations and no longer with the sources.

works well in pdf, text and odf Format. The latter contains TOC which are also
accepted by ms office 2012 

Changelog:

Version 2.5:
- sources are sorted by source.author+title+publ+abbrev
- no German non translatables
- added Filter cf. PlaceReport.py
- changed citasource from gramps_id to citation rsp. source
- constructing dic directly
- or function
- sorting direct 
- Stylesheet in Options
- added .lower to sortfunctions to sources and to citation
- get translation work
- include Persons names and gramps_id cited in the notes.

Version 2.6:
- SR for relation text
- Include Fam ID

next steps:

- have an index on Persons  
- have footer        

"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
#import posixpath
from __future__ import division
import time, datetime
from collections import defaultdict, Counter
#from gen.ggettext import gettext as _


#------------------------------------------------------------------------
#
# GRAMPS modules  alt
#
#------------------------------------------------------------------------
#-import gen.lib
#-from gen.lib import EventRoleType
#-from gen.plug.menu import StringOption, MediaOption, NumberOption
#-from gen.plug.menu import FilterOption, PlaceListOption, EnumeratedListOption, \
#-                          BooleanOption
#-from gen.plug.report import Report
#-from gen.plug.report import MenuReportOptions
#-from gen.plug.report import utils as ReportUtils

#-from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, TableStyle,
#-                            TableCellStyle, FONT_SERIF, FONT_SERIF, 
#-                            INDEX_TYPE_TOC, INDEX_TYPE_ALP, PARA_ALIGN_CENTER, PARA_ALIGN_RIGHT)                    

                    
#from Utils import media_path_full
#-import DateHandler
#-import MY_Relationship

#-from TransUtils import get_addon_translator
#-_ = get_addon_translator(__file__).gettext

##############################################
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
#from gramps.gen.const import URL_HOMEPAGE
from gramps.gen.errors import ReportError
from gramps.gen.lib import NameType, EventRoleType, EventType, Name, Date, Person, Surname
from gramps.gen.lib.date import gregorian
from gramps.gen.my_relationship import get_relationship_calculator
from gramps.gen.plug.menu import (BooleanOption, StringOption, NumberOption, 
                                  EnumeratedListOption, FilterOption, MediaOption,
                                  PersonOption, PlaceListOption, EnumeratedListOption,)
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.plug.docgen import (FontStyle, ParagraphStyle, GraphicsStyle,
                                    TableStyle, TableCellStyle,
                                    FONT_SERIF, PARA_ALIGN_RIGHT,
                                    PARA_ALIGN_LEFT, PARA_ALIGN_CENTER,
                                    IndexMark, INDEX_TYPE_TOC)

#from gramps.gen.utils.string import conf_strings
#
#import gramps.plugins.lib.libholiday as libholiday
#
## localization for BirthdayOptions only!!
from gramps.gen.datehandler import displayer as _dd
from gramps.gen.datehandler import get_date
#
#
##########################################

#------------------------------------------------------------------------
#
# PeopleCitationsEventRoleRelationParXLSReport
#
#------------------------------------------------------------------------
class PeopleCitationsEventRoleRelationParXLSReport(Report):
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
#p        self.person   = gen.lib.Person
        self.person   = Person
       
        menu = options.menu
        self.title_string = menu.get_option_by_name('title').get_value()
        self.subtitle_string = menu.get_option_by_name('subtitle').get_value()
        self.footer_string = menu.get_option_by_name('footer').get_value()
        self.showinlaw = menu.get_option_by_name('showinlaw').get_value()
#        self.showperson = menu.get_option_by_name('showperson').get_value()
#        self.addimages     = menu.get_option_by_name('incphotos').get_value()

        
        filter_option = menu.get_option_by_name('filter')
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
        self._user.begin_progress(_('PeopleCitationsEventRoleRelationReport'), 
                                  _('printing...'), 0)
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
        
    def get_spouse(self, person):
##       imported from all_relations.py  and changed name get_inlaws => get_spouse
        inlaws = []
        family_handles = person.get_family_handle_list()
        for handle in family_handles:
            fam = self.__db.get_family_from_handle(handle)
            if fam.father_handle and \
                    not fam.father_handle == person.handle:
                inlaws.append(self.__db.get_person_from_handle(
                                                        fam.father_handle))
            elif fam.mother_handle and \
                    not fam.mother_handle == person.handle:
                inlaws.append(self.__db.get_person_from_handle(
                                                        fam.mother_handle))
        return inlaws

      
    def inlaw_rel (self, p_pershandle, r_pershandle): 
        #############################
        # Sucht alle Kinder der Urgrosseltern und Grosseltern
        # und speichert deren spouses in inlaws_pers

        inlaws_pers =[]
        inlaws_pers_rel =[]
        schwager_text = "nicht verwandt"
        tr = []
#Eltern 
        par = []
        family_handle = self.__db.get_person_from_handle(p_pershandle).get_main_parents_family_handle()
        if family_handle:
            fh = self.__db.get_family_from_handle(family_handle).father_handle
            if fh:
                par.append(fh)
            mh = self.__db.get_family_from_handle(family_handle).mother_handle
            if mh:
                par.append(mh)
#Grosseltern 
        gpar = []    #handle
        i=0
        for Par in par: 
            i+=1
            family_handle = self.__db.get_person_from_handle(Par).get_main_parents_family_handle()
            if family_handle:
                fh = self.__db.get_family_from_handle(family_handle).father_handle
                if fh:
                    gpar.append(fh)
                fh = self.__db.get_family_from_handle(family_handle).mother_handle
                if fh:
                    gpar.append(fh)
#UrGrosseltern 
        tr.append(i)
        i=0
        ugpar = []  #handle
        for GPar in gpar: 
            i+=1
            family_handle = self.__db.get_person_from_handle(GPar).get_main_parents_family_handle()
            if family_handle:
                fh = self.__db.get_family_from_handle(family_handle).father_handle
                if fh:
                    ugpar.append(fh)
                fh = self.__db.get_family_from_handle(family_handle).mother_handle
                if fh:
                    ugpar.append(fh)
# alle Kinder der UrGrosseltern in der GrossElterngeneration
        tr.append(i)
        i=0

        gpar_pers = [] #person       
        for UGPar in ugpar: 
            for family_handle in self.__db.get_person_from_handle(UGPar).get_family_handle_list():
                chlist = self.__db.get_family_from_handle(family_handle).child_ref_list
                for chref in chlist:
                    i+=1

                    gpar_pers.append(self.__db.get_person_from_handle(chref.ref))
# HIER Schwager in LISTE
                    for sp in self.get_spouse(self.__db.get_person_from_handle(chref.ref)):
                        inlaws_pers.append(sp)
                        inlaws_pers_rel.append(_("Grossonkel"))
# alle Kinder der Grosseltern in der Elterngeneration

        tr.append(i)
        i=0

        ugpar_pers = []  #person      
        for GPar_pers in gpar_pers: 
            for family_handle in GPar_pers.get_family_handle_list():
                chlist = self.__db.get_family_from_handle(family_handle).child_ref_list
                for chref in chlist:
                    i+=1

                    ugpar_pers.append(self.__db.get_person_from_handle(chref.ref))
# HIER Schwager in LISTE
                    for sp in self.get_spouse(self.__db.get_person_from_handle(chref.ref)):
                        inlaws_pers.append(sp)
                        inlaws_pers_rel.append("Onkel")
        tr.append(i)
        i=0

#KORR
        ngpar_pers = []  #person      
        for GPar in gpar: 
            for family_handle in self.__db.get_person_from_handle(GPar).get_family_handle_list():
                chlist = self.__db.get_family_from_handle(family_handle).child_ref_list
                for chref in chlist:
                    i+=1

                    ngpar_pers.append(self.__db.get_person_from_handle(chref.ref))
# HIER Schwager in LISTE
                    for sp in self.get_spouse(self.__db.get_person_from_handle(chref.ref)):
                        inlaws_pers.append(sp)
                        inlaws_pers_rel.append("Onkel")
        tr.append(i)
        i=0


        for inl in inlaws_pers:
#!            schwager_text = schwager_text + ' '+ inl.gramps_id

#!        for ii in tr:
#!            schwager_text = schwager_text + (_("%s") % ii)

#            schwager_text = schwager_text + ' '+ inl.gramps_id
            if inl.gramps_id == self.__db.get_person_from_handle(r_pershandle).gramps_id:
#               schwager_text = inl.gramps_id + " (angeheiratet)"
                if inl.get_gender() == self.person.FEMALE:
                    if inlaws_pers_rel[inlaws_pers.index(inl)] == "Onkel":
                        schwager_text = "Tante"
                    if inlaws_pers_rel[inlaws_pers.index(inl)] == "Grossonkel":
                        schwager_text = "Grosstante"
                if inl.get_gender() == self.person.MALE:        
                    schwager_text = inlaws_pers_rel[inlaws_pers.index(inl)]
                schwager_text = inlaws_pers_rel[inlaws_pers.index(inl)]+"(angeheiratet)"
        return schwager_text



#######################################################################                                         
    def personrelation(self, Fam, rolepershandle, primpershandle, primpersAhandle, primpersBhandle, inlaw):
        
        if rolepershandle:
            
            # Relation
            # For Single Person Events
        
            if Fam == 0:
            
                relation_text = "nicht verwandt"
            #    self.doc.start_cell("SRC-Cell")
            #    self.doc.start_paragraph("SRC-SourceDetails")
                
#p                rel_calc = my_Relationship.get_relationship_calculator()
                rel_calc = get_relationship_calculator()
                
                relation = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpershandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relation:
                    relation_text = _("%s" % relation)
                elif self.__db.get_person_from_handle(primpershandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_text = _("IP ")
                elif (self.showinlaw == 1) and (Fam == 0):
                    inlaw_text = self.inlaw_rel(primpershandle, rolepershandle)
                    relation_text = inlaw_text
                return (_("%s") % relation_text)
                


            # Relation
            # For Family Events
            
            if Fam == 1:
                
                relation_text = "nicht verwandt"
                relation_textA = ""
                relation_textB = ""
                
#p                rel_calc = my_Relationship.get_relationship_calculator()
                rel_calc = get_relationship_calculator()
                
                relationA = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpersAhandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relationA:
                    relation_textA = _("To bride: %s" % relationA)
                elif self.__db.get_person_from_handle(primpersAhandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_text = _("IP ")

#p                rel_calc = my_Relationship.get_relationship_calculator()
                rel_calc = get_relationship_calculator()
                
                relationB = rel_calc.get_one_relationship(
                                                        self.__db, 
                                                        self.__db.get_person_from_handle(primpersBhandle),
                                                        self.__db.get_person_from_handle(rolepershandle))
                if relationB:
                    relation_textB = _("To groom: %s" % relationB)
                elif self.__db.get_person_from_handle(primpersBhandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                    relation_text = _("IP ")
                if (relation_textA + relation_textB) !="":
                    relation_text = relation_textA + " " + relation_textB
#            relation_text = relation_text + str(primpersAhandle)+ " "   + str(primpersBhandle)  + " "   + str(rolepershandle)

            if self.showinlaw == 0:
                return (_("%s") % relation_text)
#                
#            elif (self.showinlaw == 1) and (Fam == 0):
#                inlaw_text = self.inlaw_rel(primpershandle, rolepershandle)
#
#                relation_text = relation_text +' '+inlaw_text
#               
#    
#                return (_("%s") % relation_text)

    def personrelation1(self, rolepershandle, primpershandle):
        
        if rolepershandle:
            
            # Relation
            # For Single Person Events
        
            relation_text = "nicht verwandt"
            rel_calc = get_relationship_calculator(reinit=True,
                                                    clocale=glocale)
            
#            relation = rel_calc.get_one_relationship(
#                                                    self.__db, 
#                                                    self.__db.get_person_from_handle(primpershandle),
#                                                    self.__db.get_person_from_handle(rolepershandle))
#
###########################################
            (relation, Ga, Gb) = rel_calc.get_one_relationship(
                                                    self.__db, 
                                                    self.__db.get_person_from_handle(primpershandle),
                                                    self.__db.get_person_from_handle(rolepershandle),
                                                    extra_info = True)
            if relation:
                    relation_text = "%s (Ga= %d Gb= %d)" % (relation, Ga, Gb)

            #########################################
            #if self.advrelinfo:
            #    (relationship, Ga, Gb) = self.rel_calc.get_one_relationship(
            #                self.database, self.center_person, person,
            #                extra_info=True, olocale=self._locale)
            #    if relationship:
            #        label += "%s(%s Ga=%d Gb=%d)" % (lineDelimiter,
            #                                         relationship, Ga, Gb)
            ##########################################
                                                    
#            if relation:
#                relation_text = _("%s" % relation)
            elif self.__db.get_person_from_handle(primpershandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                relation_text = _("IP ")
            elif (self.showinlaw == 1):
                inlaw_text = self.inlaw_rel(primpershandle, rolepershandle)
                relation_text = inlaw_text
            return (_("%s") % relation_text)


    def personrelationpath(self, rolepershandle, primpershandle):
        
        if rolepershandle:
            
            # Relation
            # For Single Person Events
        
            relation_text = "nicht verwandt"
            rel_calc = get_relationship_calculator(reinit=True,
                                                    clocale=glocale)
            
            (relation, Ga, Gb) = rel_calc.get_one_relationship(
                                                    self.__db, 
                                                    self.__db.get_person_from_handle(primpershandle),
                                                    self.__db.get_person_from_handle(rolepershandle),
                                                    extra_info = True)
            if relation:
                    relation_text = "%s (Ga= %d Gb= %d)" % (relation, Ga, Gb)

            #########################################
            #if self.advrelinfo:
            #    (relationship, Ga, Gb) = self.rel_calc.get_one_relationship(
            #                self.database, self.center_person, person,
            #                extra_info=True, olocale=self._locale)
            #    if relationship:
            #        label += "%s(%s Ga=%d Gb=%d)" % (lineDelimiter,
            #                                         relationship, Ga, Gb)
            ##########################################
                                                    
#            if relation:
#                relation_text = _("%s" % relation)
            elif self.__db.get_person_from_handle(primpershandle).gramps_id == self.__db.get_person_from_handle(rolepershandle).gramps_id: 
                relation_text = _("IP ")
            elif (self.showinlaw == 1):
                inlaw_text = self.inlaw_rel(primpershandle, rolepershandle)
                relation_text = inlaw_text
            return (_("%s") % relation_text)

    
    def listpersonref(self):
    
        
        sc = {'source': 'S_ID',
              'citalist': 'C_ID' }
        stc = {}      
        citation_without_notes = 0
        EMPTY = " "

        def toYear(date):
            yeartext = date.get_year()
            return yeartext
            
     # genderlist = ['w','m']
        genderlist = ['w','m']            
 
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

#        for pe in self.__db.get_person_handles(sort_handles=True):
#            for eventref in self.__db.get_person_from_handle(pe).event_ref_list:
#                evdic[eventref.ref].append((self.__db.get_event_from_handle(eventref.ref).get_date_object().get_sort_value(),eventref.ref,eventref.get_role(),self.__db.get_person_from_handle(pe).primary_name.get_name(),pe))

        for pe in self.__db.get_person_handles(sort_handles=True):
            for eventref in self.__db.get_person_from_handle(pe).event_ref_list:
                if eventref.ref in ci_evkeys:
                    evdic[eventref.ref].append((self.__db.get_event_from_handle(eventref.ref).get_date_object().get_sort_value(),eventref.ref,eventref.get_role(),self.__db.get_person_from_handle(pe).primary_name.get_name(),pe))




        self.doc.start_paragraph("SRC-SourceTitle")
        self.doc.write_text(_("Person with Citations"))
        self.doc.end_paragraph()       


        evkeys = evdic.keys()
#        evkeys.sort
        
        StatCount = Counter()
        
        self.doc.start_table("PersonRoleEventTable", "SRC-PersonEventRoleTable")
        column_titles = [_("LNr"), _("Ev ID"),_("Event"), _("Date"), _("Year"), _("Prim_Place"), _("Prim_FamID"), _("Primary"), _("Prim_ID"),_("Prim_Gender"),_("Prim_DeathYear"),_("Prim_DeathPlace"), _("Person"), _("Pers_Gramps_ID"), _("PERS_FAM_ID"), _("Pers_Gender"), _("Pers_BIR_YEAR"),_("Pers_BIR_PLC"), _("Role"), _("Relation"), _("Relationpath")] 
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
        
        for ev in sorted(evkeys):
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
                     name_id = self.__db.get_person_from_handle(e).gramps_id
                     name_handle = e
                     name_Fam = self.__db.get_family_from_handle(self.__db.get_person_from_handle(e).get_main_parents_family_handle())
                     if name_Fam:
                        name_Fam_id = name_Fam.get_gramps_id()
                     FamilyText = "FAMILY"  

#######################


                     death_place_string = "UNKNOWN"
                     death_string='NV'
                     death_ref = self.__db.get_person_from_handle(e).get_birth_ref()
                     if death_ref:
                         death_date = self.__db.get_event_from_handle(death_ref.ref).get_date_object()
                         if death_date:
                             death_string = self.__db.get_event_from_handle(death_ref.ref).get_date_object().get_year()
                             #Event Place
                             death_place_string = ''
                             place_handle = self.__db.get_event_from_handle(death_ref.ref).get_place_handle()
                             if place_handle:
                                 death_place_string = self.database.get_place_from_handle(
                                                                 place_handle).get_title()
                     else:
                         for eventref in self.__db.get_person_from_handle(e).event_ref_list:
                             if eventref.role == EventRoleType.PRIMARY:
                                 if self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.BURIAL:
                                     death_string = self.__db.get_event_from_handle(eventref.ref).get_date_object().get_year() 
                                     place_handle = self.__db.get_event_from_handle(eventref.ref).get_place_handle()
                                     if place_handle:
                                         death_place_string = self.database.get_place_from_handle(
                                                                             place_handle).get_title()




###########################







                elif c != EventRoleType.PRIMARY:
                    # if it is a familyevent
                    for k in fedickeys:                         
                        if ev == k:
                            for (a,b,c) in fedic[k]:
                                Fam = 1
                                self.FamilyText = (_("%s") %
                                                self.__db.get_event_from_handle(ev).get_type())
                                self.FamilyText = self.FamilyText +(_("   Eheleute: "))
                                try:
                                    self.FamilyText = self.FamilyText + (_(" %s ") %  self.__db.get_person_from_handle(b).primary_name.get_name()) 
                                    primarypersonBhandle = b             
                                except:
                                    self.FamilyText = self.FamilyText + (_("unknown"))                                           
                                try:
                                    self.FamilyText = self.FamilyText + (_(" and %s ") %  self.__db.get_person_from_handle(a).primary_name.get_name())
                                    primarypersonAhandle = a  
                                except:
                                    self.FamilyText = self.FamilyText + (_("and unknown"))                                           
                                name = self.FamilyText                
                else:
                     continue     
                   
            for (a,b,c,d,e) in evdic[ev]:
                if c == EventRoleType.PRIMARY:
                    continue
                
                elif c != EventRoleType.PRIMARY:     
                    
                    ii+=1
                    # LNR
                    self._user.step_progress()
                    self.doc.start_row()
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
#                                        toYear(get_date(self.__db.get_event_from_handle(b))))
# ok                                        get_date(self.__db.get_event_from_handle(b)).get_year())

                                        self.__db.get_event_from_handle(b).get_date_object().get_year())

                    self.doc.end_paragraph()  
                    self.doc.end_cell()

                    #Event Place
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    
                    place = ''
                    place_handle = self.__db.get_event_from_handle(b).get_place_handle()
                    if place_handle:
                        place = self.database.get_place_from_handle(
                                                        place_handle).get_title()
                    self.doc.write_text(_("%s") %
                                        place)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
        
                    # Primary Family ID 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    #name_id = self.__db.get_person_from_handle(name_handle).get_main_parents_family_handle()
                    
                    self.doc.write_text(_("%s") %
                                        name_Fam_id)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                    
                    # Primary Role Name 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        name)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                                               
                    # Primary Role ID 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        name_id)
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

                    # Primary death year
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        death_string)
                    self.doc.end_paragraph()
                    self.doc.end_cell()

                    # Primary death place
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        death_place_string)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                                               
                    # Person Name
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                         d) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 
                                   
                    # Person ID
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %                              
                                        self.__db.get_person_from_handle(e).gramps_id) 
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    # Person Family ID 
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    name_Pers_Fam = self.__db.get_family_from_handle(self.__db.get_person_from_handle(e).get_main_parents_family_handle())
                    if name_Pers_Fam:
                        name_Pers_Fam_id = name_Pers_Fam.get_gramps_id()
                    self.doc.write_text(_("%s") %
                                        name_Pers_Fam_id)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                    
                    # Person gender
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                        genderlist[self.__db.get_person_from_handle(e).gender])
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    #######################################
                    # Birth or BAPT of second Person               
                    self.doc.start_cell("SRC-Cell")

                    self.doc.start_paragraph("SRC-SourceDetails")
                    birth_ref = self.__db.get_person_from_handle(e).get_birth_ref()
                    birth_date = None
                    Birth_string = "NO"
                    Birth_place_string = "UNKNOWN"
                    if birth_ref:
                        birth_date = self.__db.get_event_from_handle(birth_ref.ref).get_date_object()
                        if birth_date:
                            Birth_string = self.__db.get_event_from_handle(birth_ref.ref).get_date_object().get_year()
                            #Event Place
                            Birth_place_string = ''
                            place_handle = self.__db.get_event_from_handle(birth_ref.ref).get_place_handle()
                            if place_handle:
                                Birth_place_string = self.database.get_place_from_handle(
                                                                place_handle).get_title()
                    else:
                        for eventref in self.__db.get_person_from_handle(e).event_ref_list:
                            if eventref.role == EventRoleType.PRIMARY:
                                if self.__db.get_event_from_handle(eventref.ref).get_type() == EventType.BAPTISM:
                                    Birth_string = self.__db.get_event_from_handle(eventref.ref).get_date_object().get_year() 
                                    place_handle = self.__db.get_event_from_handle(eventref.ref).get_place_handle()
                                    if place_handle:
                                        Birth_place_string = self.database.get_place_from_handle(
                                                                            place_handle).get_title()
 
 
 #####################################################################################
 
              
                    self.doc.write_text(_(" %s") %
                               Birth_string)
                    self.doc.end_paragraph()
                    self.doc.end_cell() 

                    #######################################
                    #Birth Place PErson
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                               Birth_place_string)
                    self.doc.end_paragraph()
                    self.doc.end_cell()
                                   
                    # Event Role
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
                                         c)
                    self.doc.end_paragraph()  
                    self.doc.end_cell()
                    
#                    # Relation
#    
#                    Fam = 1
#                    self.doc.start_cell("SRC-Cell")
#                    self.doc.start_paragraph("SRC-SourceDetails")
#                    self.doc.write_text(_("%s") %
#                        self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1))
#                    self.doc.end_paragraph()  
#                    self.doc.end_cell()
#                    StatCount.update([self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1)])
#                    self.doc.end_row()

                    # Relation new
    
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
#                        self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1))
                        self.personrelation1(e, name_handle))

                    self.doc.end_paragraph()  
                    self.doc.end_cell()
                    StatCount.update([self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1)])
                    self.doc.end_row()

                    # Relation path
    
                    self.doc.start_cell("SRC-Cell")
                    self.doc.start_paragraph("SRC-SourceDetails")
                    self.doc.write_text(_("%s") %
#                        self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1))
                        self.personrelationpath(e, name_handle))

                    self.doc.end_paragraph()  
                    self.doc.end_cell()
                    StatCount.update([self.personrelation(Fam, e, name_handle, primarypersonAhandle, primarypersonBhandle, 1)])
                    self.doc.end_row()

        self.doc.end_table()

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
        
        for rel in sorted(StatCount):

            self.doc.start_row()
            
            # Relation
            self._user.step_progress()
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-SourceDetails")
            self.doc.write_text(_("%s") %
                                 rel)
            self.doc.end_paragraph()  
            self.doc.end_cell()
            
            # count

            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-StatCell")
            self.doc.write_text(_("%s") %
                                StatCount[rel])
            self.doc.end_paragraph()  
            self.doc.end_cell()
            
            # percent

            pc = 100*(StatCount[rel]) /(sum(StatCount.values()))
            self.doc.start_cell("SRC-Cell")
            self.doc.start_paragraph("SRC-StatCell")
#            self.doc.write_text(_(" %1.2f ") %  
            self.doc.write_text(_(" %.2f%% "  ) %
                                pc)
            self.doc.end_paragraph()  
            self.doc.end_cell()
            
            self.doc.end_row() 

            
        self.doc.start_row()
    
        # Total
        self.doc.start_cell("SRC-Cell")
        self.doc.start_paragraph("SRC-SourceDetails")
        self.doc.write_text(_("Total %s") %
                            len(StatCount))
        self.doc.end_paragraph()  
        self.doc.end_cell()
        
        self.doc.start_cell("SRC-Cell")
        self.doc.start_paragraph("SRC-StatCell")
        self.doc.write_text(_("%s") %
                  sum(StatCount.values()))
        self.doc.end_paragraph()  
        self.doc.end_cell()
        
        self.doc.end_row() 
                          
        self.doc.end_table()

                    
 
                    
       

#------------------------------------------------------------------------
#
# PeopleCitationsEventRoleRelationParXLSOptions
#
#------------------------------------------------------------------------
class PeopleCitationsEventRoleRelationParXLSOptions(MenuReportOptions):
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
#p        from Filters import CustomFilters, GenericFilter
        from gramps.gen.filters import CustomFilters, GenericFilter

        opt = FilterOption(_("Select using filter"), 0)
        opt.set_help(_("Select places using a filter"))
        filter_list = []
        filter_list.append(GenericFilter())
        filter_list.extend(CustomFilters.get_filters('Source'))
        opt.set_filters(filter_list)
        menu.add_option(category_name, "filter", opt)
        
        showinlaw = BooleanOption(_("Show inlaw"), True)
        showinlaw.set_help(_("Whether to show inlaw persons"))
        menu.add_option(category_name, "showinlaw", showinlaw)

        showperson = BooleanOption(_("Show persons"), True)
        showperson.set_help(_("Whether to show events and persons mentioned in the note"))
        menu.add_option(category_name, "showperson", showperson)

        incphotos = BooleanOption(_("Include Photos"), True)
        incphotos.set_help(_("Whether to show photos mentioned in the citation"))
        menu.add_option(category_name, "incphotos", incphotos)
                
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
        self.__event_table_style()
        self.__stat_table_style()
        self.__stat_right_style()
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

    def __stat_right_style(self):
        """
        Define the style used for the stat table right
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_RIGHT)       
        para.set_description(_('The style used for the stat table right.'))
        self.default_style.add_paragraph_style("SRC-StatCell", para)

#    def __personevent_table_style(self):
        """
        Define the style used for personevent table
        """
        table = TableStyle()
        table.set_width(100)
        table.set_columns(7)
        table.set_column_width(0, 5)
        table.set_column_width(1, 35)
        table.set_column_width(2, 10)
        table.set_column_width(3, 15)
        table.set_column_width(4, 15)
        table.set_column_width(5, 15)
        table.set_column_width(6, 30)
        
        self.default_style.add_table_style("SRC-PersonEventTable", table)

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
        
        

      