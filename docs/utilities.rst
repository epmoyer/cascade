Utilities
#########

The current web interface supports the following operations:

General
*******

Check
=====

Verify document integrity:

* Object ID Prefixes match "prefix" directive.
* Object ID Suffix is number or "?"
* No duplicate object IDs.
* Report unassigned Object IDs.
* Verify "next_id" directive exceeds highest Object ID used.

.. _annotate:

Annotate
========
Annotate any blank requirement object IDs (IDs with a "-?" suffix)

Annotate Reset
==============
Replace all requirement object ID suffix numbers with "-?"

Export
******

.. _aggregate:

Aggregate
=========
Exports an Excel spreadsheet summarizing the information in all requirements directives.

Migration
*********

Apply Styles
============
Corrects documents which were converted to Cascade format 
before Cascade used styles for directives (it previously used 
localized ad-hoc styling applied directly to the paragraphs).
This utility applies the styles accordingly, but you must first add the
Cascade styles to your document.

History
=======
Cascade began as a command line application. While some Cascade functions can be still be performed at the command line, the 
command line interface is no longer used for production (though some of the commands continue to have usefulness
to developers).  In production, Cascade is launched in http mode (using its http command line option, ``python -m cascade http``) 
and is accessed as a web service.