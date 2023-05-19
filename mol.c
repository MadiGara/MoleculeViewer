#include "mol.h"

//set value of atom passed in
void atomset (atom * atom, char element[3], double * x, double * y, double * z) 
{
    for (int i = 0; i < 3; i++) {
        atom->element[i] = element[i];
        if(element[i] == '\0') {
            break;
        }
    }
    atom->x = *x;
    atom->y = *y;
    atom->z = *z;
}

//get value of atom passed in by reference
void atomget (atom * atom, char element[3], double * x, double * y, double * z) 
{
    for (int i = 0; i < 3; i++) {
        element[i] = atom->element[i];
        if(atom->element[i] == '\0') {
            break;
        }
    }
    *x = atom->x;
    *y = atom->y;
    *z = atom->z;
}

//set bonds between atoms
void bondset (bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs) 
{
    bond->a1 = *a1;
    bond->a2 = *a2;
    bond->atoms = *atoms;
    bond->epairs = *epairs;

    compute_coords(bond);
}

//fetch bonds between atosm by reference
void bondget (bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs) 
{
    *a1 = bond->a1;
    *a2 = bond->a2;
    *atoms = bond->atoms;
    *epairs = bond->epairs;
}

//compute and set z, x1, y1, x2, y2, len, dx, and dy values of bond
void compute_coords (bond * bond) 
{
    bond->x1 = (bond->atoms[bond->a1]).x;
    bond->x2 = (bond->atoms[bond->a2]).x;
    bond->y1 = (bond->atoms[bond->a1]).y;
    bond->y2 = (bond->atoms[bond->a2]).y;
    bond->z = (((bond->atoms[bond->a1]).z) + ((bond->atoms[bond->a2]).z))/2.0;

    //distance between a1 and a2
    bond->len = sqrt((pow((bond->x2 - bond->x1), 2)) + (pow((bond->y2 - bond->y1), 2)));
    bond->dx = (bond->x2 - bond->x1)/bond->len;
    bond->dy = (bond->y2 - bond->y1)/bond->len;
}

//allocate space for one molecule and its corresponding arrays
molecule * molmalloc (unsigned short atom_max, unsigned short bond_max) 
{
    molecule * mallocMol = malloc(sizeof(molecule));
    if (mallocMol == NULL) {
        fprintf(stderr, "Molmalloc failed for molecule. Exiting.\n");
        return NULL;
    }

    mallocMol->atom_max = atom_max;
    mallocMol->atom_no = 0;

    mallocMol->atoms = malloc(sizeof(struct atom) * atom_max);
    mallocMol->atom_ptrs = malloc(sizeof(struct atom *) * atom_max);

    if ((mallocMol->atoms == NULL) && (mallocMol->atom_max != 0)) {
        fprintf(stderr, "Molmalloc failed for atoms. Exiting.\n");
        return NULL;
    }
    if ((mallocMol->atom_ptrs == NULL) && (mallocMol->atom_max != 0)) {
        fprintf(stderr, "Molmalloc failed for atom_ptrs. Exiting.\n");
        return NULL;
    }
    
    mallocMol->bond_max = bond_max;
    mallocMol->bond_no = 0;

    mallocMol->bonds = malloc(sizeof(struct bond) * bond_max);
    mallocMol->bond_ptrs = malloc(sizeof(struct bond *) * bond_max);

    if ((mallocMol->bonds == NULL) && (mallocMol->bond_max != 0)) {
        fprintf(stderr, "Molmalloc failed for bonds. Exiting.\n");
        return NULL;
    }
    if ((mallocMol->bond_ptrs == NULL) && (mallocMol->bond_max != 0)) {
        fprintf(stderr, "Molmalloc failed for bond_ptrs. Exiting.\n");
        return NULL;
    }
    
    return mallocMol;
}

//duplicate the source molecule
molecule * molcopy (molecule * src)
{
    molecule * copiedMol = NULL;
    copiedMol = molmalloc(src->atom_max, src->bond_max);

    if (copiedMol == NULL) {
        fprintf(stderr, "Molmalloc failed for molcopy. Exiting.\n");
        return NULL;
    }

    //when molappend is called, it will increment the _nos for copiedMol itself
    for (int i = 0; i < src->atom_no; i++) {
        molappend_atom(copiedMol, &src->atoms[i]);
    }

    for (int i = 0; i < src->bond_no; i++) {
        molappend_bond(copiedMol, &src->bonds[i]);
    }
    return copiedMol;
}

//free allocated space for ptr molecule
void molfree (molecule * ptr) 
{
    free(ptr->bond_ptrs);
    free(ptr->atom_ptrs);
    free(ptr->bonds);
    free(ptr->atoms);
    free(ptr);
}

//add the atom from the parameter to the end of the molecule's atoms array
void molappend_atom (molecule * molecule, atom * atom) 
{
    if (molecule->atom_no == molecule->atom_max) {
        if (molecule->atom_max == 0) {
            molecule->atom_max = 1;
        } else {
            molecule->atom_max *= 2;
        }

        molecule->atoms = realloc(molecule->atoms, sizeof(struct atom) * molecule->atom_max);
        molecule->atom_ptrs = realloc(molecule->atom_ptrs, sizeof(struct atom *) * molecule->atom_max);

        if (molecule->atoms == NULL) {
            fprintf(stderr, "Realloc failed for atoms. Exiting.\n");
            exit(0);
        }
        if (molecule->atom_ptrs == NULL) {
            fprintf(stderr, "Realloc failed for atom_ptrs. Exiting.\n");
            exit(0);
        }
    }

    molecule->atoms[molecule->atom_no] = *atom;
    // reaffirm atom_ptrs post-realloc
    for (int i = 0; i <= molecule->atom_no; i++) {
        molecule->atom_ptrs[i] = &molecule->atoms[i];
    }
    molecule->atom_no++;
}

