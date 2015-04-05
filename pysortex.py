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


import sys
import os
import re
import operator

version = 'v. 0.3.1' # (April 6, 2015)
S = "."


def recursive_parser(filename, flag_stripcomments=True, _firstcall=True, _filecount=1, _filename_bib=''):

    try:
        f = open(filename, 'r')
        filename_found = filename
    except:
        try:
            f = open(filename+'.tex', 'r')
            filename_found = filename+'.tex'
        except:
            filename_found = None

    if filename_found is not None:

        f = open(filename_found, 'r')

        text = f.read()

        if flag_stripcomments:
            text = re.sub('(%.*\n)','', text) # strip off comments
            str_comment = "without comments]"
        else:
            str_comment = "with comments]"

        print S*6+"reading file '{}' [{} lines...{}".format(filename_found, len(text.splitlines()), str_comment)

        pos = [m.start() for m in re.finditer(ur'\\input{|\\include{', text)]

        file_bib = [m.start() for m in re.finditer(ur'\\begin{thebibliography}', text)]!=[]

        if file_bib:
            _filename_bib = filename_found

        while len(pos) > 0:

            p = pos[0]
            idx = [m.start() for m in re.finditer(ur'{|}', text[p:-1])]
            i0 = p + idx[0] # position of first '{' after \input or \include
            i1 = p + idx[1] # position of first '}' after \input or \include
            filename = text[i0+1:i1]

            s, _filecount, _filename_bib = recursive_parser(filename, flag_stripcomments, False, _filecount+1, _filename_bib)
            text = text[:p] + s + text[i1+1:]

            pos = [m.start() for m in re.finditer(ur'\\input{|\\include{', text)]

        if _firstcall:

            print S*3+"read {} files [total of {} lines]".format(_filecount, len(text.splitlines()))
            print S*3+"thebibliography environment found in file '{}'".format(_filename_bib)


        return text, _filecount, _filename_bib

    else:
        print S*3+"ERROR: cannot open file '{}'".format(filename)

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

    print S*3+"parsed",

    cites = re.findall(ur'\\cite{((?!#).+?)}', text)
    ncites = len(cites)

    cites = break_multiple_cites(cites)
    cites = remove_duplicates_preserve_order(cites)
    ncitesall = len(cites)

    print "{} different citations in {} occurrencies of \\cite{}".format(ncitesall, ncites, '{}')

    return cites



def parse_bibitems(text):

    print S*3+"parsed",
    bibitems = dict()

    i, i_before, i_after = 0, 0, 0
    
    try:
        pos_thebibliography_start = [m.start() for m in re.finditer(ur'\\begin\s*{\s*thebibliography\s*}', text)][0]
    except:
        pos_thebibliography_start = -1
        
    try:
        pos_thebibliography_end = [m.start() for m in re.finditer(ur'\\end\s*{\s*thebibliography\s*}', text)][0]
    except:
        pos_thebibliography_end = -1
        
    if pos_thebibliography_start < 0 or pos_thebibliography_end < 0:
        print "ERROR: 'thebibliography' environment not properly defined"

    for ix in [m.start() for m in re.finditer(ur'\\bibitem{', text)]:

        if ix < pos_thebibliography_start:
            
            i_before += 1
            
        elif ix > pos_thebibliography_end:
            
            i_after += 1
            
        else:
            
            i += 1

            idx = [m.start() for m in re.finditer(ur'{|}', text[ix:-1])]
            i0 = ix + idx[0] # position of first '{' after \bibitem
            i1 = ix + idx[1] # position of first '}' after \bibitem
            key = text[i0+1:i1]
            key = key.strip(' \n\t\r')

            idx = [m.start() for m in re.finditer(ur'\\bibitem{|\\end{', text[ix:-1])]
            i1 = ix + idx[1] # position of end of \bibitem{}
            item = text[ix:i1]

            bibitems[key] = [i, item, 0]

    print "{} occurencies of \\bibitem{} to process".format(i, '{}')
    
    if i_before > 0:
        print S*3+"parsed",
        print "{} occurencies of \\bibitem{} before 'thebibliography' environment (discarded)".format(i_before, '{}')
        
    if i_after > 0:
        print S*3+"parsed",
        print "{} occurencies of \\bibitem{} after 'thebibliography' environment (discarded)".format(i_after, '{}')

    return bibitems



