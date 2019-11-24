#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008,2011  Gary Burton
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Heinz Brinker
# Copyright (C) 2013-2014  Paul Franklin
# Copyright (C) 2015-2018  Hans Ulrich Frink
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
# by use of code from gramps project
# 
#

"""PlaceFamily Report"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from collections import defaultdict
from collections import OrderedDict

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
import locale
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.plug.menu import (FilterOption, PlaceListOption,
                                  BooleanOption)
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle,
                                    FONT_SANS_SERIF, FONT_SERIF, 
                                    INDEX_TYPE_TOC, INDEX_TYPE_ALP, PARA_ALIGN_CENTER)
from gramps.gen.proxy import PrivateProxyDb
from gramps.gen.sort import Sort
from gramps.gen.display.place import displayer as _pd
from gramps.gen.lib import EventRoleType, EventType

class PlaceFamilyReport(Report):
    """
    Place Report class
    """
    def __init__(self, database, options, user):
        """
        Create the PlaceFamilyReport object produces the PlaceFamily report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - instance of a gen.user.User class

        This report needs the following parameters (class variables)
        that come in the options class.
        
        places          - List of places to report on.
        place_fmt       - Place Fromat used
        incpriv         - Whether to include private data
        showgodparents  - Whether to include and show godparents

        """

        Report.__init__(self, database, options, user)

        self._user = user
        menu = options.menu
        places = menu.get_option_by_name('places').get_value()
        self.place_fmt = menu.get_option_by_name("place_format").get_value()
        print("self.place_fmt                     ", self.place_fmt)
        self.incpriv = menu.get_option_by_name('incpriv').get_value()
        self.showgodparents = menu.get_option_by_name('showgodparents').get_value()

        self.set_locale(menu.get_option_by_name('trans').get_value())

        name_format = menu.get_option_by_name("name_format").get_value()
        if name_format != 0:
            self._name_display.set_default_format(name_format)
        self._nd = self._name_display

        if self.incpriv:
            self.db = database
        else:
            self.db = PrivateProxyDb(database)

        filter_option = menu.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
        self.sort = Sort(self.db)

        if self.filter.get_name() != '':
            # Use the selected filter to provide a list of place handles
            plist = self.db.iter_place_handles()
            self.place_handles = self.filter.apply(self.db, plist)
        else:
            # Use the place handles selected without a filter
            self.place_handles = self.__get_place_handles(places)

        self.place_handles.sort(key=self.sort.by_place_title_key)

    def write_report(self):
        """
        The routine that actually creates the report.
        At this point, the document is opened and ready for writing.
        """

        # Write the title line. Set in INDEX marker so that this section will be
        # identified as a major category if this is included in a Book report.

        title = self._("PlaceFamily Report")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)        
        self.doc.start_paragraph("PLC-ReportTitle")
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()
        
        self.__write_all_places()
        self.__write_referenced_families()

    def __write_all_places(self):
        """
        This procedure writes out each of the selected places.
        """
        place_nbr = 1
        subtitle = self._("Places")
        mark = IndexMark(subtitle, INDEX_TYPE_TOC, 2)        
        self.doc.start_paragraph("PLC-ReportSubtitle")
        self.doc.write_text(subtitle, mark)
        self.doc.end_paragraph()

        self.doc.start_paragraph("PLC-Section")
        self.doc.write_text("Enthält alle Familien mit Hochzeitsereignis in diesen Orten")
        self.doc.end_paragraph()
        
        pl_list = []
        pl_list = [_pd.display(self.db, self.db.get_place_from_handle(handle)) for handle in self.place_handles]
        for p in pl_list:
            self.doc.start_paragraph("PLC-Section")
            self.doc.write_text("     %s  " % place_nbr)
            self.doc.write_text(p)
            self.doc.end_paragraph()
            place_nbr += 1

        subtitle = self._("Families")
        mark = IndexMark(subtitle, INDEX_TYPE_TOC, 2)        
        self.doc.start_paragraph("PLC-ReportSubtitle")
        self.doc.write_text(subtitle, mark)
        self.doc.end_paragraph()


    def __format_date_place(self, eventref):
        estr = " "
        event = self.db.get_event_from_handle(eventref.ref)
        if event:
            #e_date = event.get_date_object()
            e_date = self._get_date(event.get_date_object())
            place_handle = event.get_place_handle()
            if place_handle:
                # feature requests 2356, 1657: avoid genitive form
                place_title = _pd.display_event(self.db, event, fmt=self.place_fmt)
                estr = (_(" %s in %s") % (e_date, place_title))
                #print(estr)
                #print(_(" %s in ") % e_date, place_title)
            else:
                estr = (_(" %s") % e_date)
        else:
            estr = "leer"
        return estr



    def __add_grampsID_to_index(self, list, person):
        """
        This procedure adds the (gramps_id, _nd(Person)) tuple to person_tuple = tuple()
        """
        list.append((self._nd.display_name(person.get_primary_name()), person.get_gramps_id()))


    def __write_referenced_families(self):
        """
        This procedure writes out each of the families related to the place
        """
        i = 0
        iw = 0
        ifam = 0
        marrevt_handle_list = []
        marr = []
        fam_list = []
        fam_index = {}
        person_index = []
        Patenlist = []
        with self._user.progress(_("PlaceFamily Report"), 
                                  _("preparing Dictionaries"), 
                                  len(self.place_handles)) as step:
        
            if self.showgodparents:
                pedic = {}
                pedic = defaultdict(list)
                for pe in self.db.get_person_handles():
                    for eventref in self.db.get_person_from_handle(pe).event_ref_list:
                        if not eventref.get_role().is_primary():
                            pedic[eventref.ref].append((eventref.get_role(), pe))

            for handle in self.place_handles:        
    # first all events
                event_handles = [event_handle for (object_type, event_handle) in
                                 self.db.find_backlink_handles(handle, ['Event'])]
                event_handles.sort(key=self.sort.by_date_key)
            # increment progress bar
                step()
    
    # only marriage            
                for evt_handle in event_handles:
                    if self.db.get_event_from_handle(evt_handle).get_type().is_marriage():
                        marrevt_handle_list.append(evt_handle)
    #            print(len(marrevt_handle_list))
    # no dups            
            marr = list(OrderedDict.fromkeys(marrevt_handle_list))
    #        print(len(marr))
            mi = 0   

            for evt_handle in marr:
                event = self.db.get_event_from_handle(evt_handle)
                date = self._get_date(event.get_date_object())
                date_sort = event.get_date_object().get_sort_value()
                descr = event.get_description()
                ref_handles = [x for x in
                                self.db.find_backlink_handles(evt_handle)]
    #            print(mi, evt_handle)
                mi += 1
                for (ref_type, ref_handle) in ref_handles:
                    if ref_type == 'Person':
                        continue
                    else:
                        family = self.db.get_family_from_handle(ref_handle)
                        ifam += 1
                        father_handle = family.get_father_handle()
        # now from the families only fathers
                        if father_handle:
                            fp = self.db.get_person_from_handle(father_handle)
                            father_name = \
                                self._nd.display_name(fp.get_primary_name()).lower()
                        else:
                            father_name = _("unknown")
                        place_d = _pd.display_event(self.db, event)                                        
                        event_details = [father_handle, father_name, date, ref_handle, descr, place_d, family, date_sort]
                        fam_list.append(event_details)

            fam_index_keys = fam_index.keys()
            printsurname = "NOW"
            index = 0
            for fn in sorted(fam_list, key=lambda t: (locale.strxfrm(t[1]), t[7])):
                index += 1
                fam_index[fn[6].get_gramps_id()] = index
            for fn in sorted(fam_list, key=lambda t: (locale.strxfrm(t[1]), t[7])):
                if fn[0] is None:
                    surname = _("unknown")
                else:
                    surname = self.db.get_person_from_handle(fn[0]).get_primary_name().get_surname()
                if printsurname == surname:
                    pass
                else:
        #Family Surname
                    printsurname = surname
                    self.doc.start_paragraph("PLC-PlaceTitle")
                    mark = IndexMark( surname, INDEX_TYPE_ALP )
                    
                    self.doc.write_text(surname, mark)
                    self.doc.end_paragraph()                              
                i += 1
    # weddingdetails
                family = fn[6]
                iw += 1
                self.doc.start_paragraph("PLC-Details")
                self.doc.start_bold()
    #            self.doc.write_text("<%s> " % iw)
                self.doc.write_text(" <%s>" % fam_index[fn[6].gramps_id])
    #            self.doc.write_text("Heirat %s " % fn[1])
                self.doc.write_text("%s " % u'\u26AD')
                self.doc.write_text("%s " % fn[2])
                self.doc.end_bold()
    # wedding place
                self.doc.write_text("in %s." % fn[5])
    # FamID            
                self.doc.write_text(" [%s]" % fn[6].gramps_id)        
                self.doc.end_paragraph()

    
    ##################################################
    # fatherdetails
                if fn[6].father_handle:
                    father = self.db.get_person_from_handle(fn[6].father_handle)
                    self.doc.start_paragraph("PLC-PlaceDetails")
    #given Name
                    self.doc.start_bold()
                    mark = ReportUtils.get_person_mark(self.db, father)
                    text = father.get_primary_name().get_first_name()
                    self.doc.write_text(text, mark)
                    self.doc.write_text(" %s" % father.get_primary_name().get_surname())
                    
                    self.doc.end_bold()
                    self.doc.write_text(" [%s] " % father.get_gramps_id())
    #ggf familyID
                    for fam in father.get_family_handle_list():
                        if self.db.get_family_from_handle(fam).gramps_id == fn[6].gramps_id:
                            pass
                        else:
                            self.doc.write_text(" [%s]" % self.db.get_family_from_handle(fam).gramps_id)
                            if self.db.get_family_from_handle(fam).gramps_id in fam_index_keys:
                                self.doc.start_bold()
                                self.doc.write_text(" <%s>" % fam_index[self.db.get_family_from_handle(fam).gramps_id])
                                self.doc.end_bold()
                    self.__add_grampsID_to_index(person_index, father)
        #birth date
                    birth_ref = father.get_birth_ref()
                    if birth_ref:
                        self.doc.write_text(" *")
                        self.doc.write_text(self.__format_date_place(birth_ref))
        #bapt date
                    for eventref in father.event_ref_list:
                        if eventref.role == EventRoleType.PRIMARY:
                            if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BAPTISM:
                                self.doc.write_text(" %s " % u'\u2053')
                                self.doc.write_text(self.__format_date_place(eventref))
        #death date
                    death_ref = father.get_death_ref()
                    if death_ref:
                        self.doc.write_text(" † ")
                        self.doc.write_text(self.__format_date_place(death_ref))
        #burr date
                    for eventref in father.event_ref_list:
                        if eventref.role == EventRoleType.PRIMARY:
                            if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BURIAL:
                                self.doc.write_text("%s " % u'\u26B0')
                                self.doc.write_text(self.__format_date_place(eventref))
                    self.doc.end_paragraph()
    # motherdetails
#                print(fn[6].gramps_id,fn[6])
                print('            handle', fn[6].mother_handle)

                if fn[6].mother_handle:
                    mother = self.db.get_person_from_handle(fn[6].mother_handle)
                    self.doc.start_paragraph("PLC-PlaceDetails")					
        #given Name
                    self.doc.write_text("und ")
                    self.doc.start_bold()
                
                    mark = ReportUtils.get_person_mark(self.db, mother)
                    text = mother.get_primary_name().get_surname()
                    self.doc.write_text(text, mark)
                
                    self.doc.end_bold()
                    self.doc.write_text(" %s " % mother.get_primary_name().get_first_name())
                    self.doc.write_text("[%s] " % mother.get_gramps_id())
        #ggf familyID
                    for fam in mother.get_family_handle_list():
                        if self.db.get_family_from_handle(fam).gramps_id == fn[6].gramps_id:
                            pass
                        else:
                            self.doc.write_text(" [%s]" % self.db.get_family_from_handle(fam).gramps_id)
                            if self.db.get_family_from_handle(fam).gramps_id in fam_index_keys:
                                self.doc.start_bold()
                                self.doc.write_text(" <%s>" % fam_index[self.db.get_family_from_handle(fam).gramps_id])
                                self.doc.end_bold()
                    self.__add_grampsID_to_index(person_index, mother)              

        #birth date
                    birth_ref = mother.get_birth_ref()
                    if birth_ref:
                        self.doc.write_text(" *")
                        self.doc.write_text(self.__format_date_place(birth_ref))
        #bapt date
                    for eventref in mother.event_ref_list:
                        if eventref.role == EventRoleType.PRIMARY:
                            if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BAPTISM:
                                self.doc.write_text(" %s " % u'\u2053')
                                self.doc.write_text(self.__format_date_place(eventref))
        #death date
                    death_ref = mother.get_death_ref()
                    if death_ref:
                        self.doc.write_text(" † ")
                        self.doc.write_text(self.__format_date_place(death_ref))
        #burr date
                    for eventref in mother.event_ref_list:
                        if eventref.role == EventRoleType.PRIMARY:
                            if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BURIAL:
                                self.doc.write_text("%s " % u'\u26B0')
                                self.doc.write_text(self.__format_date_place(eventref))
                    self.doc.end_paragraph()
    # Children
                fc = 0
                for ch in fn[6].get_child_ref_list():
                    self.doc.start_paragraph("PLC-PlaceDetailsChildren")
                    fc += 1
                    child = self.db.get_person_from_handle(ch.ref)
                    if child:
        #lnr
                        self.doc.write_text("     %s " % fc)
        #given Name
                        mark = ReportUtils.get_person_mark(self.db, child)
                        text = child.get_primary_name().get_first_name()
                        self.doc.write_text(text, mark)
                        self.doc.write_text(" [%s] " % child.get_gramps_id())
        #ggf familyID
                        for fam in child.get_family_handle_list():
                            if self.db.get_family_from_handle(fam).gramps_id == fn[6].gramps_id:
                                pass
                            else:
                                self.doc.write_text(" [%s]" % self.db.get_family_from_handle(fam).gramps_id)
                                if self.db.get_family_from_handle(fam).gramps_id in fam_index_keys:
                                    self.doc.start_bold()
                                    self.doc.write_text(" <%s>" % fam_index[self.db.get_family_from_handle(fam).gramps_id])
                                    self.doc.end_bold()
                        self.__add_grampsID_to_index(person_index, child)            
        #birth date
                        birth_ref = child.get_birth_ref()
                        if birth_ref:
                            self.doc.write_text(" * ")                                
                            self.doc.write_text(self.__format_date_place(birth_ref))
        #bapt date
                        for eventref in child.event_ref_list:
                            if eventref.role == EventRoleType.PRIMARY:
                                if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BAPTISM:
                                    self.doc.write_text(" %s " % u'\u2053')
                                    self.doc.write_text(self.__format_date_place(eventref))
        
                                    if self.showgodparents:
                                        Patenlist = []
                                        Patenlist = pedic[eventref.ref]

        #death date
                        death_ref = child.get_death_ref()
                        if death_ref:
                            self.doc.write_text(" † ")
                            self.doc.write_text(self.__format_date_place(death_ref))
        #burr date
                        for eventref in child.event_ref_list:
                            if eventref.role == EventRoleType.PRIMARY:
                                if self.db.get_event_from_handle(eventref.ref).get_type() == EventType.BURIAL:
                                    self.doc.write_text("%s " % u'\u26B0')
                                    self.doc.write_text(self.__format_date_place(eventref))
                        self.doc.end_paragraph()

                        if self.showgodparents:
                            if len(Patenlist) > 0:
                                self.doc.start_paragraph("PLC-Godparents")
                                self.doc.write_text(" Paten: ")
                                for i, (pa_a,pa_b) in enumerate(Patenlist):
                                    self.doc.write_text(" (%s) " % str(i+1))
                                    pate = self.db.get_person_from_handle(pa_b) 
                                    mark = ReportUtils.get_person_mark(self.db, pate)
                                    self.doc.write_text(pate.get_primary_name().get_first_name() + " " + pate.get_primary_name().get_surname() ,mark)
                                self.doc.end_paragraph()
                            Patenlist =[]

        person_index = list(set(person_index))
        for (indname, pi) in sorted(person_index):
            print(indname, pi)
            self.doc.start_paragraph("PLC-Details")
            self.doc.write_text("%s  [%s]" % (indname, pi))
            self.doc.end_paragraph()
        self.doc.start_paragraph("PLC-Details")
        self.doc.write_text("Anzahl: %s" % len(person_index))
        self.doc.end_paragraph()
##########            
            
            
            

    def __get_place_handles(self, places):
        """
        This procedure converts a string of place GIDs to a list of handles
        """
        place_handles = [] 
        for place_gid in places.split():
            place = self.db.get_place_from_gramps_id(place_gid)
            if place is not None:
                place_handles.append(place.get_handle())

        return place_handles
    
#------------------------------------------------------------------------
#
# PlaceFamilyReportOptions
#
#------------------------------------------------------------------------
class PlaceFamilyReportOptions(MenuReportOptions):

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

        stdoptions.add_place_format_option(menu, category_name)

        incpriv = BooleanOption(_("Include private data"), True)
        incpriv.set_help(_("Whether to include private data"))
        menu.add_option(category_name, "incpriv", incpriv)

        showgodparents = BooleanOption(_("show godparents"), True)
        showgodparents.set_help(_("Whether to include and show godparents"))
        menu.add_option(category_name, "showgodparents", showgodparents)

        stdoptions.add_localization_option(menu, category_name)

    def make_default_style(self, default_style):
        """
        Make the default output style for the Place report.
        """
        self.default_style = default_style
        self.__report_title_style()
        self.__report_subtitle_style()
        self.__section_style()
        self.__place_title_style()
        self.__place_details_style()
        self.__place_details_children_style()
        self.__place_details_godparents_style()
        self.__details_style()

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
        
    def __report_subtitle_style(self):
        """
        Define the style used for the report title
        """
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_header_level(2)
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        #para.set_alignment(PARA_ALIGN_LEFT)       
        para.set_description(_('The style used for the title of the report.'))
        self.default_style.add_paragraph_style("PLC-ReportSubtitle", para)        

    def __place_title_style(self):
        """
        Define the style used for the place title
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_header_level(3)
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
        para.set(first_indent=-1.5, lmargin=2.5)
        para.set_description(_('The style used for place details.'))
        self.default_style.add_paragraph_style("PLC-PlaceDetails", para)

    def __place_details_children_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-2.0, lmargin=4.5)
        para.set_description(_('The style used for place details.'))
        self.default_style.add_paragraph_style("PLC-PlaceDetailsChildren", para)
        
    def __place_details_godparents_style(self):
        """
        Define the style used for the place details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10, italic=1, bold=0)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0, lmargin=4.5)
        para.set_description(_('The style used for Godparents details.'))
        self.default_style.add_paragraph_style("PLC-Godparents", para)        

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


    def __details_style(self):
        """
        Define the style used for person and event details
        """
        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_top_margin(0.25)
        para.set_font(font)
        para.set_description(_('The style used for event and person details.'))
        self.default_style.add_paragraph_style("PLC-Details", para)
