# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "aztst40"
__date__ = "$16-03-2015 15:19:43$"
__author__ = 'toan'

from fileinput import filename
import os.path
import psycopg2

import os
#import fnmatch
#import time 
#from datetime import timedelta
import datetime
import re
import zipfile
import layout_scanner
import xlrd
from ODSReader import *
from pprint import pprint
import sys
#import rtf2xml
import smtplib
import csv
import zipfile
import subprocess
import logging

import urllib2
import urllib
import json
import pprint
from datetime import datetime, timedelta
import shutil
import ConfigParser

g_not_readable = '.dwg, .mdb, .zip,.wk3'
g_sender = 'dkaarhuskommuneodaa@gmail.com'
g_toEmail = ''
g_error_template = "Error ==> Exception %s"
g_ignore = ""

def readIniFile():
    config = ConfigParser.RawConfigParser()
    config.read('dkaarhuskommuneodaa.ini')

    global g_password
    global g_authorization
    global g_link
    global g_ignore
    global g_toEmail
    g_password=config.get('checkfileforcpr', 'Password')
    g_authorization=config.get('checkfileforcpr', 'Authorization')
    g_link=config.get('checkfileforcpr', 'Link')    
    g_ignore=config.get('checkfileforcpr','ignore')
    g_toEmail=config.get('checkfileforcpr','toEmail')

def changePackage(id):
    connectString = """dbname='oddk_default' user='ckan_default' host='localhost' password='%s'""" % g_password
    conn = psycopg2.connect(connectString)
    cur = conn.cursor()
    #CKANValidators is set in plugin.py.
    #public=true if the user has set the dataset to private.
    #If the user has set the private to true, then do not chech this dataset.
    sql="""
    SELECT count(*) from CKANValidators where id='%s' and public=true;
    """ % id
    cur.execute(sql)
    rows = cur.fetchall()
    if rows[0][0]>0:     
    	#Jump out if the dataset is set to private by user,
	return

    dataset_dict = {
        'id': '',
    }
    dataset_dict["id"]=id
    
    data_string = urllib.quote(json.dumps(dataset_dict))

    request = urllib2.Request(
        'http://' + g_link + '/api/action/package_show')
    request.add_header('Authorization', g_authorization)

    response = urllib2.urlopen(request, data_string)
    assert response.code == 200
    response_dict = json.loads(response.read())
    assert response_dict['success'] is True

    dataset_dict = response_dict['result']
    dataset_dict["private"]="false"

    # Put the details of the dataset we're going to create into a dict.
    
    # Use the json module to dump the dictionary to a string for posting.
    data_string = urllib.quote(json.dumps(dataset_dict))

    # We'll use the package_create function to create a new dataset.
    request = urllib2.Request(
        'http://' + g_link + '/api/action/package_update')

    # Creating a dataset requires an authorization header.
    # Replace *** with your API key, from your user account on the CKAN site
    # that you're creating the dataset on.
    request.add_header('Authorization', g_authorization)

    # Make the HTTP request.
    response = urllib2.urlopen(request, data_string)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    assert response_dict['success'] is True

    # package_create returns the created package as its result.
    created_package = response_dict['result']

def send_mail(to,subject, _body):        
    body = _body.replace('\n', '\r\n')
    #print "sendeing mail"

    # Prepare actual message
    message = """From: %s
To: %s
Subject: %s

%s
""" % (g_sender,to,subject,body)
    try:
        smtpObj = smtplib.SMTP('localhost')        
	to=to.split(',')
        smtpObj.sendmail(g_sender, to, message)
    except Exception as e:
        logging.error('Error: unable to send email. %s ',e)
        #sys.exit(1)

