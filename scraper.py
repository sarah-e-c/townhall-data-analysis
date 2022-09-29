# config for automatic resuming
from configparser import ConfigParser

# beautifulsoup for parsing
from bs4 import BeautifulSoup

# requests
import requests
import os

# time
import time

# csv control
import csv
# logging
import logging

# for command line arguments
import getopt, sys

# constants
PAGE_URL = 'https://townhall.virginia.gov/L/ViewComments.cfm?GdocForumID=1953'
BASE_URL = 'https://townhall.virginia.gov/'
SCRAPER_CONFIG_FILE_NAME = 'scraper_config.ini'
CSV_FILE_NAME = 'townhall_data.csv'
REQUEST_BUFFER_TIME = 0

# sending a note with the requests just to let them know if they see something weird for some reason
HEADER = {'Note': 'Running an analysis on the town hall data. If you have any questions, contact sarah.beth.crowder@gmail.com'}


FIELDS = ['CommenterName', 'CommentTitle', 'Comment', 'CommentID', 'CommentDateTime', 'CommentLink']


logger = logging.getLogger(__name__)

first_time_scraping = False

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # getting parameters passed from system. The default is set to 30 seconds of scraping.
    if len(sys.argv) > 1:
        try:
            seconds_to_scrape = int(sys.argv[1])
        except:
            logger.info(sys.argv[1])
            if sys.argv[1] == 'all':
                seconds_to_scrape = 1000000000
    else:
        seconds_to_scrape = 30


    parser = ConfigParser()
    if not os.path.isfile(CSV_FILE_NAME): # running this for the first time
        parser.add_section('progress')
        parser.set('progress', 'pages_scraped', '0')
        with open(SCRAPER_CONFIG_FILE_NAME, 'w') as configfile:
            parser.write(configfile)
        num_pages_scraped = parser.getint('progress', 'pages_scraped')
        first_time_scraping = True
        with open(CSV_FILE_NAME, 'w') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerow(FIELDS) # setting up fields
    
    else: # continue where left off
        parser.read(SCRAPER_CONFIG_FILE_NAME)
        num_pages_scraped = parser.getint('progress', 'pages_scraped')
    
    # the page actually is weird and doesn't use a separate URL for page numbers.
    # so we have to use forms to post the page number that we want.


    # finding max number of pages:
    source = requests.get(PAGE_URL, HEADER)
    soup = BeautifulSoup(source.text, 'lxml')
    last_link = soup.find('a', class_='linkbrown')
    max_number_of_pages = int(last_link.text)
    logger.info(f'max number of pages: {max_number_of_pages}')

    pages_to_scrape = max_number_of_pages - num_pages_scraped
    start_time = time.time()

    with open(CSV_FILE_NAME, 'a') as file:
        csvwriter = csv.writer(file)

        for i in range(num_pages_scraped, max_number_of_pages):

            # checking time
            current_time = time.time()
            if current_time - start_time > seconds_to_scrape:
                logger.info('time ran out.')
                # saving progress

                break # exiting

            source = requests.post(PAGE_URL, data={'vpage': i}, headers=HEADER)
            soup = BeautifulSoup(source.text, 'lxml')
            all_comments_boxes = list(soup.find_all('div', class_='Cbox'))
            
            for comment in all_comments_boxes:

                # commenter name
                try:
                    name = ' '.join(comment.find_all('div')[2].text.split('\n')[4].split('    ')[1].split(' ')[1:]).replace('\r', '')
                except Exception as e:
                    comment_div = comment.find_all('div')[2].text
                    name = comment_div.split('\n')[2].replace('          ', '').replace('\n', '').replace('\r', '')
                    
                    

                # comment title
                try:
                    title = comment.find_all('strong')[1].text.split('\n')[1].split('      ')[1]
                except Exception as e:
                    title = comment.find_all('strong')[1].text

                # comment
                content = ' '.join(map(lambda x: x.text, list(comment.find_all('p')))).replace('\n', '')

                # comment datetime
                try:
                    datetime = comment.find_all('div')[1].text.split(' ')[6] + comment.find_all('div')[1].text.split(' ')[7]
                except Exception as e:
                    datetime = comment.find_all('div')[1].text.replace('       ', '').replace(' ', '')
                # comment id
                try:
                    comment_id = int(comment.find('a').text.replace('\n', '').replace('      ', ''))
                except:
                    comment_id = None

                # comment link
                link = BASE_URL + comment.find('a', href=True)['href']

                csvwriter.writerow([name, title, content, comment_id, datetime, link])




            num_pages_scraped += 1 # tracking progress
            time.sleep(REQUEST_BUFFER_TIME)
    



    logger.info('done scraping')
    
    # saving progress
    parser.set('progress', 'pages_scraped', str(num_pages_scraped))
    with open(SCRAPER_CONFIG_FILE_NAME, 'w') as f:
        parser.write(f)
        logger.info('config written')


    

    # source = requests.get(PAGE_URL, HEADER)
    # soup = BeautifulSoup(source.text, 'html.parser')
    # with open('first_page_html.html', 'w') as f:
    #     f.write(soup.prettify())

    # source = requests.post(PAGE_URL, data={'vpage': 1030}, headers=HEADER)
    # soup = BeautifulSoup(source.text, 'html.parser')
    # with open('1030_page_html.html', 'w') as f:
    #     f.write(soup.prettify())


        
        