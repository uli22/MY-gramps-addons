#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2013-2014  Paul Franklin
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

"""
Reports/Text Reports/Database Summary Report.
"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import posixpath
import csv
import datetime
from collections import defaultdict, namedtuple, Counter

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.lib import Person
from gramps.gen.lib.eventtype import EventType
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import stdoptions
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle,
                                    FONT_SANS_SERIF, INDEX_TYPE_TOC,
                                    PARA_ALIGN_CENTER)
from gramps.gen.utils.file import media_path_full
from gramps.gen.datehandler import get_date

#------------------------------------------------------------------------
#
# MYSummaryReport
#
#------------------------------------------------------------------------
class MYSummaryReport(Report):
    """
    This report produces a summary of the objects in the database.
    """
    def __init__(self, database, options, user):
        """
        Create the SummaryReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User() instance

        incl_private    - Whether to count private data
        """
        Report.__init__(self, database, options, user)

        stdoptions.run_private_data_option(self, options.menu)
        self.__db = self.database
        
        lang = options.menu.get_option_by_name('trans').get_value()
        self.set_locale(lang)

    def write_report(self):
        """
        Overridden function to generate the report.
        """
        self.doc.start_paragraph("SR-Title")
        title = self._("Database Summary Report")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()
		
		
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Date: %s") % f"{datetime.datetime.now(): %d.%m.%Y}")
        self.doc.end_paragraph()
		
        self.summarize_people()
        self.summarize_families()
        self.summarize_media()

    def count_by_quality(self, event):
        """
        count events of a person or family by quality.
        """
        n_missing = 0
        n_exact = 0
        n_estimated = 0
        n_calculated = 0

        if event:
            if not get_date(event):
                n_missing += 1
            elif event.get_date_object().get_quality() == 0:
                n_exact += 1
            elif event.get_date_object().get_quality() == 1:
                n_estimated += 1
            elif event.get_date_object().get_quality() == 2:
                n_calculated += 1
        return [n_exact, n_calculated, n_estimated, n_missing]
		
    def summarize_people(self):
        """
        Write a summary of all the people in the database.
        """

        peDict = defaultdict()

        with_media = 0
        incomp_names = 0
        disconnected = 0
        missing_bday = 0
        males = 0
        females = 0
        unknowns = 0
        namelist = []
        exact_birth = 0
        estimated_birth = 0
        calculated_birth = 0
        missing_birth = 0
        sum_birth = 0

        exact_bapt = 0
        estimated_bapt = 0
        calculated_bapt = 0
        missing_bapt = 0
        sum_bapt = 0
		
        exact_death = 0
        estimated_death = 0
        calculated_death = 0
        missing_death = 0
        sum_birth = 0

        exact_burial = 0
        estimated_burial = 0
        calculated_burial = 0
        missing_burial = 0
        sum_bapt = 0

        mi_bday = 0
        ex_birth = 0
        est_birth = 0
        cal_birth = 0
        su_birth = 0

        ##EventTuple = namedtuple('Eventtuple', ['exact_birth', 'estimated_birth', 'calculated_birth', 'missing_birth',
        ##                       'exact_bapt', 'estimated_bapt', 'calculated_bapt', 'missing_bapt',
		##					   'exact_death', 'estimated_death', 'calculated_death', 'missing_death',
        ##                       'exact_burial', 'estimated_burial', 'calculated_burial', 'missing_burial'])
		
        self.doc.start_paragraph("SR-Heading")
        self.doc.write_text(self._("Individuals"))
        self.doc.end_paragraph()
        
        num_people = 0
        for person in self.__db.iter_people():
            num_people += 1
            evList=[0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]
            
            # Count people with media.
            length = len(person.get_media_list())
            if length > 0:
                with_media += 1
            
            # Count people with incomplete names.
            for name in [person.get_primary_name()] + person.get_alternate_names():
                if name.get_first_name().strip() == "":
                    incomp_names += 1
                else:
                    if name.get_surname_list():
                        for surname in name.get_surname_list():
                            if surname.get_surname().strip() == "":
                                incomp_names += 1
                    else:
                        incomp_names += 1
                    
            # Count people without families.
            if (not person.get_main_parents_family_handle() and
               not len(person.get_family_handle_list())):
                disconnected += 1
            
            # Count missing birthdays.
            birth_ref = person.get_birth_ref()
            if birth_ref:
                birth = self.__db.get_event_from_handle(birth_ref.ref)
                if not get_date(birth):
                    missing_bday += 1
            else:
                missing_bday += 1

            # Count exact birthdays.
            # events with Date Quality (0 Exact, 1 Estimated, 2 Calculated)
            birth_ref = person.get_birth_ref()
            if birth_ref:
                birth = self.__db.get_event_from_handle(birth_ref.ref)
                if not get_date(birth):
                    mi_bday += 1
                elif birth.get_date_object().get_quality() == 0:
                    ex_birth += 1
                elif birth.get_date_object().get_quality() == 1:
                    est_birth += 1
                elif birth.get_date_object().get_quality() == 2:
                    cal_birth += 1
            else:
                mi_bday += 0

            # Count primary events by quality
            # events with Date Quality (0 Exact, 1 Estimated, 2 Calculated)
            
            for ev_ref in person.get_primary_event_ref_list():
                if ev_ref:
                    ev = self.__db.get_event_from_handle(ev_ref.ref)
                    if ev and ev.type.is_birth():
                        birth_exact, birth_calculated, birth_estimated, birth_missing = self.count_by_quality(ev)

                        exact_birth = exact_birth + birth_exact
                        calculated_birth = calculated_birth + birth_calculated
                        estimated_birth = estimated_birth + birth_estimated
                        missing_birth = missing_birth + birth_missing
                        evList[0:4] = self.count_by_quality(ev)
                        ##EventTuple[0], EventTuple[1], EventTuple[2], EventTuple[3] = self.count_by_quality(ev)

                    if ev and ev.type.is_baptism():
                        bapt_exact, bapt_calculated, bapt_estimated, bapt_missing = self.count_by_quality(ev)

                        exact_bapt = exact_bapt + bapt_exact
                        calculated_bapt = calculated_bapt + bapt_calculated
                        estimated_bapt = estimated_bapt + bapt_estimated
                        missing_bapt = missing_bapt + bapt_missing
                        evList[4:8] = self.count_by_quality(ev)
                        ##EventTuple[4:8] = self.count_by_quality(ev)

                    if ev and ev.type.is_death():
                        death_exact, death_calculated, death_estimated, death_missing = self.count_by_quality(ev)

                        exact_death = exact_death + death_exact
                        calculated_death = calculated_death + death_calculated
                        estimated_death = estimated_death + death_estimated
                        missing_death = missing_death + death_missing
                        evList[8:12] = self.count_by_quality(ev)
                        ##EventTuple[8:12] = self.count_by_quality(ev)

                    if ev and ev.type.is_burial():
                        burial_exact, burial_calculated, burial_estimated, burial_missing = self.count_by_quality(ev)

                        exact_burial = exact_burial + burial_exact
                        calculated_burial = calculated_burial + burial_calculated
                        estimated_burial = estimated_burial + burial_estimated
                        missing_burial = missing_burial + burial_missing
                        evList[12:16] = self.count_by_quality(ev)
                        ##EventTuple[12:16] = self.count_by_quality(ev)

            peDict[person.gramps_id] = tuple(evList)
            peC = Counter(peDict.values())

            # Count genders.
            if person.get_gender() == Person.FEMALE:
                females += 1
            elif person.get_gender() == Person.MALE:
                males += 1
            else:
                unknowns += 1
                
            # Count unique surnames
            for name in [person.get_primary_name()] + person.get_alternate_names():
                if not name.get_surname().strip() in namelist \
                    and not name.get_surname().strip() == "":
                    namelist.append(name.get_surname().strip())
        
        # totals
        sum_bday = ex_birth + est_birth + cal_birth + mi_bday

        sum_birth =  exact_birth + calculated_birth + estimated_birth + missing_birth
        sum_bapt =  exact_bapt + calculated_bapt + estimated_bapt + missing_bapt
        sum_death =  exact_death + calculated_death + estimated_death + missing_death
        sum_burial =  exact_burial + calculated_burial + estimated_burial + missing_burial

        #for key in peDict.keys():
        #    print(key, peDict[key])

        #for k, v in peC.items():
        #    print('Item    ', k, v)

        with open('C://Users//Frink//Documents//dict.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            #for key, value in peDict.items():
            writer.writerows(peDict.items())

			
		
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Number of individuals: %d") % num_people)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Males: %d") % males)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Females: %d") % females)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals with unknown gender: %d") % 
                            unknowns)
        self.doc.end_paragraph()
                            
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Incomplete names: %d") % incomp_names)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals missing birth dates: %d") % 
                            mi_bday)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals exact birth dates: %d") % 
                            ex_birth)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals estimated birth dates: %d") % 
                            est_birth)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals calculated birth dates: %d") % 
                            cal_birth)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals birth dates: %d") % 
                            sum_bday)
        self.doc.end_paragraph()
		
        self.doc.start_paragraph("SR-Normal")
        #print(bapt_exact, bapt_calculated, bapt_estimated, bapt_missing)
        #print(sum_bapt , exact_bapt, calculated_bapt, estimated_bapt, missing_bapt)

        self.doc.write_text(self._("Indiv birth exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_birth, calculated_birth, estimated_birth , missing_birth, sum_birth ))
        self.doc.write_text(self._("Indiv bapt exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_bapt, calculated_bapt, estimated_bapt , missing_bapt, sum_bapt ))
        self.doc.write_text(self._("Indiv death exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_death, calculated_death, estimated_death , missing_death, sum_death ))
        self.doc.write_text(self._("Indiv burrial exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_burial, calculated_burial, estimated_burial , missing_burial, sum_burial ))
        self.doc.end_paragraph()

        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Disconnected individuals: %d") % 
                            disconnected)
        self.doc.end_paragraph()
                            
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Unique surnames: %d") % len(namelist))
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Individuals with media objects: %d") % 
                            with_media)
        self.doc.end_paragraph()

        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("____:_bi____ba____de____bu____|\n"))
        for k, n in sorted(peC.items()):
            k1 = " ".join(str(elem) for elem in k)
            #print('k1    ',k1, type(k1))
            self.doc.write_text(self._("Item: %s %d \n") % (k1, n))
        self.doc.end_paragraph()

    def summarize_families(self):
        """
        Write a summary of all the families in the database.
        """
        # Family records

        exact_marr = 0
        estimated_marr = 0
        calculated_marr = 0
        missing_marr = 0
        sum_marr = 0

        exact_divorce = 0
        estimated_divorce = 0
        calculated_divorce = 0
        missing_divorce = 0
        sum_divorce = 0

        exact_residence = 0
        estimated_residence = 0
        calculated_residence = 0
        missing_residence = 0
        sum_residence = 0

        family_without_events = 0

        fam_father_miss = 0
        fam_mother_miss = 0
        fam_parents_miss = 0

        for family in self.__db.iter_families():
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if not father_handle:
                if not mother_handle:
                    fam_parents_miss += 1
                else:
                    fam_father_miss += 1
            else:
                if not mother_handle:
                    fam_mother_miss += 1

            if len(family.event_ref_list) == 0:
                family_without_events = family_without_events + 1
                continue
				
            for event_ref in family.get_event_ref_list():
                event = self.__db.get_event_from_handle(event_ref.ref)
                if not event:
                   continue

                if (event.get_type().is_marriage() and 
                   (event_ref.get_role().is_family() or 
                    event_ref.get_role().is_primary())):
                    #marriage_date = event.get_date_object()

                    marr_exact, marr_calculated, marr_estimated, marr_missing = self.count_by_quality(event)

                    exact_marr = exact_marr + marr_exact
                    calculated_marr = calculated_marr + marr_calculated
                    estimated_marr = estimated_marr + marr_estimated
                    missing_marr = missing_marr + marr_missing


                if (event and event.get_type().is_divorce() and 
                   (event_ref.get_role().is_family() or 
                    event_ref.get_role().is_primary())):
                    #divorce_date = event.get_date_object()
					
                    divorce_exact, divorce_calculated, divorce_estimated, divorce_missing = self.count_by_quality(event)

                    exact_divorce = exact_divorce + divorce_exact
                    calculated_divorce = calculated_divorce + divorce_calculated
                    estimated_divorce = estimated_divorce + divorce_estimated
                    missing_divorce = missing_divorce + divorce_missing

                if (event and event.get_type() == EventType.RESIDENCE and 
                   (event_ref.get_role().is_family() or 
                    event_ref.get_role().is_primary())):
#                    residence_date = event.get_date_object()
					
                    residence_exact, residence_calculated, residence_estimated, residence_missing = self.count_by_quality(event)

                    exact_residence = exact_residence + residence_exact
                    calculated_residence = calculated_residence + residence_calculated
                    estimated_residence = estimated_residence + residence_estimated
                    missing_residence = missing_residence + residence_missing

        sum_marr =  exact_marr + calculated_marr + estimated_marr + missing_marr
        sum_divorce =  exact_divorce + calculated_divorce + estimated_divorce + missing_divorce
        sum_residence =  exact_residence + calculated_residence + estimated_residence + missing_residence

        self.doc.start_paragraph("SR-Heading")
        self.doc.write_text(self._("Family Information"))
        self.doc.end_paragraph()		

        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Families without Events: %d") % family_without_events)
        self.doc.end_paragraph()		


        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Fam marr exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_marr, calculated_marr, estimated_marr , missing_marr, sum_marr ))
        self.doc.write_text(self._("Fam divorce exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_divorce, calculated_divorce, estimated_divorce , missing_divorce, sum_divorce ))
        self.doc.write_text(self._("Fam residence exac:  %d calc:  %d est:  %d miss: %d  sum: %d \n") % 
                            (exact_residence, calculated_residence, estimated_residence , missing_residence, sum_residence ))
        self.doc.end_paragraph()

        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Fam without father:  %d without mother:  %d without both: %d \n") % 
                            (fam_father_miss, fam_mother_miss, fam_parents_miss))
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Number of families: %d") % 
                            self.__db.get_number_of_families())
        self.doc.end_paragraph()

    def summarize_media(self):
        """
        Write a summary of all the media in the database.
        """
        total_media = 0
        size_in_bytes = 0
        notfound = []
        
        self.doc.start_paragraph("SR-Heading")
        self.doc.write_text(self._("Media Objects"))
        self.doc.end_paragraph()
        
        total_media = len(self.__db.get_media_object_handles())
        mbytes = "0"
        for media_id in self.__db.get_media_object_handles():
            media = self.__db.get_object_from_handle(media_id)
            try:
                size_in_bytes += posixpath.getsize(
                                 media_path_full(self.__db, media.get_path()))
                length = len(str(size_in_bytes))
                if size_in_bytes <= 999999:
                    mbytes = self._("less than 1")
                else:
                    mbytes = str(size_in_bytes)[:(length-6)]
            except:
                notfound.append(media.get_path())
                
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Number of unique media objects: %d") % 
                            total_media)
        self.doc.end_paragraph()
        
        self.doc.start_paragraph("SR-Normal")
        self.doc.write_text(self._("Total size of media objects: %s MB") % 
                            mbytes)
        self.doc.end_paragraph()
    
        if len(notfound) > 0:
            self.doc.start_paragraph("SR-Heading")
            self.doc.write_text(self._("Missing Media Objects"))
            self.doc.end_paragraph()

            for media_path in notfound:
                self.doc.start_paragraph("SR-Normal")
                self.doc.write_text(media_path)
                self.doc.end_paragraph()

#------------------------------------------------------------------------
#
# MYSummaryOptions
#
#------------------------------------------------------------------------
class MYSummaryOptions(MenuReportOptions):
    """
    SummaryOptions provides the options for the SummaryReport.
    """
    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the summary report.
        """
        category_name = _("Report Options")

        stdoptions.add_private_data_option(menu, category_name)
        include_private_data = menu.get_option_by_name('incl_private')
        include_private_data.set_help(_("Whether to count private data"))

        stdoptions.add_localization_option(menu, category_name)

    def make_default_style(self, default_style):
        """Make the default output style for the Summary Report."""
        font = FontStyle()
        font.set_size(16)
        font.set_type_face(FONT_SANS_SERIF)
        font.set_bold(1)
        para = ParagraphStyle()
        para.set_header_level(1)
        para.set_bottom_border(1)
        para.set_top_margin(ReportUtils.pt2cm(3))
        para.set_bottom_margin(ReportUtils.pt2cm(3))
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_("The style used for the title of the page."))
        default_style.add_paragraph_style("SR-Title", para)
        
        font = FontStyle()
        font.set_size(12)
        font.set_bold(True)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_top_margin(0)
        para.set_description(_('The basic style used for sub-headings.'))
        default_style.add_paragraph_style("SR-Heading", para)
        
        font = FontStyle()
        font.set_size(12)
        para = ParagraphStyle()
        para.set(first_indent=-0.75, lmargin=.75)
        para.set_font(font)
        para.set_top_margin(ReportUtils.pt2cm(3))
        para.set_bottom_margin(ReportUtils.pt2cm(3))
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("SR-Normal", para)
