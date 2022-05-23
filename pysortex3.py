# -*- coding: utf-8 -*-

#    PySorTeX
#        A small utility that sort the bibliography of a LaTeX document
#        (possibily split into multiple files) which makes use of
#        "thebibliography" environment.
#
#    Copyright (C) 2015, Andrea Mentrelli <andrea.mentrelli@unibo.it>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python

# Changelog:
#   v.0.3 (April 1, 2015)
#   v.0.3.1 (April 5, 2015)
#   v.0.4 (April 6, 2015)
#   v.0.5 (April 14, 2015)
#   v 0.6 (March 12, 2018): fixed problem with legatures (fi, fl, etc.),
#         em-dashes and similar; fixed problem with capital letters with
#         umlaut.

# present version
version = 'v.0.6-py3'

import sys
import os
import re
import operator

S  = "..."
SS = S*2 


def recursive_parser(filename, dirname=None, flag_stripcomments=True, _firstcall=True, _filecount=1, _filename_bib=''):
    """
    returns a string containing all the text of 'filename' file, including
    the files possibily included.
    
    Arguments:
       filename
           name of the root file to parse (all the included files are
           automatically sources into the file)
       dirname [optional, default is working directory]
           directory where the root file is located
       flag_stripcomments [optional, default is True]
           wether to strip off all comments or leave the comments in the 
           parsed string
    """
      
    
    if dirname is None:
        dirname = os.getcwd()
        
    filenamepath = os.path.join(dirname, filename)
    
    try:
        f = open(filenamepath, 'r')
        filename_found = filename
    except:
        try:
            f = open(filenamepath+'.tex', 'r')
            filename_found = filename+'.tex'
        except:
            filename_found = None

    if filename_found is not None:
        
        filenamefoundpath = os.path.join(dirname, filename_found)

        f = open(filenamefoundpath, 'r')

        text = f.read()

        if flag_stripcomments:
            text = re.sub('(%.*\n)','', text) # strip off comments
            str_comment = "without comments]"
        else:
            str_comment = "with comments]"

        if _firstcall:
            dirnameabs = os.path.abspath(dirname)
            print(S+f"working directory: {dirnameabs}")
        print(SS+f"reading file '{filename_found}' [{len(text.splitlines())} lines...{str_comment}")

        pos = [m.start() for m in re.finditer(r'\\input{|\\include{', text)]

        file_bib = [m.start() for m in re.finditer(r'\\begin{thebibliography}', text)]!=[]

        if file_bib:
            _filename_bib = filename_found

        while len(pos) > 0:

            p = pos[0]
            idx = [m.start() for m in re.finditer(r'{|}', text[p:-1])]
            i0 = p + idx[0] # position of first '{' after \input or \include
            i1 = p + idx[1] # position of first '}' after \input or \include
            filename = text[i0+1:i1]

            s, _filecount, _filename_bib = recursive_parser(filename, dirname, flag_stripcomments, False, _filecount+1, _filename_bib)
            text = text[:p] + s + text[i1+1:]

            pos = [m.start() for m in re.finditer(r'\\input{|\\include{', text)]

        if _firstcall:

            print(S+f"read {_filecount} files [total of {len(text.splitlines())} lines]")
            print(S+f"thebibliography environment found in file '{_filename_bib}'")


        return text, _filecount, _filename_bib

    else:
        print(S+f"ERROR: cannot open file '{filename}'")

    return text, _filecount, _filename_bib



def break_multiple_cites(ll):

    # split multiple citations (and remove blank spaces)
    newll = []
    for l in ll:
        for x in l.split(','):
            newll.append(x.strip(' \t\n\r'))
    return newll



def remove_duplicates_preserve_order(ll):

    seen = set()
    seen_add = seen.add # good for performance
    return [ l for l in ll if not (l in seen or seen_add(l))]