def make_new_bib(cites, bibitems, flag_sort):

    print S*6+"processing ordered bibliography"

    thebibliography = ''
    i, i_nokey, i_nocite = 0, 0, 0
    bb_keys = bibitems.keys()

    if flag_sort in ['c', 'call']:

        for key in cites:

            if key in bb_keys:
                thebibliography = thebibliography + bibitems[key][1] #+ '\n\n'
                i += 1
                bibitems[key][2] = i
            else:
                print S*6+"WARNING: citation '{}' does not appear in the bibliography".format(key)
                i_nokey += 1


        if i < len(bibitems):

            sorted_bibitems = sorted(bibitems.items(), key=operator.itemgetter(1))
            for item in sorted_bibitems:
                if item[1][2] < 1:
                    print S*6+"WARNING: bibitem '{}' (position #{}) is not cited in the text (moved at the bottom)".format(item[0], item[1][0])
                    key = item[0]
                    thebibliography = thebibliography + bibitems[key][1] #+ '\n\n'
                    i_nocite += 1
                    i += 1

        if i_nokey > 0:
            print S*3+"found {} citations without a bibitem entry".format(i_nokey)

        if i_nocite > 0:
            print S*3+"found {} bibliography entries without citations (moved at the bottom)".format(i_nocite)

        print S*3+"{} bibliography entries have been processed".format(i)

    elif flag_sort in ['a', 'alphabetic']:

        print S*3+"ERROR: alphabetic sorting still to implement."
        thebibliography = None

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

    print S*3+"backup of input file: '{}'".format(filename_backup)




def write_new_file(filename_bib, new_bib):

    f = open(filename_bib, 'r')
    text = f.read()

    s_beg, s_end = r'\begin{thebibliography}', r'\end{thebibliography}'
    i0 = text.find(s_beg)
    i0 = text.find(r'}', i0+len(s_beg)) + 1
    i1 = text.find(s_end)

    #new_bib = os.linesep.join([s for s in new_bib.splitlines() if s])

    text_new = text[:i0] + '\n' + new_bib + '\n'+ text[i1:]

    f = open(filename_bib, 'w')
    f.write(text_new)
    f.close()

    print S*3+"output file: '{}'".format(filename_bib)

    return text_new




def bibsort(filename_in, filename_out=None, flag_sort='call', flag_stripcomments=True, flag_backup=True):

    print "*"*65
    print "* PySorTeX {} -  Copyright (C) 2015, Andrea Mentrelli       *".format(version)
    print "* This program comes with ABSOLUTELY NO WARRANTY.               *"
    print "* This is free software, and you are welcome to redistribute it *"
    print "* under certain conditions. For details, run the program with   *"
    print "* the flag -w (i.e. python pysort.py -w)                        *"
    print "*"*65

    text, nfiles, filename_bib = recursive_parser(filename_in, flag_stripcomments)

    if filename_out is None:
        filename_out = filename_bib
        flag_backup = True

    if flag_backup:
        make_backup_file(filename_bib)

    cites = parse_cites(text)

    bibitems = parse_bibitems(text)

    new_bib = make_new_bib(cites, bibitems, flag_sort)

    if new_bib is not None:
        tt = write_new_file(filename_out, new_bib)
        print S*3+"done!"
    else:
        tt = None
        print S*3+"...execution failed"

    return tt




if __name__ == "__main__":

    import argparse

    class ArgParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = ArgParser()
    parser.add_argument('-i','--inputfile', help="input file (containing the bibliography)", required=False)
    parser.add_argument('-o','--outputfile', help="output file", required=False)
    parser.add_argument('-s','--sort', help="type of sorting: 'c': by call [default], 'a': alphabetic", required=False)
    parser.add_argument('-c','--comments', help="parsing of comments: 'y': parse comments, 'n': don't parse comments [default]", required=False)
    parser.add_argument('-b','--backup', help="backup of inputfile: 'y': make a backup [default], 'y': don't make a backup", required=False)
    parser.add_argument('-w', action='store_true', help="show licence information", required=False)

    args = vars(parser.parse_args())

    if args['inputfile'] is None:
        filename_in = None
    else:
        filename_in = args['inputfile']

    if args['outputfile'] is None:
        filename_out = None
    else:
        filename_out = args['outputfile']

    if args['sort'] in ['c', 'call']:
        flag_sort = 'call'
    elif args['sort'] in ['a', 'alphabetic']:
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

    if args['w']:
        filename_in = None
        try:
            f = open('LICENSE', 'r')
            GPLv3 = f.read()
            print GPLv3
        except:
            print "*** licence file (LICENSE) is missing. ***"

    if filename_in is not None:
        if os.path.isfile(filename_in):
            bibsort(filename_in, filename_out, flag_sort, flag_stripcomments, flag_backup)
        else:
            print S*3+"file '{}' not found".format(filename_in)
            print S*3+"execution failed :("