//add the bond from the parameter to the end of molecule's bonds array
void molappend_bond (molecule * molecule, bond * bond) 
{
    if (molecule->bond_no >= molecule->bond_max) {
        if (molecule->bond_max == 0) {
            molecule->bond_max = 1;
        } else {
            molecule->bond_max *= 2;
        }

        molecule->bonds = realloc(molecule->bonds, sizeof(struct bond) * molecule->bond_max);
        molecule->bond_ptrs = realloc(molecule->bond_ptrs, sizeof(struct bond *) * molecule->bond_max);

        if (molecule->bonds == NULL) {
            fprintf(stderr, "Realloc failed for bonds. Exiting.\n");
            exit(0);
        }
        if (molecule->bond_ptrs == NULL) {
            fprintf(stderr, "Realloc failed for bond_ptrs. Exiting.\n");
            exit(0);
        }
    }

    //pass atoms array from molecule to bonds
    bond->atoms = molecule->atoms;
    compute_coords(bond);

    molecule->bonds[molecule->bond_no] = *bond;
    // reaffirm bond_ptrs post-realloc
    for (int i = 0; i <= molecule->bond_no; i++) {
        molecule->bond_ptrs[i] = &molecule->bonds[i];
    }
    molecule->bond_no++;
}

/* Helper functions for molsort */

//compare atoms by z value
int atom_compare (const void * a1_ptr, const void * a2_ptr)
{
    atom * a1, * a2;
    a1 = *(atom **)a1_ptr;
    a2 = *(atom **)a2_ptr;
    
    if (a1->z > a2->z) {
        return 1;
    } else if (a1->z < a2->z) {
        return -1;
    } else {
        return 0;
    }
}

//compare average of the z values of both atoms of a bond
int bond_comp (const void * a, const void * b) 
{
    bond * b1, * b2;
    b1 = *(bond **) a;
    b2 = *(bond **) b;

    //z values set in compute_coords
    float b1_z = b1->z;
    float b2_z = b2->z;

    if (b1_z > b2_z) {
        return 1;
    } else if (b1_z < b2_z) {
        return -1;
    } else {
        return 0;
    }
}

/* End of helper functions */

//sort atoms in ascending order by z value
void molsort (molecule * molecule)
{
    qsort(molecule->atom_ptrs, molecule->atom_no, sizeof(atom *), atom_compare);
 
    qsort(molecule->bond_ptrs, molecule->bond_no, sizeof(bond *), bond_comp);
}

//establish matrix for rotation about the x axis of deg degrees
void xrotation (xform_matrix xform_matrix, unsigned short deg) 
{
    // convert to radians
    double rads;
    rads = deg * (M_PI / 180.0);

    xform_matrix[0][0] = 1;
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = 0;

    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = cos(rads);
    xform_matrix[1][2] = -sin(rads);

    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = sin(rads);
    xform_matrix[2][2] = cos(rads);
}

//establish matrix for rotation about the y axis of deg degrees
void yrotation (xform_matrix xform_matrix, unsigned short deg) 
{
    double rads;
    rads = deg * (M_PI / 180.0);

    xform_matrix[0][0] = cos(rads);
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = sin(rads);

    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = 1;
    xform_matrix[1][2] = 0;

    xform_matrix[2][0] = -sin(rads);
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = cos(rads);
}

//establish matrix for rotation about the z axis of deg degrees
void zrotation (xform_matrix xform_matrix, unsigned short deg) 
{
    double rads;
    rads = deg * (M_PI / 180.0);

    xform_matrix[0][0] = cos(rads);
    xform_matrix[0][1] = -sin(rads);
    xform_matrix[0][2] = 0;

    xform_matrix[1][0] = sin(rads);
    xform_matrix[1][1] = cos(rads);
    xform_matrix[1][2] = 0;

    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = 1;
}

//matrix multiplication of each atom's x y z values by the transformation matrix
void mol_xform (molecule * molecule, xform_matrix matrix) 
{
    //copy so as not to override original values when using in matrix multiplication
    struct molecule * origMol;
    origMol = molcopy(molecule);

    for (int i = 0; i < molecule->atom_no; i++) {
        molecule->atoms[i].x = (matrix[0][0] * origMol->atoms[i].x)
                               + (matrix[0][1] * origMol->atoms[i].y)
                               + (matrix[0][2] * origMol->atoms[i].z);
        molecule->atoms[i].y = (matrix[1][0] * origMol->atoms[i].x)
                               + (matrix[1][1] * origMol->atoms[i].y)
                               + (matrix[1][2] * origMol->atoms[i].z);
        molecule->atoms[i].z = (matrix[2][0] * origMol->atoms[i].x)
                               + (matrix[2][1] * origMol->atoms[i].y)
                               + (matrix[2][2] * origMol->atoms[i].z);
    }

    //pass atoms array from molecule to bonds
    molecule->bonds->atoms = molecule->atoms;
    for (int i = 0; i < molecule->bond_no; i++) {
        compute_coords(molecule->bond_ptrs[i]);
    }

    free(origMol);
}
