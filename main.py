import os

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

        yield { 
            'name': element.h3.text, 
            'status': element.p.text if element.p is not None else 'no applications'
        }

def get_last_known_dog(dog_name):
    """
    Get the last known state for a given dog
    """
    dogs = [
        {'name': 'Rogue', 'status': 'no applications'}, 
        {'name': 'Dasher', 'status': 'application pending'}, 
        {'name': 'Prancer', 'status': 'application pending'}, 
        {'name': 'Portman', 'status': 'application pending'}, 
        {'name': 'Cooper', 'status': 'no applications'}, 
        {'name': 'Doogie', 'status': 'application pending'}, 
        {'name': 'Easton', 'status': 'application pending'}, 
        {'name': 'Moses', 'status': 'application pending'}, 
        {'name': 'Jasmine', 'status': 'application pending'}, 
        {'name': 'Royal', 'status': 'no applications'}, 
        {'name': 'Trevor', 'status': 'application pending'}, 
        {'name': 'Naveen', 'status': 'application pending'}, 
        {'name': 'March', 'status': 'application pending'},
        {'name': 'Pammi', 'status': 'application pending'}, 
        {'name': 'Archimedes', 'status': 'no applications'}, 
        {'name': 'Sparky', 'status': 'no applications'}
    ]
    
    # BUG: what happens when two dogs have the same name?
    # TODO: store a unique ID for the dog, use end fragment of the path
    # TODO: implement SQLite
    return next(filter(lambda dog: dog['name'] == dog_name, dogs))

if __name__ == '__main__':
    current_dogs = get_current_dogs()
    # print(list(current_dogs))

    # TODO: find dogs in DB that arent in current_dogs - flag for deletetion
    # TODO: delete dogs that were flagged for deletion 15 days ago
    # TODO: generate a report object for all state changes - notify with that
    # TODO: implement timer via config 
    # TODO: implement notifications

    for dog in current_dogs:
        last_known = get_last_known_dog(dog['name'])

        if last_known is None:
            print('New dog!')
        elif last_known['status'] != dog['status']:
            print('{0} has gone from \'{1}\' to \'{2}\''.format(dog['name'], last_known['status'], dog['status']))