#------------------------------------------------------------------------
#
# PeopleCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'placefamilyreport'
plg.name  = _("Placefamily MY Report")
plg.description =  _("Provides an Placefamily Report")
plg.version = '1.5'
plg.gramps_target_version = '5.1'
plg.status = STABLE
plg.fname = 'MYplacefamilyreport.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'PlaceFamilyReport'
plg.optionclass = 'PlaceFamilyReportOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False