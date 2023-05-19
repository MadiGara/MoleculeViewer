COMPILER = clang
CFLAGS = -std=c99 -Wall -pedantic
LIB = libmol.so

all: $(LIB) molecule_wrap.o _molecule.so

mol.o: mol.c mol.h
	$(COMPILER) $(CFLAGS) -fpic -c mol.c -o mol.o
libmol.so: mol.o
	$(COMPILER) $(CFLAGS) -shared mol.o -lm -o $(LIB)
molecule_wrap.o: molecule_wrap.c
	$(COMPILER) $(CFLAGS) -c molecule_wrap.c -fPIC -I/usr/include/python3.7m -o $@
molecule_wrap.c: molecule.i mol.c mol.h $(LIB)
	swig3.0 -python molecule.i
_molecule.so: molecule_wrap.o
	$(COMPILER) molecule_wrap.o -L. -shared -lmol -dynamiclib -L/usr/lib/python3.7/config-3.7m-x86_64-linux-gnu -lpython3.7m -o $@

clean:
	rm *.o *.so