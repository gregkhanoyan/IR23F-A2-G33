# imports and libraries we will be using for scraper

import re
import time
from urllib.parse import urlparse, urljoin, urldefrag, unquote
import urllib.robotparser
from bs4 import BeautifulSoup
from collections import Counter
from difflib import SequenceMatcher

# linkSet will transform list of links into a set to remove duplicates
linkSet = set()

# set of domains used for similarity
domainSet = {}

# set that stores all the domains for robots.txt
# robotsSet = set()

# pagewordCounts dictionary will hold url and word count - for max words
pageWordCounts = {}

# subdomainCounts dictionary will hold subdomains and their frequency
subdomainCounts = {}

# wordCounter will hold number of times a certain word is read
wordCounter = Counter()

# user agent for robots
user_agent = "IR UF23 11539047,55544104"

# list of stopwords
stopWords = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", 
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", 
    "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", 
    "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for", 
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", 
    "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", 
    "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", 
    "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", 
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", 
    "our", "ours", "ourselves", "out", "over", "own", "same", "markellekelly", "shan't", "she", "she'd", 
    "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", 
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", 
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", 
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", 
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", 
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", 
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
])

# list of valid domains we can crawl in
domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

# maximum file size for any webpage
max_file_size = 200 * 1024 * 1024


# FUNCTION: scraper(url, resp) - scrapes links using extract_next_links(url, resp) and returns them to worker.py where it is placed to the frontier
def scraper(url, resp):
    # try-except to catch exceptions
    try:
        # check if the url is valid
        if is_valid(url):

            # politeness
            time.sleep(0.2)

            # checking for preliminary emptiness - if all these are False, we know that the webpage has no "real content" size
            if resp.raw_response is not None and resp.raw_response.headers is not None and 'Content-Length' in resp.raw_response.headers:
                content_size = int(resp.raw_response.headers['Content-Length'])
            else:
                content_size = None  

            # checking for a status code returned over 400 - this signifies some error
            if resp.status >= 400:
                print("TIMEOUT") 
                return []
            
            # checks for the actual content of the webpage, if the text results in 0, we return an empty list
            if resp.raw_response is not None and resp.raw_response.content is not None:
                if len(resp.raw_response.content.strip()) == 0:
                    # empty
                    return []
            
            # more checks because we were getting lots of 'NoneType' errors
            if resp.raw_response is not None:
                if resp.raw_response.headers is None:
                    return []
            
            # returns an empty list if file size is too big
            if content_size is not None and content_size > max_file_size:
                return []
            
            # Fixes URL's having / at the end being different from not having a /
            url = url.rstrip("/")

             # Subdomain Counts
            parsed_url = urlparse(url)

            # checking for subdomains with 'ics.uci.edu' at the end - these are the subdomains we want
            if parsed_url.netloc == "ics.uci.edu" or parsed_url.netloc.endswith(".ics.uci.edu"):
                # remove 'www' if in URL
                if parsed_url.netloc.rsplit('.')[0] == 'www':
                    subdomain = parsed_url.netloc.rsplit('.')[1]
                else:
                    subdomain = parsed_url.netloc.rsplit('.')[0]

                # if our subdomain is not ICS, we can count it towards our subdomain counts
                if subdomain != 'ics':
                    subdomainCounts[subdomain] = subdomainCounts.get(subdomain, 0) + 1

                    # print("SUBDOMAIN: ", subdomainCounts)

            # List of found links - calls 'extract_next_links(url, resp)' in order to retrieve a set of links from the current webpage
            links = extract_next_links(url, resp)

            # Links added to set to remove duplicates
            if links is not None:
                linkSet.update(links)
            else:
                print("No more links here! Moving on...")
            
            # Store word count for the current URL
            if resp.raw_response and resp.raw_response.content is not None:
                content = resp.raw_response.content
                pageWordCounts[url] = count_words(content)

                # Update wordCounter for each tokenized word, not including stop words
                tokens = tokenize(content)
                for word in tokens:
                    if word.lower() not in stopWords:
                        wordCounter[word.lower()] += 1           
        else:
            print(url, " is not a valid URL for crawling.")
    except Exception as e:
        print("Error processing URL: ", url, " ", str(e))

        # Find the url of the longest page in terms of words count
    if pageWordCounts:
        longest_page_url = max(pageWordCounts, key=pageWordCounts.get)
        # print("LONGEST PAGE URL:", longest_page_url)
        # print("NUMBER OF WORDS:", pageWordCounts[longest_page_url])

    # Get the 50 most common words
    if wordCounter:
        most_common_words = wordCounter.most_common(50)
        # print("50 MOST COMMON WORDS:", most_common_words)

    # Print out the counts for each subdomain
    sorted_subdomains = []
    keys = list(subdomainCounts.keys())
    keys.sort()

    for key in keys:
        value = subdomainCounts[key]
        full_url = f"https://{key}.uci.edu"
        sorted_subdomains.append((full_url, value))

    print("SORTED SUBDOMAINS: ", sorted_subdomains)

    # returns a list of links
    return list(linkSet)