def ckeckfileforcpr(newfile,extension):
    r = '\d{5,6}[- ]\d{4} '
    reg = re.compile(r)

    fileName, fileExtension = os.path.splitext(newfile)
    try:
	file_size = os.path.getsize(newfile)
            
        filetext = " "
        loglines = ""
        abstract = ""
        count_cpr = 0
    
    #logfile.write("\nChecking: %s size: %d" % (newfile, len(filetext)))
    #print " file: %s ext %s" % (fileName, fileExtension)

    #collecting ext, just fore info in logfile
    #if fileExtension not in file_ext:
    #    file_ext += ' ' + fileExtension

    # there are some types we know that we can't extract
        error_in_read = ""
        if extension in g_not_readable:
	    filetext=None	    
        if extension == '.pdf':
            error_in_read, filetext = process_pdf(newfile)
        elif extension == '.docx':
            #Check m$ docc
            error_in_read, filetext  = process_docx(newfile)
        elif extension == '.doc':
            #Check m$ doc
            error_in_read, filetext  = process_doc(newfile)
        elif extension == '.odt':
            #open office writer
            error_in_read, filetext  = process_odt(newfile)
        elif extension == '.xlsx':
            #Check m$ excel
            error_in_read, filetext  = process_xlsx(newfile)
        elif extension == '.rtf':
            #continue
            error_in_read, filetext  = process_rtf(newfile)
            #print filetext
        elif extension == '.xls':
            #Check m$ old excel
            error_in_read, filetext = process_xls(newfile)
        elif extension == '.ods':
            #open office calc
            if file_size > 4000000:               
                logfile.write("\n\n ==> NB NB File %s is too large (%d byte) to auto control\n" % (newfile, file_size))
                abstract += "\n ==>  File %s is too large (%d byte) to auto control" % (newfile, file_size)
            else:
                error_in_read, filetext  = process_ods(newfile)
        elif extension == '.zip':
            #not in use cfr. g_not_readable
            filetext = process_zip(newfile)            
        else:  # all other filetypes and default handling        
            inf = open(newfile, "r")
            filetext = inf.read()        
            inf.close()
 
        # if content in "error_in_read" we have an error
        if len(error_in_read) > 5:
            #logfile.write("\nNB NB == > Can not read : %s size: %d" % (newfile, len(filetext)) )
            abstract += "\n == > Can not read : %s size: %d %s " % (newfile, len(filetext), error_in_read)            
            error_in_read = ""
         
            # now we can check for cpr
        if filetext is not None:            
            fundet = reg.findall(filetext)            
	    cprFound=""
            for f in fundet:                
		checkity = f[:6].strip(' ').strip('-')		
                try:
                    datetime.datetime.strptime(checkity, '%d%m%y')
                    pos=filetext.index(f)
                    start=pos-25
                    if start<0:
                        start=0
                    end=pos+25
                    if end>len(filetext):
                        end=len(filetext)
                    cprFound+="char:" + str(pos) + " cpr:" + f[:11] + " substr:" + filetext[start:end] + "\n"                    
                except ValueError as e:
		    print str(e)
                    pass
            return cprFound
        else:
            return "Kan ikke checke filetype."
    except os.error as ose:
	logging.error(str(ose))

def process_pdf(path):
    """Extract text from PDF file using PDFMiner with whitespace inatact."""
    str = ""
    try:
        pages = layout_scanner.get_pages(path)        
        i = 0
        l = len(pages)
        while i < l:            
            str += pages[i]
            i += 1
    except Exception, e:
        return g_error_template % e, ""        
    
    return "", str


def process_docx(newfile):

    with open(newfile) as f:
        unzip = zipfile.ZipFile(f)
        xml_content = unzip.read('word/document.xml')

    return "", xml_content


def process_doc(newfile):
    proc = subprocess.Popen(['/usr/bin/antiword', newfile], stdout=subprocess.PIPE)

 #    error handling missing
    contents = ""
    for line in iter(proc.stdout.readline, ''):
        contents += line.rstrip()

    return "", contents


def process(newfile):
    print "in process: %s " % filename

def process_xls(newfile):
    try:
        book = xlrd.open_workbook(newfile)
        contents = ""
        sheets = book.sheet_names()
    except Exception, e:
        return g_error_template % e, ""
    try:
        for sheet_name in sheets:
            worksheet = book.sheet_by_name(sheet_name)
            for row_index in xrange(worksheet.nrows):
                for coll_index in xrange ( worksheet.ncols):
                    ctype = worksheet.cell_type(row_index, coll_index)
                    if ctype == xlrd.XL_CELL_EMPTY or ctype == xlrd.XL_CELL_BLANK:
                        continue

                    if ctype == xlrd.XL_CELL_TEXT:
                        contents += worksheet.cell_value(row_index, coll_index).encode('utf-8') + " "
                    else:
                        contents += str(worksheet.cell_value(row_index, coll_index)  ) + " "
    except Exception, e:
        print " except  " + repr(e)
        return g_error_template % e, ""
    return "", contents

def process_xlsx(newfile):

    error = ""
    print "start process_xlsx file %s " % newfile
    try:

        try:
            wb = xlrd.open_workbook(newfile,  ragged_rows=True)
           #wb = xlrd.open_workbook(newfile)

        except Exception, e:
            print "===> 01. Execp: %s " % e
            return g_error_template % e, ""

        print wb.biff_version, wb.codepage, wb.encoding
        #print "after xlrd.open_workbook "

        sheet_name = wb._sheet_names
       # print ','.join(sheet_name)
        print "ready to go"
        with open(g_temp_csv_file, 'w') as csv_file:

            wr = csv.writer(csv_file, quoting=0 )

            #print "---- runningh all the rows ----"
            for name in sheet_name:
                #print "process %s" % name
                sh = wb.sheet_by_name(name)

                #print "Before row process process_xlsx"
                row = " "
                try:
                    for rownum in xrange(sh.nrows):

                       # rw = sh.row_values(rownum)
                        row = fix(sh.row_values(rownum))
                        # row = ''.join(unicode(str(e), errors='ignore') for e in rw)
                        #wr.writerow(sh.row_values(rownum).unicodeData.encode('ascii', 'ignore'))
                        wr.writerow(row)
                except Exception, e:
                    #row = ''.join(row).encode(encoding='utf-8', error='ignore')
                    print "except 002"
                    print "Execp 002: %s  %s" % (e, row)


            csv_file.close()

        with open(g_temp_csv_file, 'r') as tfile:
            contents = tfile.read()
            tfile.close()
        return " ", contents.strip('\n')

    except Exception, e:
        print "Execp 2: %s " % e
        return g_error_template % e, ""

