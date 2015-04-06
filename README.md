# pybibsortex
Utility to sort by order of appearance the bibliography of a LaTeX document making use of 'thebibliography' environment.

Assuming that the main tex file is named 'inputfile.tex', and it is located in the current directory, the program can be run by issuing the command::

    $ python pysortex.py -i inputfile.tex
    
If the 'inputfile.tex' is located in the directory '/path/to/files', the program can be run by issuing the command::

    $ python pysortex.py -i inputfile.tex -d '/path/to/files'
    
Other options are illustrated by issuing::

    $ python pysortex.py --help

    
The tex file (and all the files possibly included, which have to be located in the same directory) will be parsed and the items in the bibliography will be sorted by their order of appearance. The file including the bibliography is automatically backed up before being overwritten. (If the file containing the bibliography is named 'inputfilebib.tex', the backup file is named 'inputfilebib.backup.X.tex', where X is a progressive number as to maintain a history of the backup files).

As of today, this project is very much a work in progress. Bugs notifications and requests for additional features/facilities are welcome. 


