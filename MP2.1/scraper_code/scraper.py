from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import re 
import urllib
import time

#create a webdriver object and set options for headless browsing
options = Options()
options.headless = True
driver = webdriver.Chrome('./chromedriver',options=options)

#uses webdriver object to execute javascript code and get dynamically loaded webcontent
def get_js_soup(url, driver):
    driver.get(url)
    res_html = driver.execute_script('return document.body.innerHTML')
    # beautiful soup object to be used for parsing html content
    soup = BeautifulSoup(res_html, 'html.parser') 
    return soup

#tidies extracted text
def process_bio(bio):
    # removes non-ascii characters
    bio = bio.encode('ascii', errors='ignore').decode('utf-8')
    # replaces repeated whitepace characters with simple space
    bio = re.sub('\s+',' ', bio)
    return bio

''' More tidying
Sometimes the text extracted HTML webpage may contain javascript code and some style elements. 
This function removes script and style tags from HTML so that extracted text does not contain them.
'''

def remove_script(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup

# Checks if bio_url is a valid faculty homepage
def is_valid_homepage(bio_url, dir_url):
    if bio_url.endswith('.pdf'): # we are not parsing pdfs
        return False
    try:
        #sometimes the homepage url points to the same page as the faculty profile page
        #which should be treated differently from an actual homepage
        ret_url = urllib.request.urlopen(bio_url).geturl()
    except:
        return False # unable to access bio_url
    # remove url scheme (https, http, www)
    urls = [re.sub('((https?://)|(www.))','',url) for url in [ret_url, dir_url]]
    return not(urls[0]==urls[1])


#extracts all Faculty Profile page urls from the Directory Listing Page
def scrape_dir_page(dir_url,driver):
    print ('-'*20,'Scraping directory page','-'*20)
    faculty_links = []
    #faculty_base_url = 'https://cs.illinois.edu'
    #execute js on webpage to load faculty listings on webpage and get ready to parse the loaded HTML 
    soup = get_js_soup(dir_url,driver)     
    for link_holder in soup.find_all('div',class_='fusion-image-wrapper'): #get list of all <div> of class 'fusion-image-wrapper'
        fac_link = link_holder.find('a')['href'] #get url
        #url returned is relative, so we need to add base url
        faculty_links.append(fac_link) 
    print ('-'*20,'Found {} faculty profile urls'.format(len(faculty_links)),'-'*20)
    return faculty_links


'''
'''


dir_url = 'https://cee.mit.edu/people/faculty/' #url of directory listings of CEE faculty
faculty_links = scrape_dir_page(dir_url,driver)
faculty_links = faculty_links[1:]

'''
'''
fac_url = 'https://cee.mit.edu/people_individual/markus-j-buehler/'#faculty_links[5]''
def scrape_faculty_page(fac_url,driver):
    soup = get_js_soup(fac_url,driver)
    homepage_found = False
    bio_url = ''
    bio = ''
    profile_sec = soup.find('span',class_='bio-detail bio-website')
    if profile_sec is None:
        return bio_url,bio
    all_tags = profile_sec.find_all('a') #get url
    all_links = []
    for tg in all_tags:
        all_links.append(tg.get('href'))
        
    faculty_name = fac_url[38:-1].split('-')
    homepage_txts = [faculty_name[0],faculty_name[-1],'https:','web']
    exceptions = ['@mit','mailto']
    
    for lk in all_links:
        count = 0
        if lk is not None and not any(e in lk for e in exceptions):
            for txt in homepage_txts:
                if txt in lk:
                    count += 1
            if count >= 2:
                bio_url = lk
                homepage_found = True
                print('yes')
                print(count)
            #check if homepage url is valid
                if not(is_valid_homepage(bio_url,fac_url)):
                    homepage_found = False
                else:
                    try:
                        bio_soup = remove_script(get_js_soup(bio_url,driver))
                        print('yes')
                    except:
                        print ('Could not access {}'.format(bio_url))
                        homepage_found = False   
        
        if homepage_found:
            #get all the text from homepage(bio)
            bio = process_bio(bio_soup.get_text(separator=' '))
            break
        
    if not homepage_found:
        bio_url = fac_url #treat faculty profile page as homepage
        bio = process_bio(profile_sec.get_text(separator=' '))   
    
    return bio_url,bio

'''
'''

#Scrape homepages of all urls
bio_urls, bios = [],[]
tot_urls = len(faculty_links)
for i,link in enumerate(faculty_links):
    print ('-'*20,'Scraping faculty url {}/{}'.format(i+1,tot_urls),'-'*20)
    bio_url,bio = scrape_faculty_page(link,driver)
    if bio.strip()!= '' and bio_url.strip()!='':
        bio_urls.append(bio_url.strip())
        bios.append(bio)
driver.close()

def write_lst(lst,file_):
    with open(file_,'w') as f:
        for l in lst:
            f.write(l)
            f.write('\n')
            
            
bio_urls_file = 'bio_urls.txt'
bios_file = 'bios.txt'
write_lst(bio_urls,bio_urls_file)
write_lst(bios,bios_file)