# FUNCTION - extract_next_links(url, resp) - takes the URL of the page we are currently on and parses the page to return only valid links retrieved
def extract_next_links(url, resp):
    link_list = []

    # checks for a successful response status, 200
    if resp.status == 200:
        try:

            # set page content
            content = resp.raw_response.content
            
            # checks for useless pages with less than 100 words
            if count_words(content) < 100:
                print("PAGE TOO SHORT!")
                return []

            # uses the BeautifulSoup library to parse the HTML of the page
            soup = BeautifulSoup(content, 'html.parser')

            # in the HTML, we want to find all '<a>' tags and extract the link, the 'href'
            for curr in soup.find_all('a'):
                link = curr.get('href')
                if link is not None:

                    # we then use 'urllib.parse: urljoin' in order to combine the relative URL's with our base URL in order to get our final URL
                    url_joined = urljoin(url, link)

                    # Strip the trailing '/'
                    url_joined = url_joined.rstrip("/")

                    # Use 'urllibe.parse: urldefrag' to remove the fragment, as in this assignment we ignore the fragment 
                    if "#" in url_joined:
                        url_joined = urldefrag(url_joined).url
                   
                    final_url  = unquote(url_joined)

                    # checks validity of our final_url - if it is valid, then we can add it to our list of links
                    
                    if is_valid(final_url):
                        # ATTEMPT AT robots.txt POLITNESS IMPLEMENTATION

                        # temp_url = urlparse(final_url)

                        # final_url_domain = temp_url.netloc
                        # print("FINAL URL DOMAIN", final_url_domain)

                        # Extract the subdomain
                        # subdomain = None

                        # # Check if the netloc (domain) ends with one of the valid domains
                        # for valid_domain in domains:
                        #     if temp_url.netloc.endswith(valid_domain):
                        #         # Extract the subdomain by splitting at the first period ('.') in the netloc
                        #         if temp_url.netloc.rsplit('.')[0] == 'www':
                        #             # print("LINE 227")
                        #             subdomain = temp_url.netloc.rsplit('.')[1]
                        #         else:
                        #             subdomain = temp_url.netloc.rsplit('.')[0]
                        #         # print("SUBDOMAIN", subdomain)
                        #         break
                        
                        # robots_url = ''
                        
                        # if robotsSet is not None:
                        #     if final_url_domain + "/robots.txt" in robotsSet:
                        #         robots_url = final_url_domain + "/robots.txt"
                        #         # print(robots_url)
                        #     else:
                        #         # big "if in"
                        #         for url, count in subdomainCounts.items():          # vision
                        #             if subdomain == url:
                        #                 # if in, then create robots URL
                        #                 robots_url = final_url_domain + "/robots.txt"
                        #                 robotsSet.add(robots_url)
                        #                 break
                        #                 # print(robots_url)                  
                        
                        # if robots_url:
                        #     parser = urllib.robotparser.RobotFileParser()
                        #     parser.set_url(robots_url)
                        #     parser.read()
                        #     allowed = parser.can_fetch(user_agent, robots_url)
                        
                        #     if(allowed):

                        # is the URL is valid, add the URL to our set of unique URL's and append it to our list
                        linkSet.add(final_url)
                        link_list.append(final_url)

                        # for similarity checking function
                        temp = urlparse(final_url)
                        domainSet[final_url] = {
                        "scheme": temp.scheme,
                        "netloc": temp.netloc,
                        "path": temp.path,
                        "params": temp.params,
                        "query": temp.query,
                        "fragment": temp.fragment
                        }
                        

                        

                        # else:
                        #     continue
                    else:
                        continue
                else:
                    continue
        except Exception as e:
            print("ERROR: Error parsing " + url + " - " + str(e)) 
            return []      
    # if the response code was something other than 200, means there was an error - print it so we can see
    else:
        print("Error: " + str(resp.status))
        return

    # prints unique page count with each iteration so we can see while our code is running
    print("UNIQUE PAGES - ", len(linkSet))
    return link_list

