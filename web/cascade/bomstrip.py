""" Strip the UTF-8 Byte Order Mark (BOM) from a file (if it exists)
"""
import codecs

BOMLEN = len(codecs.BOM_UTF8)

def copy_and_strip_bom(infilename, outfilename):
    """Copy file into a new file, excluding the BOM (if it exists)
    """
    buffer_size = 4096

    with open(infilename, "r+b") as infile:
        with open(outfilename, "wb") as outfile:
            chunk = infile.read(buffer_size)
            if chunk.startswith(codecs.BOM_UTF8):
                chunk = chunk[BOMLEN:]
            while chunk:
                outfile.write(chunk)
                chunk = infile.read(buffer_size)

def open_and_seek_past_bom(infilename):
    """Open file, seek past BOM (if it exists), and return the handle to the open file object
    """

    infile = open(infilename, "r+b")
    chunk = infile.read(BOMLEN * 2)
    if chunk.startswith(codecs.BOM_UTF8):
        infile.seek(BOMLEN)
    else:
        infile.seek(0)
    return infile
