#------------------------------------------------------------------------
#
# SourcesCitations Report
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'visone-Par-xlsxreport'
plg.name  = _("VISONE Par XLSX")
plg.description =  _("Provides a report for Excel")
plg.version = '1.0'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'visone-Par-xlsxreport.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'VisoneParXLSXReport'
plg.optionclass = 'VisoneParXLSXReportOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False