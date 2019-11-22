#------------------------------------------------------------------------
#
# SourcesCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'peoplestat_bud'
plg.name  = _("People Statistics BuD Report")
plg.description =  _("People Statistics BuD Report")
plg.version = '1.0'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'peoplestat_bud.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'PeopleStatBuDReport'
plg.optionclass = 'PeopleStatBuDOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False