#!/usr/bin/python3

import MolDisplay;
from MolDisplay import Molecule;
from MolDisplay import Atom;
from MolDisplay import Bond;
import sqlite3;
import os;

# transfers data from files in local directory into the database tables
class Database:

    # connect database to local file molecules.db
    def __init__(self, reset=False):
        # for testing only; resets database if it exists
        if reset == True:
            if os.path.exists("molecules.db"):
                os.remove("molecules.db");

        # create database file if it doesn't exist and connect to it
        self.conn = sqlite3.connect("molecules.db");   

    # create tables (if they don't exist) for atoms, bonds, and molecules, their relations, and elements
    def create_tables(self):

        # Elements
        self.conn.execute("""CREATE TABLE 
                IF NOT EXISTS Elements
                  (ELEMENT_NO   INTEGER         NOT NULL,
                   ELEMENT_CODE VARCHAR(3)      NOT NULL,
                   ELEMENT_NAME VARCHAR(32)     NOT NULL,
                   COLOUR1      CHAR(6)         NOT NULL,
                   COLOUR2      CHAR(6)         NOT NULL,
                   COLOUR3      CHAR(6)         NOT NULL,
                   RADIUS       DECIMAL(3)      NOT NULL,
                   PRIMARY KEY (ELEMENT_CODE));""");

        # Atoms
        self.conn.execute("""CREATE TABLE 
                IF NOT EXISTS Atoms
                  (ATOM_ID      INTEGER         NOT NULL    PRIMARY KEY   AUTOINCREMENT,
                   ELEMENT_CODE VARCHAR(3)      NOT NULL,
                   X            DECIMAL(7,4)    NOT NULL,
                   Y            DECIMAL(7,4)    NOT NULL,
                   Z            DECIMAL(7,4)    NOT NULL,
                   FOREIGN KEY (ELEMENT_CODE) REFERENCES Elements);""");

        # Bonds
        self.conn.execute("""CREATE TABLE
                IF NOT EXISTS Bonds
                  (BOND_ID      INTEGER         NOT NULL    PRIMARY KEY   AUTOINCREMENT,
                   A1           INTEGER         NOT NULL,
                   A2           INTEGER         NOT NULL,
                   EPAIRS       INTEGER         NOT NULL);""");

        # Molecules
        self.conn.execute("""CREATE TABLE 
                IF NOT EXISTS Molecules
                  (MOLECULE_ID  INTEGER         NOT NULL    PRIMARY KEY   AUTOINCREMENT,
                   NAME         TEXT            NOT NULL    UNIQUE);""");

        # MoleculeAtom
        self.conn.execute("""CREATE TABLE
                IF NOT EXISTS MoleculeAtom
                  (MOLECULE_ID  INTEGER         NOT NULL,
                   ATOM_ID      INTEGER         NOT NULL,
                   PRIMARY KEY (MOLECULE_ID,ATOM_ID),
                   FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                   FOREIGN KEY (ATOM_ID) REFERENCES Atoms);""");

        # MoleculeBond
        self.conn.execute("""CREATE TABLE 
                IF NOT EXISTS MoleculeBond
                  (MOLECULE_ID  INTEGER         NOT NULL,
                   BOND_ID      INTEGER         NOT NULL,
                   PRIMARY KEY (MOLECULE_ID,BOND_ID),
                   FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                   FOREIGN KEY (BOND_ID) REFERENCES Bonds);""");

    # set values in table to values in tuple values via indexing
    def __setitem__(self, table, values):
        self.conn.execute(f"""INSERT INTO {table} VALUES {str(values)};""");
        self.conn.commit();

    # add attributes of atom (Atom object) to its table, add link to MolAtoms table
    def add_atom (self, molname, atom):

        # add values to atoms table
        self.conn.execute(f"""INSERT INTO Atoms (ELEMENT_CODE, X, Y, Z)
                    VALUES ('{atom.atom.element}', {atom.atom.x}, {atom.atom.y}, {atom.atom.z});""");
        self.conn.commit();
        
        # add values to MolAtoms table
        mol_id = (self.conn.execute(f"""SELECT Molecules.MOLECULE_ID
                            FROM Molecules 
                            WHERE Molecules.NAME = '{molname}';""").fetchone())[0];
        
        # get most recent atom id (should be maximum)
        atom_id = (self.conn.execute(f"""SELECT MAX(ATOM_ID) 
                            FROM Atoms;""").fetchone())[0];
        
        self.conn.execute(f"""INSERT INTO MoleculeAtom (MOLECULE_ID, ATOM_ID)
                   VALUES ({mol_id}, {atom_id});""");
        self.conn.commit();

    # add attributes of bond (Bond object) to its table, add link to MolBond table
    def add_bond (self, molname, bond):

        # add values to bonds table
        self.conn.execute(f"""INSERT INTO Bonds (A1, A2, EPAIRS)
                    VALUES ({bond.bond.a1}, {bond.bond.a2}, {bond.bond.epairs});""");
        self.conn.commit();
        
        # add values to MolBond table
        mol_id = (self.conn.execute(f"""SELECT Molecules.MOLECULE_ID
                            FROM Molecules 
                            WHERE Molecules.NAME = '{molname}';""").fetchone())[0];
        
        # get most recent bond id (should be maximum)
        bond_id = (self.conn.execute(f"""SELECT MAX(BOND_ID) 
                            FROM Bonds""").fetchone())[0];
        
        self.conn.execute(f"""INSERT INTO MoleculeBond (MOLECULE_ID, BOND_ID)
                    VALUES ({mol_id}, {bond_id});""");
        self.conn.commit();

    # create molecule from fp, add its atoms and bonds, add to database
    def add_molecule (self, name, fp):
        mol = Molecule();
        valid = mol.parse(fp);
        if not valid:
            return False;
    
        self.conn.execute(f"""INSERT INTO Molecules (NAME)
                    VALUES ('{name}');""");
        self.conn.commit();
        #iterate through and fetch all atoms and bonds, add to database
        for i in range(mol.atom_no): 
            atom = Atom(mol.get_atom(i));
            self.add_atom(name, atom);
        for j in range(mol.bond_no):
            bond = Bond(mol.get_bond(j));
            self.add_bond(name, bond);
        return True;

    # initialize one Molecule object, select and join atoms and bonds to molecule
    def load_mol (self, name):
        mol = Molecule();

        # getting the atoms - selects all cols from all atoms
        atom_info = (self.conn.execute(f"""SELECT * FROM Atoms 
                        INNER JOIN MoleculeAtom
                            ON Atoms.ATOM_ID = MoleculeAtom.ATOM_ID
                        INNER JOIN Molecules
                            ON MoleculeAtom.MOLECULE_ID = Molecules.MOLECULE_ID
                            WHERE Molecules.NAME = '{name}';""")).fetchall();

        # append atoms to molecule
        for atom in atom_info:
            mol.append_atom(atom[1], atom[2], atom[3], atom[4]);
        
        # getting bonds (all columns)
        bond_info = (self.conn.execute(f"""SELECT * FROM Bonds
                        INNER JOIN MoleculeBond
                            ON Bonds.BOND_ID = MoleculeBond.BOND_ID
                        INNER JOIN Molecules
                            ON MoleculeBond.MOLECULE_ID = Molecules.MOLECULE_ID
                            WHERE Molecules.NAME = '{name}';""")).fetchall();
        
        # append bonds to molecule
        for bond in bond_info:
            mol.append_bond(bond[1], bond[2], bond[3]);

        return mol;

    # return dict mapping ELEMENT_CODE values to RADIUS values
    def radius (self):
        rad_dict = {};

        element_info = (self.conn.execute("""SELECT ELEMENT_CODE, RADIUS
                        FROM Elements;""")).fetchall();
        
        # make the dictionary
        for element in element_info:
            rad_dict[element[0]] = element[1];

        return rad_dict;

    # return dict mapping ELEMENT_CODE values to ELEMENT_NAME values
    def element_name (self):
        name_dict = {};

        element_info = (self.conn.execute("""SELECT ELEMENT_CODE, ELEMENT_NAME
                        FROM Elements;""")).fetchall();
        
        # make the dictionary
        for element in element_info:
            name_dict[element[0]] = element[1];

        return name_dict;

    # assemble new svg with values from element table
    def radial_gradients (self):
        radialGradientSVG = "";
        elements = self.conn.execute("""SELECT * FROM Elements;""").fetchall();

        for el in elements:
            radialGradientSVG += """
            <radialGradient id="%s" cx="-50%%" cy="-50%%" r="220%%" fx="20%%" fy="20%%">
            <stop offset="0%%" stop-color="#%s"/>
            <stop offset="50%%" stop-color="#%s"/>
            <stop offset="100%%" stop-color="#%s"/>
            </radialGradient>""" % (el[2], el[3], el[4], el[5]);

        return radialGradientSVG;


