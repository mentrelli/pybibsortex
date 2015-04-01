# pybibsortex
Utility to sort by order of appearance the bibliography of a LaTeX document.

By issuing the command::

    $ python pysortex.py -i inputfile.tex
    
the tex file (and all the files possibly included) will be parsed and the items in the bibliography will be sorted by their order of appearance. The file including the bibliography is automatically backed up before being overwritten.


