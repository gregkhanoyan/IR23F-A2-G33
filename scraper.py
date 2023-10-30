import re
from urllib.parse import urlparse, urljoin, urldefrag, unquote
from bs4 import BeautifulSoup
from collections import Counter
from difflib import SequenceMatcher
from robotexclusionrulesparser import RobotExclusionRulesParser

# seed = "https://ics.uci.edu/" 
# seed = "https://sami.ics.uci.edu/research.html"

# linkSet will transform list of links into a set to remove duplicates
linkSet = set()

# set that stores all the domains for robots.txt
domainSet = set()

# pagewordCounts dictionary will hold url and word count
pageWordCounts = {}

# subdomainCounts dictionary will hold subdomains and their frequency
subdomainCounts = {}

# sorted subdomains
# sortedSubdomains = {}

# wordCounter will hold number of times a certain word is read
wordCounter = Counter()

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
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", 
    "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", 
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", 
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", 
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", 
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", 
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", 
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
])

valid_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

def scraper(url, resp):
    try:
        if is_valid(url) and resp.status == 200:

            if resp.raw_response is not None and resp.raw_response.headers is not None and 'Content-Length' in resp.raw_response.headers:
                content_size = int(resp.raw_response.headers['Content-Length'])
            else:
                content_size = None  # Handle the case where the header is missing
                
            max_file_size = 200 * 1024 * 1024

            if resp.status == 408:
                print("timeout")
                return
            if resp.raw_response is not None and resp.raw_response.content is not None:
                if len(resp.raw_response.content.strip()) == 0:
                    # empty
                    return
            if resp.raw_response is not None:
                if resp.raw_response.headers is None:
                    return
            if content_size is not None and content_size > max_file_size:
                return
            
            # Fixes URL's having / at the end being different from not
            url = url.rstrip("/")

            # List of found links
            links = extract_next_links(url, resp)
            # print(links)

            # Links added to set to remove duplicates
            if links is not None:
                linkSet.update(links)
            else:
                print("No more links here! Moving on...")

            # print("LINK LENGTH: ", len(links))
            # print("Extracted Links:")

            # Find number of UNIQUE PAGES
            uniquePages = len(linkSet)
            print("Number of Unique Pages: ", uniquePages)
            
            # Store word count for the current URL; PAGEWORDCOUNTER
            if resp.raw_response and resp.raw_response.content is not None:
                content = resp.raw_response.content
                pageWordCounts[url] = count_words(content)

                # Update WORDCOUNTER for each tokenized word, not including stop words
                tokens = tokenize(content)
                for word in tokens:
                    if word.lower() not in stopWords:
                        wordCounter[word] += 1

            # Update SUBDOMAINCOUNTER dictionary
            parsed_url = urlparse(url)
            if parsed_url.netloc.endswith('ics.uci.edu'):

                # https://subdomain.ics.uci.edu
                # url_to_store = parsed_url.scheme +  "://" + parsed_url.netloc
                subdomain = parsed_url.netloc.split('.')[0]
                
                # Extract the subdomain part
                subdomain = parsed_url.netloc.rsplit('.')[0]

                if subdomain != 'ics':
                    # If base ics.uci.edu, skip
                    # Increment count for the subdomain or initialize it if it doesn't exists
                    # subdomainCounts[url_to_store] = subdomainCounts.get(subdomain, 0) + 1
                    subdomainCounts[subdomain] = subdomainCounts.get(subdomain, 0) + 1

                    # print("SUBDOMAIN: ", subdomainCounts)

        else:
            print(url, " is not a valid URL for crawling.")
    except Exception as e:
        print("Error processing URL: ", url, " ", str(e))
        # Find the url of the longest page in terms of words count
    if pageWordCounts:
        longest_page_url = max(pageWordCounts, key=pageWordCounts.get)
        # print("Longest page URL:", longest_page_url)
        # print("Number of words:", pageWordCounts[longest_page_url])

    # Get the 50 most common words
    most_common_words = wordCounter.most_common(50)
    # print("50 most common words:", most_common_words)

    # Print out the counts for each subdomain
    # sortedSubdomains = dict(sorted(subdomainCounts.items(), key=lambda item: item[0]))
    sorted_subdomains = []
    keys = list(subdomainCounts.keys())
    keys.sort()

    # for key in keys:
    #     value = subdomainCounts[key]
    #     sorted_subdomains.append((key, value))
    
    for key in keys:
        value = subdomainCounts[key]
        full_url = f"https://{key}.ics.uci.edu"
        sorted_subdomains.append((full_url, value))

    print("Sorted Subdomains: ", sorted_subdomains)

    # linkSet validity checker
    links_return = []

    for link in linkSet:
        if is_valid(link):
            links_return.append(link)

    # returns a list of links
    return links_return


