# Import general libraries
import datetime
import os

from bs4 import BeautifulSoup as soup
import time

import requests
requests.packages.urllib3.disable_warnings()
import random

# Improt Selenium packages
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException as NoSuchElementException
from selenium.common.exceptions import WebDriverException as WebDriverException
from selenium.common.exceptions import ElementNotVisibleException as ElementNotVisibleException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def request_page(url_string, verification, robust):
    """HTTP GET Request to URL.
    Args:
        url_string (str): The URL to request.
        verification: Boolean certificate is to be verified
        robust: If to be run in robust mode to recover blocking
    Returns:
        HTML code
    """
    if robust:
        loop = False
        first = True
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                uclient = requests.get(url_string, timeout = 60, verify = verification)
                page_html = uclient.text
                loop = False
                return page_html
            except requests.exceptions.ConnectionError:
                c += 10
                print("Request blocked, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
            except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectTimeout):
                print("Request timed out, .. waiting one minute and continuing...")
                time.sleep(60)
                loop = True
                continue
    else:
        uclient = requests.get(url_string, timeout = 60, verify = verification)
        page_html = uclient.text
        loop = False
        return page_html

def request_page_fromselenium(url_string, driver, robust):
    """ Request HTML source code from Selenium web driver to circumvent mechanisms
    active with HTTP requests
    Args:
        Selenium web driver
        URL string
    Returns:
        HTML code
    """
    if robust:
        loop = False
        first = True
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                open_webpage(driver, url_string)
                time.sleep(5)
                page_html = driver.page_source
                loop = False
                return page_html
            except WebDriverException:
                c += 10
                print("Web Driver problem, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
    else:
        open_webpage(driver, url_string)
        time.sleep(5)
        page_html = driver.page_source
        loop = False
        return page_html

def set_driver(webdriverpath, headless):
    """Opens a webpage in Chrome.
    Args:
        url of webpage.
    Returns:
        open and maximized window of Chrome with webpage.
    """
    options = Options()  
    if headless:
        
        options.add_argument("--headless")
    elif not headless:
        options.add_argument("--none")
    return webdriver.Chrome(webdriverpath, chrome_options = options)

def create_object_soup(object_link, verification, robust):
    """ Create page soup out of an object link for a product
    Args:
        Object link
        certificate verification parameter
        robustness parameter
    Returns:
        tuple of beautiful soup object and object_link
    """
    object_soup = soup(request_page(object_link, verification, robust), 'html.parser')
    return (object_soup, object_link)

def make_soup(link, verification):
    """ Create soup of listing-specific webpage
    Args:
        object_id
    Returns:
        soup element containing listings-specific information
    """
    return soup(request_page(link, verification), 'html.parser')

def reveal_all_items(driver):
    """ Reveal all items on the categroy web page of Albert Heijn by clicking "continue"
    Args:
        Selenium web driver
    Returns:
        Boolean if all items have been revealed
    """
    hidden = True
    while hidden:
        try:
           time.sleep(random.randint(5,7))
           driver.find_element_by_css_selector('section#listing-home div.col-md-6.customlistinghome > a').click()
        except (NoSuchElementException, ElementNotVisibleException):
           hidden = False
    return True

def open_webpage(driver, url):
    """Opens web page
    Args:
        web driver from previous fct and URL
    Returns:
        opened and maximized webpage
    """
    driver.set_page_load_timeout(60)
    driver.get(url)
    driver.maximize_window()


def find_correct_css_element(pagination_container): 
    """ Finds current position in pagination container 
    and returns right CSS number to click on.
    Args:
        BS4 pagination container
    Returns:
        Integer for correct clicking
    """
    container = pagination_container[1:len(pagination_container)-1]
    for i in container:
        try:
            i.a['href']
            continue
        except TypeError:
            pos = container.index(i)
            return pos + 2

def click_page_forward(driver, counter, pagecount, pagination_length):
    """ Click pages forward to access PDF files on individual page
    Args:
        Pagecount
        web driver
        counter parameter
        pagination_length parameter
    Returns:
        Next page using web driver and resetted counter
    """
    # Extract page attributes
    page_html = driver.page_source
    page_soup = soup(page_html, 'html.parser')
    pagination_container = page_soup.findAll('table', {'class': 'mGrid'})[0].tbody.findAll('tr', {'align': 'center'},
                                   {'style': 'color:White;background-color:#2461BF;'})[0].findAll('td') 
    # Extract length of pagination and last element
    last_element = pagination_container[len(pagination_container)-1].text
    pagination_length_old = pagination_length
    pagination_length
    # Extract information on current pagination
    last_element = pagination_container[len(pagination_container)-1].text
    pagination_length = len(pagination_container) - 1
    print("Last element:", last_element)
    # Differentiate cases: Once page break is reached, check for last element
    if counter <= pagination_length_old:
        counter = find_correct_css_element(pagination_container)
    else:
        if last_element == "...":     
            counter = find_correct_css_element(pagination_container)
        else:
            try:
                assert int(pagecount) <= int(last_element)
                counter = find_correct_css_element(pagination_container)
            except AssertionError:
                return (False, counter, pagination_length)  ##### CHANGE THIS to return
    try:
        driver.find_element_by_css_selector('table#ContentPlaceHolder1_gwVLPListimi tr:nth-child(12) > td > table > tbody > tr > td:nth-child(' + str(counter) +') > a').click()                               
        # Check pagecount 
        return (True, counter, pagination_length)
    except NoSuchElementException:
        return (False, counter, pagination_length)

def check_item_number(page_html):
    """ Check number of listings available in PDF grid
    Args:
        HTML page
    Returns:
        Number of items + 1
    """
    page_soup = soup(page_html, 'html.parser')    
    items_container = page_soup.findAll('table', {'class': 'mGrid'})[0].tbody.findAll('tr', {'style': 'background-color:#EFF3FB;'})
    items_container = items_container + page_soup.findAll('table', {'class': 'mGrid'})[0].tbody.findAll('tr', {'style': 'background-color:White;'})
    return len(items_container)

def scrape_n_e_s_a(base_url, robust, driver, output_path, now_str):
    """ Extract item URL links and return list of all item links on web page
    Args:
        Base URL
        Categroy tuples
        Certificate verification parameter
        Robustness parameter
        Selenium web driver
    Returns:
        Dictionary with item URLs
    """   
    pagination_ongoing = True
    counter = 0
    pagecount = 0
    pagination_length = 11
    first_run= True
    # Create folder
    now_folder =  output_path + now_str + "\\"
    os.mkdir(now_folder)
    #Start PDF extraction into folder
    print("Start retrieving PDF documents ...")
    # Open first webpage
    open_webpage(driver, base_url)
    # Loop over pages by checking if next page is available
    while pagination_ongoing:
        pagecount += 1
        counter += 1       
        # Wait 1 sec
        time.sleep(3)
        # Within each page extract all links
        print("I am on page", pagecount,"Counter =", counter, "Pagination length", pagination_length)
        if not first_run:
            # Click onwards
            click_tuple = click_page_forward(driver, counter, pagecount, pagination_length)
            pagination_ongoing = click_tuple[0]
            # Reset counter f necessary
            counter = click_tuple[1]
            # Reset paination_length of current block
            pagination_length = click_tuple[2]
            if pagination_ongoing == False:
                print("Reached end, breaking out from click routine...")
                break
            else:
                pass
        else:
            pass
        # Loop over items in page
        page_html = driver.page_source
        items = check_item_number(page_html)
        for item in range(0, items):
            print("Items:", items, "current item", item)
            now_substr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            time.sleep(random.randint(2,4))
            print("Extracting PDF", item +1, "on page", pagecount, "...")
            # Click download button
            driver.find_element_by_css_selector('#ContentPlaceHolder1_gwVLPListimi_lnkOpenProfile_' + str(item)).click()

            driver.switch_to.window(driver.window_handles[-1])
            # Extract url of PDF
            pdf_url = driver.current_url
            # Save pdf locally to path
            url_id_container = pdf_url.split('/')
            url_id = url_id_container[len(url_id_container)-1].replace('.pdf', '')
            outfile = now_folder + url_id + "_" + now_substr + ".pdf"
            # Get response code
            response = requests.get(pdf_url, timeout = 60)
            # Extract file dpending on the response
            if response.status_code == 200:
                with open(outfile, 'wb') as f:
                    f.write(response.content)
            else:
                print("Skipping PDF..")
                pass
            # Close tab 
            #driver.close()
            # switch to main window
            driver.switch_to.window(driver.window_handles[0])
        first_run = False                     
    
def main():
    """ Note: Set parameters in this function
    """
    # Set time stamp 
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set scraping parameters
    base_url = 'http://www.puna.gov.al/VLPDisplay.aspx'
    robust = True
    webdriverpath = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_web_bot\\chromedriver.exe"
    
    # Set outpath for PDF files
    output_path = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_web_bot\\data\\daily_scraping\\"
    
    # Set up a web driver
    driver = set_driver(webdriverpath, False)
    
    # Start timer
    start_time = time.time() # Capture start and end time for performance
        
    # Execute functions for scraping
    scrape_n_e_s_a(base_url, robust, driver, output_path, now_str)
    driver.quit()
    
    end_time = time.time()
    duration = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    
    # For interaction and error handling
    final_text = "Your query was successful! Time elapsed:" + str(duration)
    print(final_text)
    time.sleep(0.5) 
        
# Execute scraping    
if __name__ == "__main__":
    main()
