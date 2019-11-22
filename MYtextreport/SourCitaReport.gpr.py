#------------------------------------------------------------------------
#
# SourcesCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'SourCitaReport'
plg.name  = _("Sour and Cita Report")
plg.description =  _("Provides a source and Citations with notes")
plg.version = '2.0.1'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'SourCitaReport.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'SourCitaReport'
plg.optionclass = 'SourCitaOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False