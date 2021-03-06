import os
import sqlite3
import datetime
import time
import configparser
import logging
import sys

from bs4 import BeautifulSoup
from pushover import init, Client

config = configparser.ConfigParser()
config.read('config.ini')

logging.basicConfig(format='%(asctime)s %(message)s',
                    filename=os.path.join(config['default']['LogLocation'], 'watcher.log'),
                    level=int(config['default']['LogLevel']))
ch = logging.StreamHandler(sys.stdout)
rootLogger = logging.getLogger()
rootLogger.addHandler(ch)

def get_page():
    """
    get adoptable puppies page
    """
    from urllib.request import urlopen
    url = "http://aarcs.ca/adoptable-dogs/adoptable-puppies/"
    return urlopen(url).read()
        
def get_current_dogs():
    """
    get adoptable puppies from AARCS
    return formatted dict with dog properties
    """
    current_time = datetime.datetime.utcnow()
    page = get_page()

    # bs to parse out cards for adoptable puppies
    soup = BeautifulSoup(page, 'html.parser')

    # all dogs are wrapped in element 'article'
    elements = soup.findAll('article')

    for element in elements:
        if elements.index(element) is 0:
            # skip first element in the array
            continue

        if element.h3 is None:
            continue 

        if element.a is None:
            continue

        yield { 
            'id': element.a['href'].replace('http://aarcs.ca/portfolio-item', '').replace('/', ''),
            'name': element.h3.text, 
            'status': element.p.text if element.p is not None and element.p.text is not '' else 'no applications',
            'link': element.a['href'],
            'last_seen': current_time
        }

def get_last_known_dog(c, dog_id):
    c.execute('SELECT * FROM dogs WHERE id = ?;', (dog_id,))
    return c.fetchone()

def insert_dog_to_db(c, dog):
    c.execute('''INSERT INTO dogs (id, name, status, link, last_seen) VALUES (?,?,?,?, ?);''', (dog['id'], dog['name'], dog['status'], dog['link'], dog['last_seen'],))

def update_dog_in_db(c, dog):
    c.execute('''UPDATE dogs SET last_seen = ?, status = ?, link = ? WHERE id = ?;''', (dog['last_seen'], dog['status'], dog['link'], dog['id'],))

def clean_out_unseen_dogs(c):
    c.execute('''SELECT id FROM dogs WHERE last_seen < ?;''', (str(datetime.datetime.utcnow() - datetime.timedelta(days=15)),))
    to_remove = c.fetchall()
    for item in to_remove:
        c.execute('DELETE FROM dogs WHERE id = ?;', item)
        logging.info('deleting record {0}'.format(item))

if __name__ == '__main__':
    logging.info('starting the process')

    # set up DB
    conn = sqlite3.connect(os.path.join(config['default']['DatabaseLocation'], 'dogs.db'))
    c = conn.cursor()
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='dogs';''')
    if c.fetchone() is None:
        c.execute('''CREATE TABLE dogs (id, name, status, link, last_seen);''')
        logging.info('created dogs table')
    else:
        logging.info('dogs database is ready')

    # set up pushover
    init(config['pushover']['Token'])
    pushover_client = Client(config['pushover']['UserKey'])

    logging.info('checking aarcs')
    first_pass = True
    while first_pass:
        current_dogs = get_current_dogs()
        # logging.debug(list(current_dogs))
        updates = {'new_dogs': [], 'new_applications': []}

        for dog in current_dogs:
            last_known = get_last_known_dog(conn.cursor(), dog['id'])   

            if last_known is None:
                # have a new dog
                updates['new_dogs'].append(dog)
                insert_dog_to_db(conn.cursor(), dog)
            else:
                # update the existing dog record (just update last_seen)
                update_dog_in_db(conn.cursor(), dog)

            # last_known[2] is status
            if last_known is not None and last_known[2] != dog['status']:
                # a dog status has changed
                updates['new_applications'].append(dog)

        if len(updates['new_dogs']) > 0:
            logging.info('{0} new dogs'.format(len(updates['new_dogs'])))
            body = ''
            for dog in updates['new_dogs']:
                body = body + 'See <a href="{0}">{1}</a> - Status: {2}\n'.format(dog['link'], dog['name'], dog['status'])
            pushover_client.send_message(body, title='{0} New Dogs!'.format(len(updates['new_dogs'])), html=1)

        if len(updates['new_applications']) > 0:
            logging.info('{0} updated applications'.format(len(updates['new_applications'])))
            body = ''
            for dog in updates['new_applications']:
                body = body + '<a href="{0}">{1}</a> is now {2}\n'.format(dog['link'], dog['name'], dog['status'])
            pushover_client.send_message(body, title='{0} New Applications!'.format(len(updates['new_applications'])), html=1)

        clean_out_unseen_dogs(conn.cursor())

        conn.commit()

        first_pass = int(config['default']['Repeat'])
        if first_pass:
            time.sleep(int(config['default']['RepeatIntervalInSeconds']))

    conn.close()