def parse_cites(text):

    print(S+"parsed", end=' ')

    cites = re.findall(r'\\cite{((?!#).+?)}', text)
    ncites = len(cites)

    cites = break_multiple_cites(cites)
    cites = remove_duplicates_preserve_order(cites)
    ncitesall = len(cites)

    print(f"{ncitesall} different citations in {ncites} occurrencies of \\cite{'{}'}")

    return cites



def parse_bibitems(text):
    """
    Return a dictionary containing the entries of type '\bibitem{}' inside 
    'thebibliography' environment (note that the entries outside the 
    environment) are discareded.

    Arguments:
       text
           string to parse (as returned by 'recursive_parser()')

    Note: The returned dictionary is made as follows:
      key: the label of the item (i.e. the text inside braces in
           '\bibitem{label}', after stripping all white spaces)
      value: a list [i, item, ], where:
             i: sequential number of the entry
             item: full text entry, i.e. all text of the entry, including 
                   '\bibitem{...}' until the beginning of the next entry (or,
                   for the last entry, until '\end{thebibliography})
             j: sequential number of the entry after sorting
             abc: string for the alphabetical sort (only defined when 
                  alphabetical sort is required)
           
    """

    print(S+"parsed", end=' ')
    bibitems = dict()

    i, i_before, i_after = 0, 0, 0
    
    # find the beginning of 'thebibiography' environment
    try:
        pos_thebibliography_start = [m.start() for m in re.finditer(r'\\begin\s*{\s*thebibliography\s*}', text)][0]
    except:
        pos_thebibliography_start = -1
        
    # find the end of 'thebibiography' environment
    try:
        pos_thebibliography_end = [m.start() for m in re.finditer(r'\\end\s*{\s*thebibliography\s*}', text)][0]
    except:
        pos_thebibliography_end = -1
        
    # check if 'thebibiography' environment has a start and an end
    if pos_thebibliography_start < 0 or pos_thebibliography_end < 0:
        print("ERROR: 'thebibliography' environment not properly defined")
        
    # loop over all the '\bibitem{*}' in the text
    for ix in [m.start() for m in re.finditer(r'\\bibitem{', text)]:

        if ix < pos_thebibliography_start:
            
            i_before += 1 # \bibitem{*} outside (before) 'thebibliography' environment
            
        elif ix > pos_thebibliography_end:
            
            i_after += 1 # \bibitem{*} outside (after) 'thebibliography' environment
            
        else:
            
            i += 1 # \bibitem{*} inside 'thebibliography' environment

            idx = [m.start() for m in re.finditer(r'{|}', text[ix:-1])]
            i0 = ix + idx[0] # position of first '{' after \bibitem
            i1 = ix + idx[1] # position of first '}' after \bibitem
            key = text[i0+1:i1] # bibitem key
            key = key.strip(' \n\t\r') # strip all sort of white spaces from key 

            idx = [m.start() for m in re.finditer(r'\\bibitem{|\\end{', text[ix:-1])]
            i1 = ix + idx[1] # position of end of \bibitem{}
            item = text[ix:i1]

            bibitems[key] = [i, item, 0, None]

    print(f"{i} occurencies of \\bibitem{'{}'} to process")
    
    if i_before > 0:
        print(S+"parsed", end=' ')
        print(f"{i_before} occurencies of \\bibitem{'{}'} before 'thebibliography' environment (discarded)")
        
    if i_after > 0:
        print(S+"parsed", end=' ')
        print(f"{i_after} occurencies of \\bibitem{'{}'} after 'thebibliography' environment (discarded)")

    return bibitems