def extract_next_links(url, resp):
    link_list = []
    if resp.raw_response is not None:
        if resp.raw_response.content is not None:
            content = resp.raw_response.content
        if count_words(content) < 250:
            print("PAGE TOO SHORT!")
            return
    
    # checking if we actually got the page
    # do we have to check utf-8 encoding?
    # print(resp.status_code)
    # print(resp.headers)
    # print(resp.status_code)
    if resp.status == 200:
        try:
            # use BeautifulSoup library to parse the HTML content of the page
            # print("Raw Content: ", raw)

            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

            # we want to eliminate the possibility of a 404 page which doesnt return 
            # an error 404 code, such as http://cs.uci.edu/page
            # title_tag = soup.find("title")
            # invalid_title = "Page not found"

            # # checks if Page not found is title, if so break of function
            # if title_tag and invalid_title:
            #     return

            # in the HTML, we want to find all '<a>' tags and extract the link, the 'href'
            for curr in soup.find_all('a'):
                link = curr.get('href')
                if link:
                    # we then use 'urllib.parse: urljoin' in order to combine the relative URL's with our base URL in order to get our final URL
                    url_joined = urljoin(url, link)

                    url_joined = url_joined.rstrip("/")

                    # Use 'urllibe.parse: urldefrag' to remove the fragment, as in this assignment we ignore the fragment 
                    if "#" in url_joined:
                        url_joined = urldefrag(url_joined).url
                   
                    final_url  = unquote(url_joined)
                    # print("FINAL URL", final_url)

                    # checks validity of our final_url - if it is valid, then we can add it to our list of links
                    if is_valid(final_url):
                        # parsed_url = urlparse(final_url)
                        # domain = parsed_url.netloc
                        # path = parsed_url.path
                        # robots_url = f"https://{domain}/robots.txt"
                        # robots_subdomain_url = f"https://{domain}{path}/robots.txt"
                        # print(robots_subdomain_url)

                        # https://vision.ics.uci.edu
                        if final_url in subdomainCounts:
                            robots_url = final_url + "/robots.txt"
                            print(robots_url)     
                        else:
                            robots_url = None                       

                        if robots_url and robots_url not in domainSet:
                            domainSet.add(robots_url)

                        if robots_url is not None:
                            parser = RobotExclusionRulesParser()
                            parser.fetch(robots_url)
                        
                            if parser.is_allowed(user_agent, final_url):
                                link_list.append(final_url)
                        else:
                            link_list.append(final_url)
        except Exception as e:
            print("ERROR: Error parsing " + url + " - " + str(e)) 
            return []      
    # if the response code was something other than 200, means there was an error - print it so we can see
    else:
        print("Error: " + str(resp.status))
        return

    return link_list


# FUNCTION: is_valid(url) - checks the validity of a URL:str passed in - returns a boolean True or False
def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        url = unquote(url)

        # List of disallowed file extensions
        invalid = [
            "css", "js", "bmp", "gif", "jpg", "jpeg", "ico",
            "png", "tif", "tiff", "mid", "mp2", "mp3", "mp4",
            "wav", "avi", "mov", "mpeg", "ram", "m4v", "mkv", "ogg", "ogv", "pdf",
            "ps", "eps", "tex", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "names",
            "data", "dat", "exe", "bz2", "tar", "msi", "bin", "7z", "psd", "dmg", "iso",
            "epub", "dll", "cnf", "tgz", "sha1", "thmx", "mso", "arff", "rtf", "jar", "csv",
            "rm", "smil", "wmv", "swf", "wma", "zip", "rar", "gz" , "img", "war", "mpg" , "ipynb" , "ppsx"
        ]

        # List of valid domains we can crawl in
        domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

        # Check if the parsed domain matches any of the allowed domains
        domain_check = any(parsed.netloc.endswith("." + domain) or parsed.netloc == domain for domain in domains)

        pdf_check = "pdf" not in url.lower()

        # Check if the path doesn't have invalid extensions
        extension_check = not any(parsed.path.lower().endswith("." + filetype) for filetype in invalid)

        # return the boolean expression determined by the logical AND of domain_match and extension_match
        # if the url exists in our valid domains and does not fall under any of the invalid extensions, return True, else return False
        return domain_check and extension_check and pdf_check

    except TypeError:
        print("TypeError for ", parsed)
        raise


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


def count_words(content):
    # Parse HTML markup
    soup = BeautifulSoup(content, 'html.parser')

    # Remove html tags, invisible text
    for tags in soup(["script", "style"]):
        tags.extract()
    
    # Get text
    newContent = soup.get_text()

    # Use regex to count the number of words in the content
    words = re.findall(r'\w+', newContent)
    return len(words)


def not_similar(url):
    parsed = urlparse(url)
    domain_key = parsed.netloc  # Use the domain as the key for efficient lookups

    for other_url in linkSet:
        other_parsed = urlparse(other_url)
        other_domain_key = other_parsed.netloc

        # If the domain is the same, consider comparing paths and queries
        if domain_key == other_domain_key:
            path_similarity = SequenceMatcher(None, parsed.path, other_parsed.path).ratio()
            query_similarity = SequenceMatcher(None, parsed.query, other_parsed.query).ratio()

            # If path and query are significantly similar, consider them as similar URLs
            if path_similarity > 0.8 and query_similarity > 0.8:
                return False

    # If no similar URL is found, return True
    return True