"""
process OpenDocument Spreadsheet
"""
def process_ods(newfile, reg=None):

    doc = ODSReader(newfile)

    #print doc.SHEETS
    #print ','.join(doc.SHEEexceptTS)
    #print doc.SHEETS.keys()

    contents = ""
    if reg <> None:
        for key in doc.SHEETS.keys():
            thisrow =  ' '.join(' '.join(u''.join(el) for el in list) for list in doc.SHEETS[key])
            contents += u''.join(reg.findall(thisrow) )
    else:
        for key in doc.SHEETS.keys():
            #print doc.SHEETS[key]
            #contents += u' '.join(" ".join(map(str, l)).decode('ascii', 'ignore') for l in doc.SHEETS[key])
            contents += '\n'.join('\t'.join(u''.join(el) for el in list) for list in doc.SHEETS[key])
            #print contents
            #l =  doc.SHEETS[key]
            #print type(l)
    return "", contents

##
## process OpenDocument writer
##

def process_odt(newfile):
    return " ", odf.opendocument.load(newfile).xml()

def process_zip(newfile):
    return None

def logCaurusel(number,actual,back):
    now=datetime.now()
    try:
        file=datetime.fromtimestamp(os.path.getatime(actual + '.log')) + timedelta(days=1)
    except OSError as e:
        return
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    if now>file:
        for i in range (number,0,-1):
            sIdx="{0:02d}".format(i)
            sIdxPe="{0:02d}".format(i+1)

            fromFile=back + sIdx + '.log'
            toFile=back + sIdxPe + '.log'

            if os.path.isfile(fromFile):
	       if os.path.getsize(fromFile)>0:	
                   shutil.copy2(fromFile, toFile)

        fromFile=actual + '.log'
        toFile=back + '01.log'
        if os.path.isfile(fromFile):
            shutil.copy2(fromFile, toFile)
            os.remove(fromFile)

def checkForCPR():      
    connectString = """dbname='ckan_default' user='ckan_default' host='localhost' password='%s'""" % g_password  
    con = psycopg2.connect(connectString)
    cur = con.cursor()

	#Find all the dataset which is private.
    cur.execute("""SELECT DISTINCT R.ID,P.ID,P.private,R.url,PU.fullname,PU.email,P.name
                FROM Package P
                JOIN Package_Revision PR ON P.ID = PR.ID  
                JOIN Resource R ON R.package_id = PR.ID
                JOIN public.user PU ON PU.id=P.creator_user_id
                WHERE P.Private = True
                AND PR.State = 'active'
                AND PR.Private = False
                AND R.state<>'deleted';""")   
    rows=cur.fetchall()
    con.close
    ret=""
    for row in rows:
		#Path to filestore
        directory = os.path.join("/var/lib/ckan/default/resources/",
                                 row[0][0:3], row[0][3:6],row[0][6:])
		#Check files for CPR
        cpr=ckeckfileforcpr(directory,row[3][len(row[3])-4:])
        if cpr is not None:
            if len(cpr)>0 and g_ignore.find(row[0])==-1:
			    #If CPR is found and must not be ignored write to the ret.
                ret="packageid:" + row[1] + " fullname:" + row[4] + " email:" + row[5] + " url:" + row[3] + " resourceid:" + row[0] + " cpr=" + cpr + "\n" + ret   
    for row in rows:                
        if ret.find(row[1])==-1:    
            #If package_id not present in ret, so sets dataset to public.		
            changePackage(row[1])
    if len(ret)>0:
	    #If CPR is found, send mail and write to log.
        logging.error(ret)
        send_mail(g_toEmail,"Found cpr",ret)
    logCaurusel(9,'/home/deploy/bin_script/checkFileForCPR/checkfileforcpr','/home/deploy/bin_script/checkFileForCPR/checkfileforcpr')

def main():
    readIniFile()
    checkForCPR()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename='/home/deploy/bin_script/checkFileForCPR/checkfileforcpr.log', level=logging.ERROR)
#    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename='/home/deploy/bin_script/checkFileForCPR/checkfileforcpr.log', level=logging.INFO)
    logging.debug("Started")
    main()    
    logging.debug("Finish")
    

