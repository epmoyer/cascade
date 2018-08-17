# Cascade

## Introduction

Cascade is a web-based utility enabling requirements management in Microsoft Word files. Its primary design goal is to provide an efficient and rapid turn-around time for requirement document update/publish cycles.

Cascade requirements documents are authored using Microsoft Word.  Requirement meta-data (such as requirement id, test verification method, etc.) is stored within those documents in the form of "Cascade Directives", which are human readable / maintainable text (in a Cascade-specific syntax).  Because Cascade Directives are just text, Cascade requirements documents are just regular Microsoft Word documents, which means they can be shared, edited, revised, printed, and published by anyone running Microsoft Word.

Authoring, revising, publishing, and viewing Cascade documents requires no special software or plugins.  When a Cascade operation (such as requirements ID annotation, document check, or requirements export) needs to be preformed, that operation is achieved by running the Cascade utility on the MS Word file.

## Current Status

Cascade has been in active use for over two years as a proprietary closed source project.  This open source version (beginning with v2.0.0) is a **Beta** deployment to get the release, install, documentation, and reference server deployment operational before going "Live".  If you are one of the people I am working with directly then you should be using this release/documentation/reference server.  If you have stumbled upon this project on your own then you are welcome to make use of it; just realize that some of the documentation may be lacking right now.  Notably weak areas are:

- Deployment instructions for setting up a custom server
- Deployment instructions for running a local instance
- Example requirements documents to get you started