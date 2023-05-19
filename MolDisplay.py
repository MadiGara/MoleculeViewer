#!/usr/bin/python3

import molecule;

header = """<svg version="1.1" width="1000" height="1000" xmlns="http://www.w3.org/2000/svg">""";

footer = """</svg>""";

offsetx = 500;
offsety = 500;

# Creating a Python library to read SDF files, represent the molecules, and write SVG files

# wrapper class for atom struct in C code
class Atom: 

    # constructor that calls atom from C code and establishes its z value
    def __init__(self, c_atom):
        self.atom = c_atom;
        self.z = c_atom.z;
    
    # toString return of an atom's values
    def __str__(self):
        return "%c %f %f %f" % (self.atom.element, self.atom.x, self.atom.y, self.z); 

    # establish parameters for drawing atom circle
    def svg(self):
        x_center = (self.atom.x * 100.0) + offsetx;
        y_center = (self.atom.y * 100.0) + offsety;
        rad = radius[self.atom.element];
        colour = element_name[self.atom.element];
        return '  <circle cx="%.2f" cy="%.2f" r="%d" fill="url(#%s)"/>\n' % (x_center, y_center, rad, colour);

# wrapper class for bond struct in C code
class Bond:

    # constructor that calls bond from C code and establishes its z value
    def __init__(self, c_bond):
        self.bond = c_bond;
        self.z = c_bond.z;

    # toString return of bond's values
    def __str__(self):
        return "a1: %d %f %f\na2: %d %f %f\nz: %f, len: %f, dx: %f, dy: %f" % \
            (self.bond.a1, self.bond.x1, self.bond.y1, self.bond.a2, self.bond.x2, self.bond.y2, \
             self.z, self.bond.len, self.bond.dx, self.bond.dy);
    
    # establish four corners for drawing bond rectangle
    def svg(self):

        x_center1 = (self.bond.x1 * 100.0) + offsetx;
        y_center1 = (self.bond.y1 * 100.0) + offsety;
        x_center2 = (self.bond.x2 * 100.0) + offsetx;
        y_center2 = (self.bond.y2 * 100.0) + offsety;

        # establish points 10 pixels up and down from atom centers - PB
        x1 = x_center1 - (self.bond.dy * 10.0);
        y1 = y_center1 + (self.bond.dx * 10.0);
        x2 = x_center2 - (self.bond.dy * 10.0);
        y2 = y_center2 + (self.bond.dx * 10.0);

        x3 = x_center2 + (self.bond.dy * 10.0);
        y3 = y_center2 - (self.bond.dx * 10.0);
        x4 = x_center1 + (self.bond.dy * 10.0);
        y4 = y_center1 - (self.bond.dx * 10.0);

        return '  <polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="green"/>\n' % \
            (x1, y1, x2, y2, x3, y3, x4, y4);

# subclass of molecule class from C code
class Molecule(molecule.molecule):
    
    # constructor to initialize Molecule as subclass of molecule
    def __init__(self): 
        super().__init__();

    # toString return of molecule's max and no values
    def __str__(self):
        return "atom max: %d, atom no: %d, bond max: %d, bond no: %d\n" % (self.atom_max, self.atom_no, self.bond_max, self.bond_no);

    # a4 test given rotation function
    def rotate(self, xrot, yrot, zrot):
        molxform = molecule.mx_wrapper(xrot, yrot, zrot);
        self.xform(molxform.xform_matrix);

    # returns header + svg of Atom and Bond sorted by z value + footer as a string
    def svg(self):
        i = 0;
        j = 0;
        final = "";

        final += header;
        
        while i < self.atom_no and j < self.bond_no:
            atom = Atom(self.get_atom(i));
            bond = Bond(self.get_bond(j));

            if atom.z > bond.z :
                final += bond.svg();
                j += 1;
            else:
                final += atom.svg();
                i += 1;

        # append leftover bonds or molecules as appropriate once one array exhausted
        if i == self.atom_no:
            while j < self.bond_no:
                bond = Bond(self.get_bond(j));
                final += bond.svg();
                j += 1;

        if j == self.bond_no:
            while i < self.atom_no:
                atom = Atom(self.get_atom(i));
                final += atom.svg();
                i += 1;

        final += footer;

        return final;

    # open and parse sdf files into atoms and bonds into new molecule
    def parse(self, file):
        line_num = -1;
        # skip first three lines of file (title + blank lines)
        file.readline();
        file.readline();
        file.readline();

        # split each line into data elements by spaces
        for line in file:
            data = line.split();

            #check for end of file and exit if reached
            if data[0] == "M" and data[1] == "END":
                break;

            #get num atoms and num bonds from first line
            if line_num == -1: 
                atom_num = int(data[0]);
                bond_num = int(data[1]);
                line_num += 1;
                continue;

            #handle atoms and bonds separately
            if line_num < atom_num:
                x = float(data[0]);
                y = float(data[1]);
                z = float(data[2]);
                element = data[3];
                self.append_atom(element, x, y, z);
            elif line_num <= (atom_num + bond_num):
                a1 = int(data[0]) - 1; #PB: -1s new additions from A3 pt. 0
                a2 = int(data[1]) - 1;
                epairs = int(data[2]);
                self.append_bond(a1, a2, epairs);
            line_num += 1;

            #check if bad sdf
            if (self.atom_no < atom_num) or (self.bond_no < bond_num) or (atom_num == 0) or (bond_num == 0):
                print(f"Error!\n Atoms: {self.atom_no}, {atom_num}");
                print(f"Bonds: {self.bond_no}, {bond_num}");
                return False;
            return True;

# print outside of module for testing
if __name__ == "__main__":

    file_mol = Molecule();
    file = open("CID.sdf", "r");
    print();
    file_mol.parse(file);
    file.close();

    print("**Parse check**\n");
    print(file_mol); #prints bond and atom nos
    for i in range(file_mol.atom_no): 
        file_atom = Atom(file_mol.get_atom(i));
        print(file_atom);
        print(file_atom.svg());

    print();
    for j in range(file_mol.bond_no):
        file_bond = Bond(file_mol.get_bond(j));
        print(file_bond);
        print(file_bond.svg());
    print();

    # write to svg file for viewing
    w_file = open("output.svg", "w");
    file_mol.sort();
    print(file_mol.svg()); #DB
    w_file.write(file_mol.svg());
    w_file.close();
