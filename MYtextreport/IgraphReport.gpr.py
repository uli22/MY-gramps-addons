#------------------------------------------------------------------------
#
# PeopleCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'IgraphReport'
plg.name  = _("Igraph Report")
plg.description =  _("Provides an igraph")
plg.version = '1.0'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'IgraphReport.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'IgraphReport'
plg.optionclass = 'IgraphReportOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False