### crea le stringhe da ordinare per autore
def create_abc(bibitem):
    
    #bibitem = bibitem.decode('utf-8', 'ignore')
    
    # strip out \bibitem{*} and all the possible whitespaces until the next word
    abc = re.sub(r'\s*\\bibitem\s*{((?!#).+?)}\s*', '', bibitem)
    
    # replace some unicode characters
    #   http://utf8-chartable.de/unicode-utf8-table.pl?start=64256&utf8=string-literal
    abc = re.sub(r'\xef\xac\x80', r'ff', abc) # latin small ligature ff
    abc = re.sub(r'\xef\xac\x81', r'fi', abc) # latin small ligature fi
    abc = re.sub(r'\xef\xac\x82', r'fl', abc) # latin small ligature fl
    abc = re.sub(r'\xef\xac\x83', r'ffi', abc) # latin small ligature ffi
    abc = re.sub(r'\xef\xac\x84', r'ffl', abc) # latin small ligature ffl
    abc = re.sub(r'\xef\xac\x85', r'st', abc) # latin small ligature long st
    abc = re.sub(r'\xef\xac\x86', r'st', abc) # latin small ligature st
    #   http://www.utf8-chartable.de/unicode-utf8-table.pl?start=8192&number=128&utf8=string-literal
    abc = re.sub(r'\xe2\x80\x90', r'-', abc) # hyphen
    abc = re.sub(r'\xe2\x80\x91', r'-', abc) # non-breaking hyphen
    abc = re.sub(r'\xe2\x80\x92', r'-', abc) # figure dash
    abc = re.sub(r'\xe2\x80\x93', r'-', abc) # en dash
    abc = re.sub(r'\xe2\x80\x94', r'-', abc) # em dash
    abc = re.sub(r'\xe2\x80\x95', r'-', abc) # horizontal bar
    
    # convert umlaut
    abc = re.sub(r'ä', r'a', abc)
    abc = re.sub(r'ë', r'e', abc)
    abc = re.sub(r'ï', r'i', abc)
    abc = re.sub(r'ö', r'o', abc)
    abc = re.sub(r'ü', r'u', abc)
    abc = re.sub(r'\\"\s*([aeiouAEIOU])', r'\1', abc)
    abc = re.sub(r'\\"\s*{\s*([aeiouAEIOU])\s*}', r'\1', abc)
    
    # convert other funny characters 
    abc = re.sub(r'ß', r'ss', abc) 
    abc = re.sub(r'\\&', r',', abc)
    abc = re.sub(r'–', r'-', abc)
    
    # remove funny accents
    abc = re.sub(r"\\'|'", r'', abc)
    abc = re.sub(r"\\~|~", r'', abc)
    abc = re.sub(r"\\´|´", r'', abc)
    abc = re.sub(r"\\`|`", r'', abc)
    abc = re.sub(r"°", r'', abc)
    
    # remove strange things
    abc = re.sub(r"\s\\\s", r'', abc) # remove \ with spaces on both sides
    
    
    # remove formatting tags
    abc = re.sub(r'\\emph', r'', abc)
    abc = re.sub(r'\\textit', r'', abc)
    abc = re.sub(r'\\bold', r'', abc)
    abc = re.sub(r'\\normalsize', r'', abc)
    
    abc = re.sub(r'\\[a-z]+{', r'{', abc)
    
    # transform 'and' in ','    
    abc = re.sub(r'\sand\s', r', ', abc)
    
    # remove indication of Editor(s)
    abc = re.sub(r'\s\(Ed.\)', r',', abc)
    abc = re.sub(r'\s\(Eds.\)', r',', abc)       
    
    # remove all braces
    abc = re.sub(r'{|}', r'', abc)
    
    
    # strip out the first name matching the following pattern: one or two
    # letters followed by a dot, followed optionally by a whitespace and
    # optionally preceded by a "-".
    abc = re.sub(r'-?([A-Z][a-z]?)\.\s*', r'', abc)
    abc = re.sub(r'\s-?[A-Z],', r'', abc)
    
    
    # remove multiple "," and "-" which may result
    abc = re.sub(r',\s*,', r',', abc)
    abc = re.sub(r'-\s*-', r'-', abc)
    
    # strip out all whitespaces
    abc = re.sub(r'\s', r'', abc)
    
    abc = abc.lower()
    
    """
    #abc = re.sub('\s\\\\\s', ' ', abc)
    abc = re.sub('(T\.R)', 'T. R ', abc)
    line = re.sub('({\\\\"\s*u})|(\\\\"{u})|(\\\\"u)', 'u', line)
    #line = re.sub('({\\\\''\s*c})|(\\\\''{c})|(\\\\''c)', 'c', line)
    line = re.sub('(.\.\-.\.)|(.\-.\.)|(I\,)', '', line)
    #print(line)
    try:
        arg = re.search('(bibitem(\[.*\])?{[^{]*}\s*)(sc)?(it)?({\s*)?'+\
        '([A-Z][a-z]\.\s)*([A-Z]\.\s)*([A-Z]\.[A-Z]\.\s)*{*\s*', line).group(0)
        #arg = re.sub('\\Bi', 'Bi', arg)
        author, flag_err = line[len(arg)+1:], 0
    except:
        author, flag_err = "", 1
    return author, flag_err
    """
    return abc
    
    

