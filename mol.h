#ifndef _mol_h
#define _mol_h

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define M_PI 3.14159265358979323846

// typedefs, struct definitions, function prototypes

typedef struct atom
{
    char element[3];
    double x, y, z;
} atom;

typedef struct bond
{
    unsigned short a1, a2;  //indexes
    unsigned char epairs;
    atom * atoms;           //array address
    double x1, x2, y1, y2, z, len, dx, dy;   //x and y differences
    //len is distance b/w a1 and a2
} bond;

typedef struct molecule 
{
    unsigned short atom_max, atom_no;
    atom * atoms, ** atom_ptrs;
    unsigned short bond_max, bond_no;
    bond * bonds, ** bond_ptrs;
} molecule;

typedef double xform_matrix[3][3];

typedef struct mx_wrapper
{
    //first two must be zero, third is rotation
    xform_matrix xform_matrix;
} mx_wrapper;


// function prototypes

void atomset (atom * atom, char element[3], double * x, double * y, double * z);

void atomget (atom * atom, char element[3], double * x, double * y, double * z);

void bondset (bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs);

void bondget (bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs);

molecule * molmalloc (unsigned short atom_max, unsigned short bond_max);

molecule * molcopy (molecule * src);

void molfree (molecule * ptr);

void molappend_atom (molecule * molecule, atom * atom);

void molappend_bond (molecule * molecule, bond * bond);

void molsort (molecule * molecule);

void compute_coords(bond * bond);

int atom_compare (const void *, const void *);

int bond_comp (const void *, const void *);

void xrotation (xform_matrix xform_matrix, unsigned short deg);

void yrotation (xform_matrix xform_matrix, unsigned short deg);

void zrotation (xform_matrix xform_matrix, unsigned short deg);

void mol_xform (molecule * molecule, xform_matrix matrix);

#endif
