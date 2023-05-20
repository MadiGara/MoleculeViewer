# MoleculeViewer
A website to display and rotate added molecule SDF files. C library, python server, SQL database, and HTML/jQuery/CSS code built and incorporated together. 

# To compile
* export LD_LIBRARY_PATH=.
* make

# To run
* python3 server.py 53333

# Dependencies
* Swig 3
* Python 3
* C99 or newer
* SQLITE 3

Only official molecule sdf files can be uploaded. All paths included in the makefile are meant to be run on the UofG server, and need to be changed to run on a local device.
