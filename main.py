import os
import sqlite3
import datetime

def get_page():
    """
    get adoptable puppies page
    """
    if os.path.isfile('page.html'):
        return open('page.html').read()
    else:
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
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, 'html.parser')

    # all dogs are wrapped in element 'article'
    elements = soup.findAll('article')

    print('Number of elements: ', len(elements))
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
            'status': element.p.text if element.p is not None else 'no applications',
            'last_seen': current_time
        }

def get_last_known_dog(c, dog_id):
    """
    Get the last known state for a given dog
    """
    c.execute('SELECT * FROM dogs WHERE id = ?;', (dog_id,))
    return c.fetchone()

def insert_dog_to_db(c, dog):
    c.execute('''INSERT INTO dogs (id, name, status, last_seen) VALUES (?,?,?,?);''', (dog['id'], dog['name'], dog['status'], dog['last_seen'],))


def update_dog_in_db(c, dog):
    c.execute('''UPDATE dogs SET last_seen = ?, status = ? WHERE id = ?;''', (dog['last_seen'], dog['status'], dog['id'],))

if __name__ == '__main__':
    # set up DBs
    conn = sqlite3.connect('dogs.db')
    c = conn.cursor()

    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='dogs';''')
    if c.fetchone() is None:
        c.execute('''CREATE TABLE dogs (id, name, status, last_seen)''')
        print('Created dogs table')
    else:
        print('Table already exists')

    current_dogs = get_current_dogs()

    # TODO: delete dogs unseen for 15 days
    # TODO: generate a report object for all state changes - notify with that
    # TODO: implement timer via config 
    # TODO: implement notifications
    updates = []

    for dog in current_dogs:
        last_known = get_last_known_dog(conn.cursor(), dog['id'])   

        if last_known is None:
            print('New dog!')
            updates.append(dog)
            insert_dog_to_db(conn.cursor(), dog)
        # elif last_known['status'] != dog['status']:
        #     print('{0} has gone from \'{1}\' to \'{2}\''.format(dog['name'], last_known['status'], dog['status']))
        else:
            update_dog_in_db(conn.cursor(), dog)

    if len(updates) > 0:
        print('We got some updates!')
    else:
        print('No change')

    conn.commit()
    conn.close()