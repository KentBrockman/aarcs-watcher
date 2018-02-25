import os

def get_page():
    """get adoptable puppies page"""
    if os.path.isfile('page.html'):
        return open('page.html').read()
    else:
        from urllib.request import urlopen
        url = "http://aarcs.ca/adoptable-dogs/adoptable-puppies/"
        return urlopen(url).read()

page = get_page()

# bs to parse out cards for adoptable puppies
from bs4 import BeautifulSoup
soup = BeautifulSoup(page, 'html.parser')

# grid-sort-container isotope no_margin-container with-only_excerpt-container grid-total-odd grid-col-5 grid-links- isotope_activated
myElements = soup.findAll('article')

print('Number of elements: ', len(myElements))
for element in myElements:
    dog = ''
    applicationStatus = ''

    if element.h3 is not None:
        dog = element.h3.text

    if element.p is not None:
        applicationStatus = element.p.text

    print('{0} {1}'.format(dog, applicationStatus))

