import logging
import pylons.config as config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import psycopg2

log = logging.getLogger(__name__)

class SetStateForPendingValidationPlugin(plugins.SingletonPlugin):
   plugins.implements(plugins.IPackageController, inherit=True)

   def after_update(self, context, data_dict):
    log.debug("CKAN after_update context: %r", context)
    log.debug("CKAN after_update data_dict: %r", data_dict)
    
    # Check if the user is the one who is allowed to publish datasets
    userAllowedToPublish = config.get('ckan.setstateforpendingvalidation.user')
    if userAllowedToPublish == context['user']:
        log.info("User is allowed to publish dataset")
        return

    # Only do this for active datasets, and not ones in draft or deleted state
    # it is also not needed if the dataset is already private
    if 'state' not in data_dict or ( 'state' in data_dict and data_dict['state'] == 'active'):
        if 'private' not in data_dict or ( 'private' in data_dict and data_dict['private'] == False):
            data_dict['private'] = True
            log.info("CKAN to send %r: ", data_dict)
            toolkit.get_action('package_update')(context, data_dict)
            try:
               #If private=false when set public to false in CKANValidators.
               #This will be used in checkfileforspr.py to check if the user has entered private to true.
                conn = psycopg2.connect("dbname='oddk_default' user='ckan_default' host='localhost' password='xxxx'")
                cur = conn.cursor()
                sql="""
                    SELECT count(*) from CKANValidators where id='%s';
                """ % data_dict['id']
                cur.execute(sql)
                rows = cur.fetchall()
               if rows[0][0]>0:                         
                      sql="""
                      UPDATE CKANValidators
                      SET public=false
                      WHERE id='%s';
                      """ % data_dict['id']
                      cur.execute(sql)
                      conn.commit()
               else:              
                      sql="""
                      INSERT INTO CKANValidators VALUES('%s',false)
                      """ % data_dict['id']
                      cur.execute(sql)    
                      conn.commit()
            except psycopg2.DatabaseError, e:
                log.info("psycopg2.DatabaseError:" + str(e))
        else: #If private=true when set public to true in CKANValidators.
            try:
                #This will be used in checkfileforspr.py to check if the user has entered private to true.
                #public=true if the user has set the dataset to private.
                conn = psycopg2.connect("dbname='oddk_default' user='ckan_default' host='localhost' password='xxxx'")
                cur = conn.cursor()
                sql="""
                    SELECT count(*) from CKANValidators where id='%s';
                """ % data_dict['id']
                cur.execute(sql)
                rows = cur.fetchall()
                if rows[0][0]>0:                         
                    sql="""
                    UPDATE CKANValidators
                    SET public=true
                    WHERE id='%s';
                    """ % data_dict['id']
                    cur.execute(sql)
                    conn.commit()
                else:              
                    sql="""
                    INSERT INTO CKANValidators VALUES('%s',true)
                    """ % data_dict['id']
                    cur.execute(sql)    
                    conn.commit()
            except psycopg2.DatabaseError, e:
                log.info("psycopg2.DatabaseError:" + str(e))
