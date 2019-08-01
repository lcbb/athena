#######################
### Welcome Message ###
#######################

Welcome to Athena!

Athena [1] is an open source Graphical User Interface (GUI) software
application that performs fully automated sequence design of 2D and 3D
wireframe scaffolded DNA origami objects based only on a simple input wireframe
geometric design file.

The aim of Athena is to make it easy for anyone to design and fabricate their
own 2D or 3D wireframe DNA origami object. Toward this end, Athena performs
fully automated sequence design by executing the published open source
algorithms PERDIX [2], METIS [3], DAEDALUS [4, 5], and TALOS [6], which were
developed by the Laboratory of Prof. Mark Bathe in the Department of Biological
Engineering at the Massachusetts Institute of Technology located in Cambridge,
Massachusetts, USA.

After using Athena, please cite the following literature sources when
incorporating any of its results or output files into any publication,
presentation, or poster in order to attribute its developers and funding
sources appropriately:

Citing Athena:
[1] Jun, H., Bricker, W.P., Jackson, S., Bathe, M. Automated Design of
Wireframe Scaffolded DNA Origami with Athena. In preparation (2019).

Citing PERDIX:
[2] Jun, H., Zhang, F., Shepherd, T., Ratalanert, S., Qi, X., Yan, H., Bathe,
M. Autonomously designed free-form 2D DNA origami. Science Advances, 5:
eaav0655 (2019)

Citing METIS:
[3] Jun, H. et al., in preparation (2019)

Citing DAEDALUS:
[4] Veneziano, R., Ratanalert, S., Zhang, K., Zhang, F., Yan, H., Chiu, W.,
Bathe, M. Designer nanoscale DNA assemblies programmed from the top down.
Science, 352: 1534 (2016)
[5] Jun, H., et al., in preparation (2019)

Citing TALOS:
[6] Jun, H., Shepherd, T.R., Zhang, K., Bricker, W.P., Li, S., Chiu, W., Bathe,
M. Automated sequence design of 3D polyhedral wireframe DNA origami with
honeycomb edges. ACS Nano, 13: 2083 (2019)

#######################################################
### Important Notes on Wireframe Input Design Files ###
#######################################################

Only PLY files are accepted by Athena as input design files. The PLY file
format is a common Computer Aided Design (CAD) file format, which you can read
about here: https://en.wikipedia.org/wiki/PLY_(file_format)

A large number of example 2D and 3D PLY files are provided within Athena.
These source files can be viewed at https://github.com/lcbb/athena/tree/master/sample_inputs

Please note that performing 2D sequence design using PERDIX and METIS requires
that the input PLY design file geometry be positioned within the XY plane,
which means that Z=0 for all vertex coordinates specified within the 2D
object's PLY file. This convention tells Athena that the geometry is 2D. All
other input PLY files (i.e., with any non-zero vertex Z-coordinate) will be
treated as 3D by Athena.

Please also note that all vertices listed within any input PLY file must be
used in at least one polygon within the input. While Athena can display a PLY
file that contains unused vertices, these files cannot be processed by PERDIX,
METIS, DAEDALUS, or TALOS to generate sequence designs, and will therefore be
rejected by these sequence design tools.

######################
### For Developers ###
######################

Athena is provided as open source so that other developers can further build on
its capabilities and tools. Please refer to HACKING.txt for information on
building and modifying Athena.



########################
### Acknowledgements ###
########################

The Laboratory of Prof. Mark Bathe is grateful to the National Science
Foundation for providing funding to develop Athena. The Laboratory of Prof.
Mark Bathe is additionally grateful to both the National Science Foundation and
the Office of Naval Research for providing the necessary funding to develop the
sequence design algorithms that enable Athena, namely PERDIX, METIS, DAEDALUS,
and TALOS.

Athena includes an option to generate and save PDB files from the results of
its sequence tools.  In output PDB files, atomic coordinates for nucleic acids
are based on the standard reference frame designed for average A- and B-form
DNA in Olsen et al. [7]

[7] WK Olsen, M Bansal, SK Burley, RE Dickerson, M Gerstein, SC Harvey, U Heinemann,
X-J Lu, S Neidle, Z Shakked, H Sklenar, M Suzuki, C-S Tung, E Westhof,
C Wolberger, HM Berman. A standard reference frame for the description of 
nucleic acid base-pair geometry. Journal of Molecular Biology 313, 229-237 
(2001).


##########################
### End of README File ###
##########################