# testing code
if __name__ == "__main__":

    # Part 1 testing
    # db = Database(reset=True);
    # db.create_tables();
    # db['Elements'] = (1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25);
    # db['Elements'] = (6, 'C', 'Carbon', '808080', '010101', '000000', 40);
    # db['Elements'] = (7, 'N', 'Nitrogen', '0000FF', '000005', '000002', 40);
    # db['Elements'] = (8, 'O', 'Oxygen', 'FF0000', '050000', '020000', 40);
    # fp = open('water.sdf');
    # db.add_molecule('Water', fp);
    # fp = open('caffeine.sdf');
    # db.add_molecule('Caffeine', fp);
    # fp = open('CID.sdf');
    # db.add_molecule('Isopentanol', fp);
    # # display tables
    # print( db.conn.execute( "SELECT * FROM Elements;" ).fetchall() );
    # print( db.conn.execute( "SELECT * FROM Molecules;" ).fetchall() );
    # print( db.conn.execute( "SELECT * FROM Atoms;" ).fetchall() );
    # print( db.conn.execute( "SELECT * FROM Bonds;" ).fetchall() );
    # print( db.conn.execute( "SELECT * FROM MoleculeAtom;" ).fetchall() );
    # print( db.conn.execute( "SELECT * FROM MoleculeBond;" ).fetchall() );
    # print();

    # Part 2 testing
    db = Database(reset=False); # or use default
    MolDisplay.radius = db.radius();
    MolDisplay.element_name = db.element_name();
    MolDisplay.header += db.radial_gradients();
    for molecule in [ 'Water', 'Caffeine', 'Isopentanol' ]:
        mol = db.load_mol( molecule );
        mol.sort();
        fp = open( molecule + ".svg", "w" );
        fp.write( mol.svg() );
        fp.close();
