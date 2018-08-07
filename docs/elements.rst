Elements of a Cascade document
##############################

Cascade Directives
******************

Metadata is entered using "Cascade Directives", which are just JSON_ strings with an extra ``$`` appended to each end. If you're not already familiar with JSON, it's a very simple syntax for expressing data as attribute-value pairs.  For example, the JSON expression ``{"temperature": 78}`` is an object (``{..}``) which contains a single attribute ``"temperature"`` having the value ``78``.  


An example Cascade Directive might look like::

    ${"#section":{"features":["Parental Lock", "RAVE Wireless Installed"]}}$

In this example:

- The base object ``${ ... }$`` contains a single attribute ``"#section"`` whose value is an object ``{...}``.

  - The ``"#section"`` object contains a single attribute called ``"features"`` whose value is a list ``[...]``.

    - The ``"features"`` list contains two strings: ``"Parental Lock"`` and ``"RAVE Wireless Installed"``


All Cascade Directives have the form::

${ <directive_type>: { <directive_info> } }$

\.\.where ``<directive_type>`` is one of the following: ``#document_info``, ``#section``, ``#shortform``, ``#requirement``


+-------------------+
| <directive_type>  |
+===================+
| "#document_info"  |
+-------------------+
| "#shortform"      |
+-------------------+


#document_info
==============

The ``#document_info`` directive does three things:

- It declares the object id prefix(es) which are permissible in the document.
- It declares the number (``"next_id"``) which will be assigned to the next (unassigned) object_id when performing an :ref:`annotate`.
- It declares the **other** `Cascade Directives`_ which are permissible in the document, and what attributes/values they are permitted to contain.

The ``"schemas"`` section of the ``#document_info`` directive follows the established `JSON Schema`_ convention.

Example #document_info directive
------------------------------------

The following is an example of a typical ERD ``#document_info`` directive::

    ${ "#document_info":{
           "object_ids":[
               {
                   "prefix":"ERD-XXXX-",
                   "next_id":1
               }
           ],
           "schemas":[
               {
                   "title":"#shortform",
                   "type":"object",
                   "properties":{
                       "id":{
                           "type":"string"
                       },
                       "method":{
                           "type":"string",
                           "maxLength":1,
                           "pattern":"^(I|A|D|T)$"
                       },
                       "satisfies":{
                          "type":"array",
                          "items":{
                             "type":"string"
                          }
                       }
                   },
                   "required":[
                       "id",
                       "method"
                   ],
                   "additionalProperties":false
               }
           ]
       }
    }$

#shortform
==========

The ``#shortform`` directive is the most common Cascade directive, and it **alone** can be written omitting the ``"<directive_type>"`` attribute (to conserve space). So, for example, the ``#shortform`` directive::

  ${"#shortform": {"id":"ERD-XXXX-?", "method":"I"}}$

Can equivalently be written::

  ${"id":"ERD-XXXX-?", "method":"I"}$

In practice, the directive type (``"#shortform"``) should NEVER be explicitly written in a document.  ``#shortform`` directives are the only Cascade Directive which uses the "Cascade Directive" style (rather than "Cascade Hidden Directive"), so they are they only directives which are (typically) visible to end-users in printed documents.  Using the shorter equivalent form:

- Minimizes visual clutter in printed documents
- Improves comprehension for people reading a Cascade document for the first time
- Minimizes character length.  The directive will typically fit on a single line.

.. -------------------------
.. External Links
.. -------------------------
.. _JSON: http://www.json.org
.. _`JSON Schema`: http://json-schema.org