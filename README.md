Setup checkfileForcpr
-------------------------------------------------------------------------------

...$ cd /usr/lib/ckan/default/src/ckan/  
...$ . /usr/lib/ckan/default/bin/activate  
...$ paster --plugin=ckan create -t ckanext ckanext-CKANValidator  
...$ cd CKANValidator/  
...$ python setup.py develop  
  
...$ sudo nano /etc/ckan/default/production.ini  
	ckan.plugins = ... setstateforpendingvalidation  
	ckan.auth.create_unowned_dataset = False  
	ckan.auth.create_dataset_if_not_in_organization = False  
	ckan.setstateforpendingvalidation.user = CKANValidator  
...$ sudo service apache2 restart  
...$ paster sysadmin add CKANValidator -c /etc/ckan/default/production.ini  
  
postgres=# create database oddk_default;  
  
postgres=# CREATE TABLE ckanvalidators (  
               id     text PRIMARY KEY,  
               public boolean  
           );  
           
postgres=# grant insert on ckanvalidators to ckan_default;  
  
postgres=# grant update on ckanvalidators to ckan_default;  
postgres=# grant select on ckanvalidators to ckan_default;  
  
psycopg2 (http://initd.org/psycopg/docs/install.html#install-from-package)  
-----------------
...$ sudo apt-get update  
...$ sudo apt-get install python-psycopg2  

pdfminer
-----------------
download source (https://github.com/euske/pdfminer/)  
...$ cd pdfminer  
...$ sudo python setup.py install  
TEST ...$ pdf2txt.py samples/simple1.pdf  
  
xlrd  
-----------------
http://installion.co.uk/ubuntu/saucy/universe/p/python-xlrd/install/index.html  
...$ sudo apt-get install python-xlrd  
  
python-odf  
-----------------
download source (https://pypi.python.org/pypi/odfpy)  
...$ cd odfpy  
...$ python setup.py build  
...$ sudo python setup.py install  
