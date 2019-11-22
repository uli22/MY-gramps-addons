#------------------------------------------------------------------------
#
# SourcesCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'SourcesCitationsReport'
plg.name  = _("Sources and Citations Report")
plg.description =  _("Provides a source and Citations Report with notes")
plg.version = '3.6.0'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'SourcesCitationsReport.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'SourcesCitationsReport'
plg.optionclass = 'SourcesCitationsOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False