def make_new_bib(cites, bibitems, flag_sort, flag_verbose=True):
    
    if flag_sort in ['c', 'call']:
        flag_sort_by_call = True
        str_sort = 'by call'
    else:
        flag_sort_by_call = False
        str_sort = 'alphabetic'
    flag_sort_alphabetic = not flag_sort_by_call
    

    print(SS+f"processing sorted bibliography ({str_sort} order)")

    thebibliography = ''
    i = 0

    if flag_sort_by_call:
        
        bb_keys = list(bibitems.keys())
        i_nokey, i_nocite = 0, 0

        for key in cites:

            if key in bb_keys:
                thebibliography = thebibliography + bibitems[key][1] #+ '\n\n'
                i += 1
                bibitems[key][2] = i
            else:
                if flag_verbose:
                    print(SS+f"WARNING: citation '{key}' does not appear in the bibliography")
                i_nokey += 1


        if i < len(bibitems):

            sorted_bibitems = sorted(list(bibitems.items()), key=operator.itemgetter(1))
            for item in sorted_bibitems:
                if item[1][2] < 1:
                    if flag_verbose:
                        print(SS+f"WARNING: bibitem '{item[0]}' (position #{item[1][0]}) is not cited in the text (moved at the bottom)")
                    key = item[0]
                    thebibliography = thebibliography + bibitems[key][1] #+ '\n\n'
                    i_nocite += 1
                    i += 1

        if i_nokey > 0:
            print(S+f"found {i_nokey} citations without a bibitem entry")

        if i_nocite > 0:
            print(S+f"found {i_nocite} bibliography entries without citations (moved at the bottom)")

        print(S+f"{i} bibliography entries have been processed")

    elif flag_sort_alphabetic:
        
        for key in bibitems:
            bibitems[key][3] = create_abc(bibitems[key][1])
            
        sorted_bibitems = sorted(list(bibitems.items()), key=lambda abc: abc[1][3])
        
        for key, value in sorted_bibitems:
            thebibliography = thebibliography + bibitems[key][1] #+ '\n\n'
            i += 1
            bibitems[key][2] = i
            
            print(f"{i}: {bibitems[key][3]}")

    return thebibliography





def make_backup_file(filename_in):

    if filename_in[-4:] == '.tex':
        filename_in_noext = filename_in[:-4]
    else:
        filename_in_noext = filename_in


    fin = open(filename_in_noext+'.tex', 'r')
    content = fin.read()
    fin.close()

    count = 0
    filename_backup = filename_in_noext + '.backup.' + str(count) + '.tex'

    while os.path.isfile(filename_backup):
        count += 1
        filename_backup = filename_in_noext + '.backup.' + str(count) + '.tex'

    fout = open(filename_backup, 'w')
    fout.write(content)
    fout.close()

    print(S+f"backup of input file containing bibliography: '{filename_backup}'")