# FUNCTION: is_valid(url) - checks the validity of a URL:str passed in - returns a boolean True or False
def is_valid(url):
    try:
        # checks for scheme equivalence
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Checks for Trap keywords
        if not re.match(r'^(\w*.?)(ics.uci.edu|cs.uci.edu|stat.uci.edu|informatics.uci.edu)$',parsed.netloc):
            return False
        if "version=" in url:
            return False
        if "sidebyside" in url:
            return False
        if "policies" in url:
            return False
        if "stayconnected" in url:
            return False
        if "filter%5B" in url:
            return False
        if "filter[" in url:
            return False
        if "format=" in url:
            return False
        if "pdf" in url:
            return False
        if "redirect" in url:
            return False
        if "?share=" in url:
            return False
        # checks for invalid file types
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|war|apk|img|mpg|ipynb|ppsx)$", parsed.path.lower()):
            return False
        
        # traps
        if url == "https://www.stat.uci.edu/covid19/index.html":
            return False

        if "https://wics.ics.uci.edu/events" in url:
            return False
        
        return True

    except TypeError:
        print("TypeError for ", parsed)
        raise

# FUNCTION: tokenize(content) - turns content from page into tokens to count towards word count
def tokenize(content):
    # Strip HTML markup
    soup = BeautifulSoup(content, 'html.parser')
    newContent = soup.get_text()

    # Splits words and creates list, non-word characters act as the break
    # cleanTokens will set all tokens lower case and will discard any tokens with length less than 2 letters
    tokens = re.split(r'\W+', newContent)
    cleanTokens = []
    for token in tokens:
        if len(token) > 2:
            token.lower()
            cleanTokens.append(token)

    return cleanTokens

# FUNCTION: count_words(content) - counts words
def count_words(content):
    # Parse HTML markup
    soup = BeautifulSoup(content, 'html.parser')

    # Remove html tags, invisible text
    for tags in soup(['script','style']):
        tags.extract()
    
    # Get text
    newContent = soup.get_text()

    # Use regex to count the number of words in the content
    words = [word for word in re.findall(r'\w+', newContent) if not word.isnumeric()]
    return len(words)

# FUNCTION - print_deliverables() - prints delivarables for our output
def print_deliverables():
    if linkSet:
        print("NUMBER OF UNIQUE PAGES - ", len(linkSet))

    if pageWordCounts:
        longest_page_url = max(pageWordCounts, key=pageWordCounts.get)
        print("LONGEST PAGE URL - ", longest_page_url, " - WITH WORD COUNT: - ", pageWordCounts[longest_page_url])
    
    if wordCounter:
        most_common_words = wordCounter.most_common(50)
        print("50 MOST COMMON WORDS:", most_common_words)
