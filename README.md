# MoleculeViewer
A website to display and rotate added molecule SDF files. C library, python server and HTML/jQuery/CSS code built and incorporated together. 
As of 05/2023, some bugs in molecule uploading still being fixed. 

# To compile
* export LD_LIBRARY_PATH=.
* make

# To run
* python3 server.py 53333

# Dependencies
* Swig
* Python 3
* C99 or newer

Only official molecule sdf files can be uploaded. All paths included in the makefile are meant to be run on the UofG server, and need to be changed to run on a local device.
