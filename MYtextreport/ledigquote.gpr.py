#------------------------------------------------------------------------
#
# SourcesCitations ReportIndex
#
#------------------------------------------------------------------------
# Version 4.2
# $Id: ledigquote.py 2015-06-19 Frink hansulrich.frink@gmail.com $

plg = newplugin()
plg.id    = 'ledigquote'
plg.name  = _("Ledigenquote")
plg.description =  _("Provides Table of unmarried in place")
plg.version = '1.0'
plg.gramps_target_version = '5.0'
plg.status = STABLE
plg.fname = 'ledigquote.py'
plg.ptype = REPORT
plg.authors = ["Uli22"]
plg.authors_email = ["hansulrich.frink@gmail.com"]
plg.category = CATEGORY_TEXT
plg.reportclass = 'ledigquote'
plg.optionclass = 'ledigquoteOptions'
plg.report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
plg.require_active = False