# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2002 Bruce J. DeGrasse
# Copyright (C) 2000-2007 Donald N. Allingham
# Copyright (C) 2007-2009 Brian G. Matherly
# Copyright (C) 2007      Robert Cawley  <rjc@cawley.id.au>
# Copyright (C) 2008-2009 James Friedmann <jfriedmannj@gmail.com>
# Copyright (C) 2009      Benny Malengier <benny.malengier@gramps-project.org>
# Copyright (C) 2010      Jakim Friant
# Copyright (C) 2010      Vlada Perić <vlada.peric@gmail.com>
# Copyright (C) 2011      Matt Keenan <matt.keenan@gmail.com>
# Copyright (C) 2011      Tim G L Lyons
# Copyright (C) 2013-2014 Paul Franklin
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

"""Reports/Text Reports/Detailed Descendant Report"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
from functools import partial

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.errors import ReportError
from gramps.gen.lib import FamilyRelType, Person, NoteType
from gramps.gen.plug.menu import (BooleanOption, NumberOption, PersonOption, 
                                  EnumeratedListOption)
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, 
                                    FONT_SANS_SERIF, FONT_SERIF, 
                                    INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from gramps.gen.plug.report import Report, Bibliography
from gramps.gen.plug.report import endnotes
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.plugins.lib.libnarrate import Narrator
from gramps.gen.display.place import displayer as place_displayer

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
EMPTY_ENTRY = "_____________"
HENRY = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetDescendantReport(Report):

    def __init__(self, database, options, user):
        """
        Create the DetDescendantReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User() instance

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen           - Maximum number of generations to include.
        pagebgg       - Whether to include page breaks between generations.
        pageben       - Whether to include page break before End Notes.
        fulldates     - Whether to use full dates instead of just year.
        listc         - Whether to list children.
        incnotes      - Whether to include notes.
        usecall       - Whether to use the call name as the first name.
        repplace      - Whether to replace missing Places with ___________.
        repdate       - Whether to replace missing Dates with ___________.
        computeage    - Whether to compute age.
        omitda        - Whether to omit duplicate ancestors
                            (e.g. when distant cousins marry).
        verbose       - Whether to use complete sentences.
        numbering     - The descendancy numbering system to be utilized.
        desref        - Whether to add descendant references in child list.
        incphotos     - Whether to include images.
        incnames      - Whether to include other names.
        incevents     - Whether to include events.
        incaddresses  - Whether to include addresses.
        incsrcnotes   - Whether to include source notes in the Endnotes
                            section. Only works if Include sources is selected.
        incmates      - Whether to include information about spouses
        incattrs      - Whether to include attributes
        incpaths      - Whether to include the path of descendancy 
                            from the start-person to each descendant.
        incssign      - Whether to include a sign ('+') before the
                            descendant number in the child-list
                            to indicate a child has succession.
        pid           - The Gramps ID of the center person for the report.
        name_format   - Preferred format to display names
        incmateref    - Whether to print mate information or reference
        incl_private  - Whether to include private data
        """
        Report.__init__(self, database, options, user)

        self.map = {}
        self._user = user

        menu = options.menu
        get_option_by_name = menu.get_option_by_name
        get_value = lambda name: get_option_by_name(name).get_value()

        stdoptions.run_private_data_option(self, menu)
        self.db = self.database

        self.max_generations = get_value('gen')
        self.pgbrk         = get_value('pagebbg')
        self.pgbrkenotes   = get_value('pageben')
        self.fulldate      = get_value('fulldates')
        use_fulldate     = self.fulldate
        self.listchildren  = get_value('listc')
        self.inc_notes     = get_value('incnotes')
        use_call           = get_value('usecall')
        blankplace         = get_value('repplace')
        blankdate          = get_value('repdate')
        self.calcageflag   = get_value('computeage')
        self.dubperson     = get_value('omitda')
        self.verbose       = get_value('verbose')
        self.numbering     = get_value('numbering')
        self.childref      = get_value('desref')
        self.addimages     = get_value('incphotos')
        self.inc_names     = get_value('incnames')
        self.inc_events    = get_value('incevents')
        self.inc_addr      = get_value('incaddresses')
        self.inc_sources   = get_value('incsources')
        self.inc_srcnotes  = get_value('incsrcnotes')
        self.inc_mates     = get_value('incmates')
        self.inc_attrs     = get_value('incattrs')
        self.inc_paths     = get_value('incpaths')
        self.inc_ssign     = get_value('incssign')
        self.inc_materef   = get_value('incmateref')
        pid                = get_value('pid')
        self.center_person = self.db.get_person_from_gramps_id(pid)
        if (self.center_person == None) :
            raise ReportError(_("Person %s is not in the Database") % pid )

        self.gen_handles = {}
        self.prev_gen_handles = {}
        self.gen_keys = []
        self.dnumber = {}
        self.dmates = {}

        if blankdate:
            empty_date = EMPTY_ENTRY
        else:
            empty_date = ""

        if blankplace:
            empty_place = EMPTY_ENTRY
        else:
            empty_place = ""

        self._locale = self.set_locale(get_value('trans'))

        stdoptions.run_name_format_option(self, menu)

        self.__narrator = Narrator(self.db, self.verbose,
                                   use_call, use_fulldate, 
                                   empty_date, empty_place,
                                   nlocale=self._locale,
                                   get_endnote_numbers=self.endnotes)

        self.bibli = Bibliography(Bibliography.MODE_DATE|Bibliography.MODE_PAGE)

    def apply_henry_filter(self,person_handle, index, pid, cur_gen=1):
        if (not person_handle) or (cur_gen > self.max_generations):
            return
        self.dnumber[person_handle] = pid
        self.map[index] = person_handle

        if len(self.gen_keys) < cur_gen:
            self.gen_keys.append([index])
        else: 
            self.gen_keys[cur_gen-1].append(index)

        person = self.db.get_person_from_handle(person_handle)
        index = 0
        for family_handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                ix = max(self.map)
                self.apply_henry_filter(child_ref.ref, ix+1,
                                  pid+HENRY[index], cur_gen+1)
                index += 1

    # Filter for d'Aboville numbering
    def apply_daboville_filter(self,person_handle, index, pid, cur_gen=1):
        if (not person_handle) or (cur_gen > self.max_generations):
            return
        self.dnumber[person_handle] = pid
        self.map[index] = person_handle

        if len(self.gen_keys) < cur_gen:
            self.gen_keys.append([index])
        else: 
            self.gen_keys[cur_gen-1].append(index)

        person = self.db.get_person_from_handle(person_handle)
        index = 1
        for family_handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                ix = max(self.map)
                self.apply_daboville_filter(child_ref.ref, ix+1,
                                            pid+"."+str(index), cur_gen+1)
                index += 1

    # Filter for Record-style (Modified Register) numbering
    def apply_mod_reg_filter_aux(self, person_handle, index, cur_gen=1):
        if (not person_handle) or (cur_gen > self.max_generations):
            return
        self.map[index] = person_handle
                
        if len(self.gen_keys) < cur_gen:
            self.gen_keys.append([index])
        else: 
            self.gen_keys[cur_gen-1].append(index)

        person = self.db.get_person_from_handle(person_handle)

        for family_handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                ix = max(self.map)
                self.apply_mod_reg_filter_aux(child_ref.ref, ix+1, cur_gen+1)

    def apply_mod_reg_filter(self, person_handle):
        self.apply_mod_reg_filter_aux(person_handle, 1, 1)
        mod_reg_number = 1
        for generation in range(len(self.gen_keys)):
            for key in self.gen_keys[generation]:
                person_handle = self.map[key]
                if person_handle not in self.dnumber:
                    self.dnumber[person_handle] = mod_reg_number
                    mod_reg_number += 1

    def write_report(self):
        """
        This function is called by the report system and writes the report.
        """
        if self.numbering == "Henry":
            self.apply_henry_filter(self.center_person.get_handle(), 1, "1")
        elif self.numbering == "d'Aboville":
            self.apply_daboville_filter(self.center_person.get_handle(), 1, "1")
        elif self.numbering == "Record (Modified Register)":
            self.apply_mod_reg_filter(self.center_person.get_handle())
        else:
            raise AttributeError("no such numbering: '%s'" % self.numbering)

        name = self._name_display.display_name(
                                      self.center_person.get_primary_name())
        if not name:
            name = self._("Unknown")

        self.doc.start_paragraph("DDR-Title")

        # feature request 2356: avoid genitive form
        title = self._("Descendant Report for %(person_name)s") % {
                           'person_name' : name }
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        generation = 0

        self.numbers_printed = list()
        for generation in range(len(self.gen_keys)):
            if self.pgbrk and generation > 0:
                self.doc.page_break()
            self.doc.start_paragraph("DDR-Generation")
            text = self._("Generation %d") % (generation+1)
            mark = IndexMark(text, INDEX_TYPE_TOC, 2)
            self.doc.write_text(text, mark)
            self.doc.end_paragraph()
            if self.childref:
                self.prev_gen_handles = self.gen_handles.copy()
                self.gen_handles.clear()

            for key in self.gen_keys[generation]:
                person_handle = self.map[key]
                self.gen_handles[person_handle] = key
                self.write_person(key)

        if self.inc_sources:
            if self.pgbrkenotes:
                self.doc.page_break()
            # it ignores language set for Note type (use locale)
            endnotes.write_endnotes(self.bibli, self.db, self.doc,
                                    printnotes=self.inc_srcnotes,
                                    elocale=self._locale)

    def write_path(self, person):
        path = []
        while True:
            #person changes in the loop
            family_handle = person.get_main_parents_family_handle()
            if family_handle:
                family = self.db.get_family_from_handle(family_handle)
                mother_handle = family.get_mother_handle()
                father_handle = family.get_father_handle()
                if mother_handle and mother_handle in self.dnumber:
                    person = self.db.get_person_from_handle(mother_handle)
                    person_name = self._name_display.display_name(
                                                person.get_primary_name())
                    path.append(person_name)
                elif father_handle and father_handle in self.dnumber:
                    person = self.db.get_person_from_handle(father_handle)
                    person_name = self._name_display.display_name(
                                                person.get_primary_name())
                    path.append(person_name)
                else:
                    break
            else:
                break

        index = len(path)

        if index:
            self.doc.write_text("(")

        for name in path:
            if index == 1:
                self.doc.write_text(name + "-" + str(index) + ") ")
            else:
                # translators: needed for Arabic, ignore otherwise
                self.doc.write_text(name + "-" + str(index) + self._("; "))
            index -= 1

    def write_person(self, key):
        """Output birth, death, parentage, marriage and notes information """

        person_handle = self.map[key]
        person = self.db.get_person_from_handle(person_handle)

        val = self.dnumber[person_handle]

        if val in self.numbers_printed:
            return
        else:
            self.numbers_printed.append(val)

        self.doc.start_paragraph("DDR-First-Entry","%s." % val)

        name = self._name_display.display(person)
        if not name:
            name = self._("Unknown")
        mark = ReportUtils.get_person_mark(self.db, person)

        self.doc.start_bold()
        self.doc.write_text(name, mark)
        if name[-1:] == '.':
            self.doc.write_text_citation("%s " % self.endnotes(person))
        elif name:
            self.doc.write_text_citation("%s. " % self.endnotes(person))
        self.doc.end_bold()

        if self.inc_paths:
            self.write_path(person)
        
        if self.dubperson:
            # Check for duplicate record (result of distant cousins marrying)
            for dkey in sorted(self.map):
                if dkey >= key: 
                    break
                if self.map[key] == self.map[dkey]:
                    self.doc.write_text(self._(
                        "%(name)s is the same person as [%(id_str)s].") % {
                            'name' :'',
                            'id_str': self.dnumber[self.map[dkey]],
                            }
                        )
                    self.doc.end_paragraph()
                    return

        self.doc.end_paragraph()
       
        self.write_person_info(person)

        if (self.inc_mates or self.listchildren or self.inc_notes or
            self.inc_events or self.inc_attrs):
            for family_handle in person.get_family_handle_list():
                family = self.db.get_family_from_handle(family_handle)
                if self.inc_mates:
                    self.__write_mate(person, family)
                if self.listchildren:
                    self.__write_children(family)
                if self.inc_notes:
                    self.__write_family_notes(family)
                first = True
                if self.inc_events:
                    first = self.__write_family_events(family)
                if self.inc_attrs:
                    self.__write_family_attrs(family, first)

    def write_event(self, event_ref):
        text = ""
        event = self.db.get_event_from_handle(event_ref.ref)

        if self.fulldate:
            date = self._get_date(event.get_date_object())
        else:
            date = event.get_date_object().get_year()

        place = place_displayer.display_event(self.db, event)

        self.doc.start_paragraph('DDR-MoreDetails')
        event_name = self._get_type(event.get_type())
        if date and place:
            text +=  self._('%(date)s, %(place)s') % { 
                       'date' : date, 'place' : place }
        elif date:
            text += self._('%(date)s') % {'date' : date}
        elif place:
            text += self._('%(place)s') % { 'place' : place }

        if event.get_description():
            if text:
                text += ". "
            text += event.get_description()
            
        text += self.endnotes(event)
        
        if text:
            text += ". "
            
        text = self._('%(event_name)s: %(event_text)s') % {
                             'event_name' : self._(event_name),
                             'event_text' : text }
        
        self.doc.write_text_citation(text)
        
        if self.inc_attrs:
            text = ""
            attr_list = event.get_attribute_list()
            attr_list.extend(event_ref.get_attribute_list())
            for attr in attr_list:
                if text:
                    # translators: needed for Arabic, ignore otherwise
                    text += self._("; ")
                attrName = attr.get_type().type2base()
                # translators: needed for French, ignore otherwise
                text += self._("%(type)s: %(value)s%(endnotes)s") % {
                                    'type'     : self._(attrName),
                                    'value'    : attr.get_value(),
                                    'endnotes' : self.endnotes(attr) }
            text = " " + text
            self.doc.write_text_citation(text)

        self.doc.end_paragraph()

        if self.inc_notes:
            # if the event or event reference has a note attached to it,
            # get the text and format it correctly
            notelist = event.get_note_list()
            notelist.extend(event_ref.get_note_list())
            for notehandle in notelist:
                note = self.db.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                        note.get_format(),"DDR-MoreDetails",
                        contains_html= note.get_type() == NoteType.HTML_CODE)

    def __write_parents(self, person):
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.db.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
                mother_name = self._name_display.display_name(
                                                    mother.get_primary_name())
                mother_mark = ReportUtils.get_person_mark(self.db, mother)
            else:
                mother_name = ""
                mother_mark = ""
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
                father_name = self._name_display.display_name(
                                                    father.get_primary_name())
                father_mark = ReportUtils.get_person_mark(self.db, father)
            else:
                father_name = ""
                father_mark = ""
            text = self.__narrator.get_child_string(father_name, mother_name)
            if text:
                self.doc.write_text(text)
                if father_mark:
                    self.doc.write_text("", father_mark)
                if mother_mark:
                    self.doc.write_text("", mother_mark)

    def write_marriage(self, person):
        """ 
        Output marriage sentence.
        """
        is_first = True
        for family_handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(family_handle)
            spouse_handle = ReportUtils.find_spouse(person, family)
            spouse = self.db.get_person_from_handle(spouse_handle)
            
            text = ""
            spouse_mark = ReportUtils.get_person_mark(self.db, spouse)
            
            text = self.__narrator.get_married_string(family,
                                                      is_first,
                                                      self._name_display)
            
            if text:
                self.doc.write_text_citation(text, spouse_mark)
                is_first = False
                
    def __write_mate(self, person, family):
        """
        Write information about the person's spouse/mate.
        """
        if person.get_gender() == Person.MALE:
            mate_handle = family.get_mother_handle()
        else:
            mate_handle = family.get_father_handle()
            
        if mate_handle:
            mate = self.db.get_person_from_handle(mate_handle)

            self.doc.start_paragraph("DDR-MoreHeader")
            name = self._name_display.display(mate)
            if not name:
                name = self._("Unknown")
            mark = ReportUtils.get_person_mark(self.db, mate)
            if family.get_relationship() == FamilyRelType.MARRIED:
                self.doc.write_text(self._("Spouse: %s") % name, mark)
            else:
                self.doc.write_text(self._("Relationship with: %s")
                                               % name, mark)
            if name[-1:] != '.':
                self.doc.write_text(".")
            self.doc.write_text_citation(self.endnotes(mate))
            self.doc.end_paragraph()

            if not self.inc_materef:
                # Don't want to just print reference
                self.write_person_info(mate)
            else:
                # Check to see if we've married a cousin
                if mate_handle in self.dnumber:
                    self.doc.start_paragraph('DDR-MoreDetails')
                    self.doc.write_text_citation(
                        self._("Ref: %(number)s. %(name)s") %
                                    {'number': self.dnumber[mate_handle],
                                     'name': name})
                    self.doc.end_paragraph()
                else:
                    self.dmates[mate_handle] = person.get_handle()
                    self.write_person_info(mate)

    def __get_mate_names(self, family):
        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.db.get_person_from_handle(mother_handle)
            mother_name = self._name_display.display(mother)
            if not mother_name:
                mother_name = self._("Unknown")
        else:
            mother_name = self._("Unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.db.get_person_from_handle(father_handle)
            father_name = self._name_display.display(father)
            if not father_name:
                father_name = self._("Unknown")
        else:
            father_name = self._("Unknown")

        return mother_name, father_name

    def __write_children(self, family):
        """ 
        List the children for the given family.
        """
        if not family.get_child_ref_list():
            return

        mother_name, father_name = self.__get_mate_names(family)

        self.doc.start_paragraph("DDR-ChildTitle")
        self.doc.write_text(
            self._("Children of %(mother_name)s and %(father_name)s") % 
                            {'father_name': father_name,
                             'mother_name': mother_name } )
        self.doc.end_paragraph()

        cnt = 1
        for child_ref in family.get_child_ref_list():
            child_handle = child_ref.ref
            child = self.db.get_person_from_handle(child_handle)
            child_name = self._name_display.display(child)
            if not child_name:
                child_name = self._("Unknown")
            child_mark = ReportUtils.get_person_mark(self.db, child)

            if self.childref and self.prev_gen_handles.get(child_handle):
                value = str(self.prev_gen_handles.get(child_handle))
                child_name += " [%s]" % value

            if self.inc_ssign:
                prefix = " "
                for family_handle in child.get_family_handle_list():
                    family = self.db.get_family_from_handle(family_handle)
                    if family.get_child_ref_list():
                        prefix = "+ "
                        break
            else:
                prefix = ""

            if child_handle in self.dnumber:
                self.doc.start_paragraph("DDR-ChildList",
                        prefix
                        + str(self.dnumber[child_handle])
                        + " "
                        + ReportUtils.roman(cnt).lower()
                        + ".")
            else:
                self.doc.start_paragraph("DDR-ChildList",
                              prefix + ReportUtils.roman(cnt).lower() + ".")
            cnt += 1

            self.doc.write_text("%s. " % child_name, child_mark)
            self.__narrator.set_subject(child)
            self.doc.write_text_citation(
                                self.__narrator.get_born_string() or
                                self.__narrator.get_christened_string() or
                                self.__narrator.get_baptised_string())
            self.doc.write_text_citation(
                                self.__narrator.get_died_string() or
                                self.__narrator.get_buried_string())
            self.doc.end_paragraph()

    def __write_family_notes(self, family):
        """ 
        Write the notes for the given family.
        """
        notelist = family.get_note_list()
        if len(notelist) > 0:
            mother_name, father_name = self.__get_mate_names(family)

            self.doc.start_paragraph("DDR-NoteHeader")
            self.doc.write_text(
                self._('Notes for %(mother_name)s and %(father_name)s:') % { 
                            'mother_name' : mother_name,
                            'father_name' : father_name })
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.db.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                                           note.get_format(),"DDR-Entry")

    def __write_family_events(self, family):
        """ 
        List the events for the given family.
        """
        if not family.get_event_ref_list():
            return

        mother_name, father_name = self.__get_mate_names(family)

        first = True
        for event_ref in family.get_event_ref_list():
            if first:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(
                    self._('More about %(mother_name)s and %(father_name)s:')
                                % {'mother_name' : mother_name,
                                   'father_name' : father_name })
                self.doc.end_paragraph()
                first = False
            self.write_event(event_ref)
        return first

    def __write_family_attrs(self, family, first):
        """ 
        List the attributes for the given family.
        """
        attrs = family.get_attribute_list()

        if first and attrs:
            mother_name, father_name = self.__get_mate_names(family)

            self.doc.start_paragraph('DDR-MoreHeader')
            self.doc.write_text(
                self._('More about %(mother_name)s and %(father_name)s:')
                            % {'mother_name' : mother_name,
                               'father_name' : father_name })
            self.doc.end_paragraph()

        for attr in attrs:
            self.doc.start_paragraph('DDR-MoreDetails')
            attrName = self._get_type(attr.get_type())
            text = self._("%(type)s: %(value)s%(endnotes)s") % {
                                'type'     : self._(attrName),
                                'value'    : attr.get_value(),
                                'endnotes' : self.endnotes(attr) }
            self.doc.write_text_citation( text )
            self.doc.end_paragraph()

            if self.inc_notes:
                # if the attr or attr reference has a note attached to it,
                # get the text and format it correctly
                notelist = attr.get_note_list()
                for notehandle in notelist:
                    note = self.db.get_note_from_handle(notehandle)
                    self.doc.write_styled_note(note.get_styledtext(), 
                                               note.get_format(),
                                               "DDR-MoreDetails")


    def write_person_info(self, person):
        name = self._name_display.display(person)
        if not name:
            name = self._("Unknown")
        self.__narrator.set_subject(person)
        
        plist = person.get_media_list()
        if self.addimages and len(plist) > 0:
            photo = plist[0]
            ReportUtils.insert_image(self.db, self.doc, photo, self._user)
        
        self.doc.start_paragraph("DDR-Entry")
        
        if not self.verbose:
            self.__write_parents(person)

        text = self.__narrator.get_born_string()
        if text:
            self.doc.write_text_citation(text)

        text = self.__narrator.get_baptised_string()
        if text:
            self.doc.write_text_citation(text)
            
        text = self.__narrator.get_christened_string()
        if text:
            self.doc.write_text_citation(text)
    
        text = self.__narrator.get_died_string(self.calcageflag)
        if text:
            self.doc.write_text_citation(text)

        text = self.__narrator.get_buried_string()
        if text:
            self.doc.write_text_citation(text)

        if self.verbose:
            self.__write_parents(person)
        self.write_marriage(person)
        self.doc.end_paragraph()

        notelist = person.get_note_list()
        if len(notelist) > 0 and self.inc_notes:
            self.doc.start_paragraph("DDR-NoteHeader")
            # feature request 2356: avoid genitive form
            self.doc.write_text(self._("Notes for %s") % name)
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.db.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                        note.get_format(),"DDR-Entry",
                        contains_html= note.get_type() == NoteType.HTML_CODE)

        first = True
        if self.inc_names:
            for alt_name in person.get_alternate_names():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:')
                                                    % {'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                atype = self._get_type(alt_name.get_type())
                aname = alt_name.get_regular_name()
                self.doc.write_text_citation(
                    self._('%(name_kind)s: %(name)s%(endnotes)s')
                                % {'name_kind' : self._(atype),
                                   'name' : aname,
                                   'endnotes' : self.endnotes(alt_name),
                                  })
                self.doc.end_paragraph()

        if self.inc_events:
            for event_ref in person.get_primary_event_ref_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:')
                                                    % {'person_name' : name })
                    self.doc.end_paragraph()
                    first = 0

                self.write_event(event_ref)
                
        if self.inc_addr:
            for addr in person.get_address_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:')
                                                    % {'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                
                text = ReportUtils.get_address_str(addr)

                if self.fulldate:
                    date = self._get_date(addr.get_date_object())
                else:
                    date = addr.get_date_object().get_year()

                self.doc.write_text(self._('Address: '))
                if date:
                    # translators: needed for Arabic, ignore otherwise
                    self.doc.write_text(self._('%s, ') % date )
                self.doc.write_text( text )
                self.doc.write_text_citation( self.endnotes(addr) )
                self.doc.end_paragraph()
                
        if self.inc_attrs:
            attrs = person.get_attribute_list()
            if first and attrs:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(self._('More about %(person_name)s:') % { 
                    'person_name' : name })
                self.doc.end_paragraph()
                first = False

            for attr in attrs:
                self.doc.start_paragraph('DDR-MoreDetails')
                attrName = attr.get_type().type2base()
                # translators: needed for French, ignore otherwise
                text = self._("%(type)s: %(value)s%(endnotes)s") % {
                                    'type'     : self._(attrName),
                                    'value'    : attr.get_value(),
                                    'endnotes' : self.endnotes(attr) }
                self.doc.write_text_citation( text )
                self.doc.end_paragraph()

    def endnotes(self, obj):
        if not obj or not self.inc_sources:
            return ""
        
        txt = endnotes.cite_source(self.bibli, self.db, obj, self._locale)
        if txt:
            txt = '<super>' + txt + '</super>'
        return txt

#------------------------------------------------------------------------
#
# DetDescendantOptions
#
#------------------------------------------------------------------------
class DetDescendantOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the detailed descendant report.
        """

        # Report Options
        category = _("Report Options")
        add_option = partial(menu.add_option, category)
        
        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the report"))
        add_option("pid", pid)
        
        stdoptions.add_name_format_option(menu, category)

        stdoptions.add_private_data_option(menu, category)

        numbering = EnumeratedListOption(_("Numbering system"), "Henry")
        numbering.set_items([
                ("Henry",      _("Henry numbering")), 
                ("d'Aboville", _("d'Aboville numbering")), 
                ("Record (Modified Register)", 
                               _("Record (Modified Register) numbering"))])
        numbering.set_help(_("The numbering system to be used"))
        add_option("numbering", numbering)
        
        generations = NumberOption(_("Generations"), 10, 1, 100)
        generations.set_help(
            _("The number of generations to include in the report")
            )
        add_option("gen", generations)
        
        pagebbg = BooleanOption(_("Page break between generations"), False)
        pagebbg.set_help(
                     _("Whether to start a new page after each generation."))
        add_option("pagebbg", pagebbg)

        pageben = BooleanOption(_("Page break before end notes"),False)
        pageben.set_help(
                     _("Whether to start a new page before the end notes."))
        add_option("pageben", pageben)

        stdoptions.add_localization_option(menu, category)

        # Content
        
        add_option = partial(menu.add_option, _("Content"))

        usecall = BooleanOption(_("Use callname for common name"), False)
        usecall.set_help(_("Whether to use the call name as the first name."))
        add_option("usecall", usecall)
        
        fulldates = BooleanOption(_("Use full dates instead of only the year"),
                                  True)
        fulldates.set_help(_("Whether to use full dates instead of just year."))
        add_option("fulldates", fulldates)
        
        listc = BooleanOption(_("List children"), True)
        listc.set_help(_("Whether to list children."))
        add_option("listc", listc)
        
        computeage = BooleanOption(_("Compute death age"),True)
        computeage.set_help(_("Whether to compute a person's age at death."))
        add_option("computeage", computeage)
        
        omitda = BooleanOption(_("Omit duplicate ancestors"), True)
        omitda.set_help(_("Whether to omit duplicate ancestors."))
        add_option("omitda", omitda)
        
        verbose = BooleanOption(_("Use complete sentences"), True)
        verbose.set_help(
                 _("Whether to use complete sentences or succinct language."))
        add_option("verbose", verbose)

        desref = BooleanOption(_("Add descendant reference in child list"),
                               True)
        desref.set_help(
                    _("Whether to add descendant references in child list."))
        add_option("desref", desref)

        category_name = _("Include")
        add_option = partial(menu.add_option, _("Include"))
        
        incnotes = BooleanOption(_("Include notes"), True)
        incnotes.set_help(_("Whether to include notes."))
        add_option("incnotes", incnotes)

        incattrs = BooleanOption(_("Include attributes"), False)
        incattrs.set_help(_("Whether to include attributes."))
        add_option("incattrs", incattrs)
        
        incphotos = BooleanOption(_("Include Photo/Images from Gallery"), False)
        incphotos.set_help(_("Whether to include images."))
        add_option("incphotos", incphotos)

        incnames = BooleanOption(_("Include alternative names"), False)
        incnames.set_help(_("Whether to include other names."))
        add_option("incnames", incnames)

        incevents = BooleanOption(_("Include events"), False)
        incevents.set_help(_("Whether to include events."))
        add_option("incevents", incevents)

        incaddresses = BooleanOption(_("Include addresses"), False)
        incaddresses.set_help(_("Whether to include addresses."))
        add_option("incaddresses", incaddresses)

        incsources = BooleanOption(_("Include sources"), False)
        incsources.set_help(_("Whether to include source references."))
        add_option("incsources", incsources)
        
        incsrcnotes = BooleanOption(_("Include sources notes"), False)
        incsrcnotes.set_help(_("Whether to include source notes in the "
            "Endnotes section. Only works if Include sources is selected."))
        add_option("incsrcnotes", incsrcnotes)

        incmates = BooleanOption(_("Include spouses"), False)
        incmates.set_help(_("Whether to include detailed spouse information."))
        add_option("incmates", incmates)

        incmateref = BooleanOption(_("Include spouse reference"), False)
        incmateref.set_help(_("Whether to include reference to spouse."))
        add_option("incmateref", incmateref)

        incssign = BooleanOption(_("Include sign of succession ('+')"
                                   " in child-list"), True)
        incssign.set_help(_("Whether to include a sign ('+') before the"
                            " descendant number in the child-list to indicate"
                            " a child has succession."))
        add_option("incssign", incssign)

        incpaths = BooleanOption(_("Include path to start-person"), False)
        incpaths.set_help(_("Whether to include the path of descendancy "
                            "from the start-person to each descendant."))
        add_option("incpaths", incpaths)

        # Missing information
        
        add_option = partial(menu.add_option, _("Missing information"))      

        repplace = BooleanOption(_("Replace missing places with ______"), False)
        repplace.set_help(_("Whether to replace missing Places with blanks."))
        add_option("repplace", repplace)

        repdate = BooleanOption(_("Replace missing dates with ______"), False)
        repdate.set_help(_("Whether to replace missing Dates with blanks."))
        add_option("repdate", repdate)

    def make_default_style(self, default_style):
        """Make the default output style for the Detailed Ancestral Report"""
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_('The style used for the title of the page.'))
        default_style.add_paragraph_style("DDR-Title", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=14, italic=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the generation header.'))
        default_style.add_paragraph_style("DDR-Generation", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_left_margin(1.5)   # in centimeters
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the children list title.'))
        default_style.add_paragraph_style("DDR-ChildTitle", para)

        font = FontStyle()
        font.set(size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-0.75, lmargin=2.25)
        para.set_top_margin(0.125)
        para.set_bottom_margin(0.125)
        para.set_description(_('The style used for the children list.'))
        default_style.add_paragraph_style("DDR-ChildList", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        default_style.add_paragraph_style("DDR-NoteHeader", para)

        para = ParagraphStyle()
        para.set(lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("DDR-Entry", para)

        para = ParagraphStyle()
        para.set(first_indent=-1.5, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for the first personal entry.'))
        default_style.add_paragraph_style("DDR-First-Entry", para)

        font = FontStyle()
        font.set(size=10, face=FONT_SANS_SERIF, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the More About header and '
            'for headers of mates.'))
        default_style.add_paragraph_style("DDR-MoreHeader", para)

        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for additional detail data.'))
        default_style.add_paragraph_style("DDR-MoreDetails", para)

        endnotes.add_endnote_styles(default_style)
