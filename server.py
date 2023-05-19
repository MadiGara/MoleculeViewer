#!/usr/bin/python3

import sys;
import io;
import urllib;
import MolDisplay;
from MolDisplay import Molecule;
import molsql;
import urllib;
import cgi;
from molsql import Database;
from http.server import BaseHTTPRequestHandler, HTTPServer;

public_files = ['/molecule.html', '/molecule.js', '/elements.html', '/elements.js', '/display.html', 'display.js', '/style.css'];
db_files = ['/Elements', '/Molecules'];

db = Database(reset=False);
db.create_tables();

# make subclass of base handler to implement do_get and do_post
class Handler (BaseHTTPRequestHandler):

    # read one string
    def get_string(self, fptr):
        string = "";
        for line in fptr.readlines():
            string += line;
        return string;

    # returns header for main display page
    def get_header(self, filename):
        return f"""<head>
                <title>Molecule Display</title>
                <meta charset="UTF-8">
                <link rel="stylesheet" href="style.css">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.3/jquery.min.js"></script>
                <script src="{filename}.js"></script>
            </head>"""

    # updates python dictionaries (radius and element_name from moldisplay) when they're changed
    def update_dictionaries(self):
        MolDisplay.radius = db.radius();
        MolDisplay.element_name = db.element_name();
    
        MolDisplay.header = """<svg version="1.1" width="1000" height="1000" xmlns="http://www.w3.org/2000/svg">
            """ + db.radial_gradients() + """
            <radialGradient id="Default" cx="-50%" cy="-50%" r="220%" fx="20%" fy="20%">
                <stop offset="0%" stop-color="#00DDBB"/>
                <stop offset="50%" stop-color="#001100"/>
                <stop offset="100%" stop-color="#%000000"/>
            </radialGradient>""";
    
        # add defaults for missing entries in elements
        final = db.conn.execute("SELECT DISTINCT ELEMENT_CODE FROM Atoms").fetchall();
        for item in final:
            if (item[0] in MolDisplay.element_name) == False:
                MolDisplay.element_name[item[0]] = "Unnamed";
            if (item[0] in MolDisplay.radius) == False:
                MolDisplay.radius[item[0]] = 40;
    
    # send responses for error handlers
    def error_response(self, error_no, message):
        self.send_response(error_no);
        self.end_headers();
        self.wfile.write(bytes(message, "utf-8"));

    # get handler for different front-end pages
    def get_response(self, filename):
        fptr = open(f"{filename}", "r");
        body = self.get_string(fptr);
        fptr.close();

        # get file name and extension
        file_details = filename.split('.');
        content_type = "";

        if file_details[1] == 'html':
            header = self.get_header(file_details[0]);
            # format body to send as html string to the browser
            body2 = f"<!DOCTYPE html>{header}{body}</html>";
            body = body2;
            content_type = "text/html";

        elif file_details[1] == 'js':
            content_type = "application/javascript";

        elif file_details[1] == 'css':
            content_type = "text/css";

        self.send_response(200);
        self.send_header("Content-type", content_type);
        self.send_header("Content-length", len(body));
        self.end_headers();
        self.wfile.write(bytes(body, "utf-8"));

    # gets count atoms or bonds from MoleculeAtom or MoleculeBond for display
    def get_count(self, mol_id, column):
        return db.conn.execute(f"""SELECT COUNT({column.upper()}_ID) FROM Molecule{column}
                                    WHERE MOLECULE_ID = {mol_id};""").fetchone()[0];

    # gets table and formats it in html for display
    def get_table_response(self, table):
        rows = db.conn.execute(f"SELECT * FROM {table};").fetchall();
        html_string = "";

        if table == "Elements":
            # format: db['Elements'] = (1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25)
            for item in rows:
                #tr = table row, td = table data (for that row), put elements in divs, style tags set colour preview
                html_string += f"""<tr id="el_{item[1]}">
                                <td>{item[0]}</td>
                                <td>{item[1]}</td>
                                <td>{item[2]}</td>
                                <td><div><div class="colour_box" style="background-color: #{item[3]};"></div><div>{item[3]}</div></div></td>
                                <td><div><div class="colour_box" style="background-color: #{item[4]};"></div><div>{item[4]}</div></div></td>
                                <td><div><div class="colour_box" style="background-color: #{item[5]};"></div><div>{item[5]}</div></div></td>
                                <td>{item[6]}</td>

                                <td><button id="del_{item[1]}" onclick="deleteElement('{item[1]}')">Delete</button></td>
                                </tr>""";

        if table == "Molecules":
            # id is 0, name is 1
            for item in rows:
                # get atom_no and bond_no to display
                atom_no = self.get_count(item[0], "Atom");
                bond_no = self.get_count(item[0], "Bond");
                # combine into string, use link to display the molecule
                html_string += f"""<tr id="mol_{item[1]}">
                                <td class="left">{item[1]}</td>
                                <td>{atom_no}</td>
                                <td>{bond_no}</td>
                                <td><a href="/display/{item[1]}">Display</a></td>
                                </tr>""";

        self.send_response(200);
        self.send_header("Content-type", "text/html");
        self.send_header("Content-length", len(html_string));
        self.end_headers();
        self.wfile.write(bytes(html_string, "utf-8"));

    # check if input is valid hexadecimal (base 16 integer)
    def check_hex (self, string):
        hex = "0x" + string;
        try:
            int(hex, 16);
            return True;
        except ValueError:
            return False;

    # only valid names are alphanumeric, - or _
    def check_name(self, name):
        for char in name:
            if (char.isalnum() or (char == '-') or (char == '_')) == False:
                return False;
        return True;

    # check for user attempting to enter sql commands via forms
    def check_sql(self, string):
        string = string.lower()
        suspects = ['select', 'drop', 'update', 'insert', 'delete', 'set', 'where', ';', '(', ')'];
        for suspect in suspects:
            if suspect in string:
                return False;
        return True;

    # error checking for all user form inputs
    def validate_input(self, post_dict):
        valid = True;
        message = "Invalid: \n";
        keys = list(post_dict.keys());
    
        # check if all required keys (el num, code, name) are included
        for key in ['element_no', 'element_code', 'element_name']:
            if (key in keys) == False:
                valid = False;
                message += "Element number, code, and name are required.\n";
                return (valid, message);

        # check if element number a positive integer and valid el num
        if ((post_dict['element_no'][0].isnumeric() == False) or
                (int(post_dict['element_no'][0]) < 0) or (int(post_dict['element_no'][0]) > 118)):
            valid = False;
            message += "Element number - must be a positive value and valid element number.\n";

        # check element code: must be 2 characters max
        if ((len(post_dict['element_code'][0]) <= 0) or
            (len(post_dict['element_code'][0]) > 2) or
                (post_dict['element_code'][0].isalpha() == False)):
            valid = False;
            message += "Element code - must be 1 or 2 alphabetical characters\n";
    
        # name can only be alphanumeric, dash or underline
        alpha_check = post_dict['element_name'][0].isalpha();
        valid_name = self.check_name(post_dict['element_name'][0]);
        if valid_name == False:
            valid = False;
            message += "Element name - must be alphanumberic, a hyphen, or a dash.\n";
    
        # check inputs that can be defaulted in order, as update happens in order #

        # radius can only be numeric and > 0
        if 'radius' in keys:
            if ((post_dict['radius'][0].isnumeric() == False) or
                    (int(post_dict['radius'][0]) < 1)):
                valid = False;
                message += "Radius - must be a positive integer.\n";
        else:
            post_dict.update({'radius': ['40']});
    
        # colours can only be hexadecimal (6 digits, alphanumeric)
        if 'colour1' in keys:
            if ((len(post_dict['colour1'][0]) != 6) or
                (post_dict['colour1'][0].isalnum() == False) or
                    (self.check_hex(post_dict['colour1'][0]) == False)):
                valid = False;
                message += "Colour 1 - must be hexadecimal.å\n";
        else:
            post_dict.update({'colour1': ['FFFFFF']});
    
        if 'colour2' in keys:
            if ((len(post_dict['colour2'][0]) != 6) or
                (post_dict['colour2'][0].isalnum() == False) or
                    (self.check_hex(post_dict['colour2'][0]) == False)):
                valid = False;
                message += "Colour 2 - must be hexadecimal.\n";
        else:
            post_dict.update({'colour2': ['050505']});
    
        if 'colour3' in keys:
            if ((len(post_dict['colour3'][0]) != 6) or
                (post_dict['colour3'][0].isalnum() == False) or
                    (self.check_hex(post_dict['colour3'][0]) == False)):
                valid = False;
                message += "Colour 3 - must be hexadecimal.\n";
        else:
            post_dict.update({'colour3': ['020202']});
    
        # check for potentially malicious input (modifies the sql) - numbers already handled above
        if ((not self.check_sql(post_dict['element_name'][0])) or
                (not self.check_sql(post_dict['colour1'][0])) or
                (not self.check_sql(post_dict['colour2'][0])) or
                (not self.check_sql(post_dict['colour3'][0]))):
            valid = False;
            message += "SQL command-like entries not permitted.\n";
    
        if valid:
            message = "Element added successfully.\n";
        return (valid, message);

    # format molecule dicitonary contents into html to pass to server for display
    def display_response(self, molecule):
        self.update_dictionaries();
        mol = db.load_mol(molecule);
        html_string = "";
    
        # dne error if molecule doesn't exist
        if mol.atom_no < 1:
            html_string = f"""<!DOCTYPE html><head><title>Molecule Viewer</title>
                            <meta charset="UTF-8"><link rel="stylesheet" href="style.css"></head>
                            <body>Error: Molecule {molecule} not found.</body></html>""";
    
            self.error_response(404, html_string);
    
        # follow molsql main to get svg
        else:
            mol.sort();
            svg = mol.svg();
            fptr = open("display.html");
            body = self.get_string(fptr);
            fptr.close();

            header = self.get_header("display");
            # molecule name is hidden in div container with molecule svg
            html_string = f"""<!DOCTYPE html>{header}
                <body>{body}
                <p><input type="hidden" value="{molecule}" id="mol_name" /></p>
                <div id="molecule">{svg}</div>
                </body></html>""";

            self.send_response(200);
            self.send_header("Content-type", "text/html");
            self.send_header("Content-length", len(html_string));
            self.end_headers();
            self.wfile.write(bytes(html_string, "utf-8"));

    # give webform when valid path entered, else return error 404
    def do_GET(self): 

        # load pages that are established, elements home page by default
        if self.path == "/":
            self.get_response("elements.html");
        elif self.path in public_files:
            self.get_response(self.path[1:]);

        # load db pages that are established
        elif self.path in db_files:
            self.get_table_response(self.path[1:]);
        
        # display molecule
        elif "/display" in self.path:
            request = (self.path).split("/").pop();
            if (request == 'display.js') or (request == 'style.css'):
                self.get_response(request);
            # will be once db molecule display request entered (the mol num):
            elif (request.isalnum()):
                self.display_response(request);
            else:
                self.error_response(404, "404: Page not found");

        # nonexistant path
        else:
            self.error_response(404, "404: Page not found");

    # display molecule given in file uploaded to server through MolDisplay
    def do_POST(self):

        # upload sdf and transfer info to database
        if self.path == "/molecule.html":
            error_header = """<DOCTYPE! html><head>
                        <title>Molecule Viewer</title>
                        <meta charset="UTF-8">
                        <link rel="stylesheet" href="style.css"></head><body>"""
            error_footer = """</body></html>"""

            content_length = int(self.headers['Content-Length']);
            # https://stackoverflow.com/questions/31486618/cgi-parse-multipart-function-throws-typeerror-in-python-3
            ctype, pdict = cgi.parse_header(self.headers['content-type']);
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8");
            pdict['CONTENT-LENGTH'] = int(self.headers['content-length']);

            postvars = {};
            try:
                postvars = cgi.parse_multipart(self.rfile, pdict);
            except KeyError:
                valid = False;
                self.error_response(404, f"{error_header}<p>Invalid data</p>{error_footer}");

            # check all data is valid
            valid = True;
            message = "<p>Invalid data:</p>";

            if (len(postvars) != 2) or (len(postvars['sdffile'][0].decode('utf-8')) < 1) or (len(postvars['filename'][0]) < 1):
                valid = False;
                message += "<p> Name and file are both required to add the molecule.";
            else:
                if ((self.check_name(postvars['filename'][0])) == False):
                    valid = False;
                    message += "<p>Molecule names must only contain alphanumeric, - or _ characters.<\p>";
                if self.check_sql(postvars['filename'][0]) == False:
                    valid = False;
                    message += "<p>Possible dangerous input detected. Molecule not added.</p>";
        
            # parse valid files and add info to database
            if valid:
                try:
                    data = io.StringIO((postvars['sdffile'][0]).decode('utf-8'));
                    valid = db.add_molecule(postvars['filename'][0], data);
                    print(f"VALID: {valid}"); #TODO - none, not working
                except molsql.sqlite3.IntegrityError:
                    valid = False;
                    self.error_response(404, f"{error_header}<p>Error: Molecule name must be unique</p>{error_footer}");
                except IndexError:
                    valid = False;
                except ValueError:
                    valid = False;
                if not valid:
                    self.error_response(241, f"{error_header}<p>Invalid file or contents</p>{error_footer}");
            
            else:
                # placeholder for future code to avoid errors
                pass;
                self.error_response(241, f"{error_header}{message}{error_footer}");
        
            # for valid and complete file information
            if valid:
                self.get_response("molecule.html");
        
        # for rotating and displaying the rotation of the selected molecule
        elif self.path == "/rotate":
            content_length = int(self.headers['Content-Length']);
            pdict = urllib.parse.parse_qs(self.rfile.read(content_length).decode('utf-8'));
        
            # verify angle for rotation, axes, molecule name
            valid = True;
            message = "";

            # degrees
            if (((pdict['degrees'][0]).isnumeric() == False) or
                    (int (pdict['degrees'][0]) <= 0)):     #continues rotation if over 360
                valid = False;
                message += "Degrees must be integer values larger than 0.";

            # axis 
            if (pdict['axis'][0] in ('x', 'y', 'z')) == False:
                valid = False;
                message += "Axis must x, y, or z.";
        
            # molecule name
            if (self.check_name(pdict['mol_name'][0])) == False:
                valid = False;
                message += "Molecule names must only contain alphanumeric, - or _ characters.";
        
            # load molecule and send response to browser
            mol = None;
            if (valid or (not valid and (('degree' in message) and (not ('axis' in message)) and (not ('name' in message))))):
                mol = db.load_mol(pdict['mol_name'][0]);
            
            response = "";
            if ((valid == False) and (('degree' in message) and (not ('axis' in message)) and (not ('name' in message))) 
                    and (pdict['degrees'][0] == '0')):
                # 0 degree rotation, give back regular svg
                mol.sort();
                response = mol.svg();
            
            elif not valid:
                response = f"<p>{message}</p>";
            
            # rotate on specified axis the number of degrees entered - x axis by default (r = 0)
            else:
                degrees = [0, 0, 0];
                r = 0;
                # replace with ascii equivalents to be sure
                if ascii('y') == ascii(pdict['axis'][0]):
                    r = 1;
                elif ascii ('z') == ascii(pdict['axis'][0]):
                    r = 2;
                degrees[r] = int(pdict['degrees'][0]);
        
                # apply rotation function from moldisplay and generate svg as usual
                mol.rotate(degrees[0], degrees[1], degrees[2]);
                mol.sort();
                response = mol.svg();

            self.send_response(200);
            self.send_header("Content-type", "text/html");
            self.send_header("Content-Length", len(response));
            self.end_headers();
            self.wfile.write(bytes(response, "utf-8"));

        # for receiving a dictionary sent as a string from POSTed form
        elif self.path == "/Elements":
            content_length = int(self.headers['Content-Length']);
            body = self.rfile.read(content_length);
        
            # convert form content (js dictionary of posted variables) to python dictionary
            postvars = urllib.parse.parse_qs(body.decode('utf-8'));
            #DBS - prints dictionary to terminal
            print(postvars);

            validity = self.validate_input(postvars);
            message = validity[1];

            if validity[0] == True:
                num = postvars['element_no'][0];
                code = postvars['element_code'][0];
                name = postvars['element_name'][0];
                colour1 = postvars['colour1'][0];
                colour2 = postvars['colour2'][0];
                colour3 = postvars['colour3'][0];
                radius = postvars['radius'][0];
            
                # try adding element details to database
                try:
                    db['Elements'] = (num, code, name, colour1, colour2, colour3, radius);
                    db.conn.commit();
                except molsql.sqlite3.IntegrityError:
                    message = "Error: Unable to update database, element code must be unique.";
                self.send_response(200);
            
            else:
                # data could not be converted 
                self.send_response(241);
            
            self.send_header("Content-type", "text/html");
            self.send_header("Content-length", len(message));
            self.end_headers();
            self.wfile.write(bytes(message, "utf-8"));

        # for receiving name of element to delete
        elif self.path == "/delete_element":
            content_length = int(self.headers['Content-Length']);
            body = self.rfile.read(content_length);
        
            # convert form content (js dictionary of posted variables) to python dictionary
            postvars = urllib.parse.parse_qs(body.decode('utf-8'));
            # delete element based on code
            db.conn.execute(f"""DELETE FROM Elements
                            WHERE ELEMENT_CODE = '{postvars['code'][0]}';""");
            db.conn.commit();
            message = f"Element {postvars['code'][0]} deleted";

            self.send_response(200);
            self.send_header("Content-type", "text/html");
            self.send_header("Content-length", len(message));
            self.end_headers();
            self.wfile.write(bytes(message, "utf-8"));
                
        else:
            # nonexistant path
            self.send_response(404);
            self.end_headers();
            self.wfile.write(bytes("404: File not found", "utf-8"));

# take first command-line argument as port name, run server, close on ctrl+c
try:
    httpd = HTTPServer(('localhost', int(sys.argv[1])), Handler);
    httpd.serve_forever();
except KeyboardInterrupt:
    print();
    httpd.socket.close();