def write_new_file(filename_bib_in, filename_bib_out, new_bib):

    f = open(filename_bib_in, 'r')
    text = f.read()

    s_beg, s_end = r'\begin{thebibliography}', r'\end{thebibliography}'
    i0 = text.find(s_beg)
    i0 = text.find(r'}', i0+len(s_beg)) + 1
    i1 = text.find(s_end)

    #new_bib = os.linesep.join([s for s in new_bib.splitlines() if s])

    text_new = text[:i0] + '\n' + new_bib + '\n'+ text[i1:]

    f = open(filename_bib_out, 'w')
    f.write(text_new)
    f.close()

    print(S+f"output file: '{filename_bib_out}'")

    return text_new




def bibsort(filename_in, filename_out=None, dirname=None, \
            flag_sort='call', flag_stripcomments=True, flag_backup=True, 
            flag_verbose=True):

    print("*"*65)
    print(f"* PySorTeX {version} -  Copyright (C) 2015, Andrea Mentrelli       *")
    print("* This program comes with ABSOLUTELY NO WARRANTY.               *")
    print("* This is free software, and you are welcome to redistribute it *")
    print("* under certain conditions. For details, run the program with   *")
    print("* the flag -w (i.e. python pysort.py -w)                        *")
    print("*"*65)
    
    if dirname is None:
        dirname = os.getcwd()

    text, nfiles, filename_bib = recursive_parser(filename_in, dirname, flag_stripcomments)

    if filename_out is None:
        filename_out = filename_bib
        flag_backup = True

    if flag_backup:
        make_backup_file(filename_bib)

    cites = parse_cites(text)

    bibitems = parse_bibitems(text)

    new_bib = make_new_bib(cites, bibitems, flag_sort, flag_verbose)

    if new_bib is not None:
        tt = write_new_file(filename_bib, filename_out, new_bib)
        print(S+"done!")
    else:
        tt = None
        print(S+"...execution failed :/")

    return tt, bibitems




if __name__ == "__main__":

    import argparse

    class ArgParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = ArgParser()
    parser.add_argument('-i','--inputfile', help="input file (containing the bibliography)", required=False)
    parser.add_argument('-d','--directory', help="directory of input file(s)", required=False)
    parser.add_argument('-o','--outputfile', help="output file", required=False)
    parser.add_argument('-s','--sort', help="type of sorting: 'c': by call [default], 'a': alphabetic", required=False)
    parser.add_argument('-c','--comments', help="parsing of comments: 'y': parse comments, 'n': don't parse comments [default]", required=False)
    parser.add_argument('-b','--backup', help="backup of inputfile: 'y': make a backup [default], 'y': don't make a backup", required=False)
    parser.add_argument('-w','--warnings', help="display warnings: 'y': display [default], 'n': don't display", required=False)
    parser.add_argument('-L', action='store_true', help="show licence information", required=False)

    args = vars(parser.parse_args())

    if args['inputfile'] is None:
        filename_in = None
    else:
        filename_in = args['inputfile']
        
    if args['directory'] is None:
        dirname = os.getcwd()
    else:
        dirname = args['directory']

    if args['outputfile'] is None:
        filename_out = None
    else:
        filename_out = args['outputfile']

    if args['sort'] in ['a', 'alphabetic']:
        flag_sort = 'alphabetic'
    else:
        flag_sort = 'call'

    if args['comments'] in ['y', 'yes']:
        flag_stripcomments = False
    else:
        flag_stripcomments = True

    if args['backup'] in ['n', 'no']:
        flag_backup = False
    else:
        flag_backup = True

    if args['L']:
        filename_in = None
        try:
            f = open('LICENSE', 'r')
            GPLv3 = f.read()
            print(GPLv3)
        except:
            print("*** licence file (LICENSE) is missing. ***")
            
    if args['warnings'] in ['n', 'no'] :
        flag_verbose = False
    else:
        flag_verbose = True

    if filename_in is not None:
        fname = os.path.join(dirname, filename_in)
        if os.path.isfile(fname):
            bibsort(filename_in, filename_out, dirname, flag_sort, \
                flag_stripcomments, flag_backup, flag_verbose)
        else:
            print(S+f"file '{fname}' not found")
            print(S+"execution failed :(")