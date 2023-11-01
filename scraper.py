#THIS IS LOCAL CODE> DONT RUN ON OPENLAB

import re
import time
from urllib.parse import urlparse, urljoin, urldefrag, unquote
import urllib.robotparser
from bs4 import BeautifulSoup, Comment
from collections import Counter
from difflib import SequenceMatcher

import requests

seed = "https://ics.uci.edu/" 
# seed = "https://sami.ics.uci.edu/research.html"

# linkSet will transform list of links into a set to remove duplicates
linkSet = set()

# set of domains used for similarity
domainSet = {}

normalizedSet = set()

# set that stores all the domains for robots.txt
# need to use domainSet
# robotsSet = set()

# pagewordCounts dictionary will hold url and word count - for max words
pageWordCounts = {}

# subdomainCounts dictionary will hold subdomains and their frequency
subdomainCounts = {}

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
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves" , "edu" , "markellekelly"
])

domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

max_file_size = 500 * 1024 * 1024

def scraper(url, resp):
    try:
        if is_valid(url):
            # politeness
            # time.sleep(2)
            if resp.text is not None and resp.headers is not None and 'Content-Length' in resp.headers:
                content_size = int(resp.headers['Content-Length'])
            else:
                content_size = None  # Handle the case where the header is missing

            if resp.status_code == 408:
                print("timeout")
                return []
            if resp.text is not None and resp.text is not None:
                if len(resp.text.strip()) == 0:
                    # empty
                    return []
            if resp.text is not None:
                if resp.headers is None:
                    return []
            if content_size is not None and content_size > max_file_size:
                return []
            
            # Fixes URL's having / at the end being different from not
            url = url.rstrip("/")

             # Update SUBDOMAINCOUNTER dictionary
            parsed_url = urlparse(url)
            # print("PARSED URL NETLOC", parsed_url.netloc)

            if parsed_url.netloc == "ics.uci.edu" or parsed_url.netloc.endswith(".ics.uci.edu"):
                print(parsed_url.netloc)
                # https://subdomain.ics.uci.edu
                # url_to_store = parsed_url.scheme +  ":!/" + parsed_url.netloc
                
                # Extract the subdomain part
                
                if parsed_url.netloc.rsplit('.')[0] == 'www':
                    # print("LINE 90")
                    subdomain = parsed_url.netloc.rsplit('.')[1]
                else:
                    subdomain = parsed_url.netloc.rsplit('.')[0]
                # print("SUBDOMAIN", subdomain)

                if subdomain != 'ics':
                    # If base ics.uci.edu, skip
                    # Increment count for the subdomain or initialize it if it doesn't exists
                    # subdomainCounts[url_to_store] = subdomainCounts.get(subdomain, 0) + 1
                    subdomainCounts[subdomain] = subdomainCounts.get(subdomain, 0) + 1

                    # print("SUBDOMAIN: ", subdomainCounts)

            # List of found links
            links = extract_next_links(url, resp)
            # print(links)

            # Links added to set to remove duplicates
            if links is not None:
                linkSet.update(links)
            else:
                print("No more links here! Moving on...")

            # print(list(linkSet))
            # print("LINK LENGTH: ", len(links))
            # print("Extracted Links:")

            # Find number of UNIQUE PAGES
            # uniquePages = len(linkSet)
            # print("Number of Unique Pages: ", uniquePages)
            
            # Store word count for the current URL; PAGEWORDCOUNTER
            if resp.text and resp.text is not None:
                content = resp.text
                pageWordCounts[url] = count_words(content)

                # Update WORDCOUNTER for each tokenized word, not including stop words
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

    # print("Sorted Subdomains: ", sorted_subdomains)

    # print(list(linkSet))
    # print(len(linkSet))

    # returns a list of links
    return list(linkSet)


def extract_next_links(url, resp):
    link_list = []
    # if resp.text is not None:
    #     if resp.text is not None:

    if resp.status_code == 200:
        try:
            # use BeautifulSoup library to parse the HTML content of the page
            # print("Raw Content: ", raw)

            content = resp.text
            # print("WORDS: ", count_words(content))
            
            if count_words(content) < 100:
                print("PAGE TOO SHORT!")
                return []

            soup = BeautifulSoup(content, 'html.parser')

            # body_content = soup.body.get_text(strip=True)
            # if not body_content:
            #     print("HTML DOES NOT CONTAIN TEXT IN BODY (extract_next_links)")
            #     return []

            # in the HTML, we want to find all '<a>' tags and extract the link, the 'href'
            for curr in soup.find_all('a'):
                link = curr.get('href')
                # print(link)
                if link is not None:
                    # we then use 'urllib.parse: urljoin' in order to combine the relative URL's with our base URL in order to get our final URL
                    url_joined = urljoin(url, link)

                    # Strip the trailing '/'
                    url_joined = url_joined.rstrip("/")
                    # print("URL JOINED: ", url_joined)

                    # Use 'urllibe.parse: urldefrag' to remove the fragment, as in this assignment we ignore the fragment 
                    if "#" in url_joined:
                        url_joined = urldefrag(url_joined).url
                   
                    final_url  = unquote(url_joined)
                    # print("FINAL URL", final_url)

                    # checks validity of our final_url - if it is valid, then we can add it to our list of links

                    # print(not_similar(final_url))
                    
                    if is_valid(final_url):
                        linkSet.add(final_url)
                        # print("Added ", final_url, " to link set!")

                        # if not_similar(final_url):


                        # https://vision.ics.uci.edu
                        # https://vision.ics.uci.edu/robots.txt

                        # https://vision.ics.uci.edu
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
                        link_list.append(final_url)
                        
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
                        #     print(url, "is too similar to add!")
                    else:
                        # print("CONTINUING LINE 269")
                        continue
                else:
                    # print("CONTINUING LINE 272 - LINK IS NONE")
                    continue
        except Exception as e:
            print("ERROR: Error parsing " + url + " - " + str(e)) 
            return []
    # if the response code was something other than 200, means there was an error - print it so we can see
    else:
        print("Error: " + str(resp.status_code))
        return

    # print("LIST IN EXTRACT: ", link_list)
    print("UNIQUE PAGES - ", len(linkSet))
    return link_list


# FUNCTION: is_valid(url) - checks the validity of a URL:str passed in - returns a boolean True or False
def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        #NEW ADD
        if not re.match(
            r'^(\w*.)(ics.uci.edu|cs.uci.edu|stat.uci.edu|informatics.uci.edu)$',parsed.netloc):
            return False
        if "?share=" in url:
            return False
        if "pdf" in url:
            return False
        if "redirect" in url:
            return False
        if "#comment" in url:
            return False
        if "#respond" in url:
            return False
        if "#comments" in url:
            return False
        if "filter" in url:
            return False
        if "calendar" in url:
            return False
        if "date" in url:
            return False
        if "stayconnected" in url:
            return False
        if "exclusion" in url:
            return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        #NEW ADD
        # can implement blacklist
        
        if url == "https://www.stat.uci.edu/covid19/index.html":
            return False

        # url = unquote(url)

        # List of disallowed file extensions
        # invalid = [
        #     "css", "js", "bmp", "gif", "jpg", "jpeg", "ico",
        #     "png", "tif", "tiff", "mid", "mp2", "mp3", "mp4",
        #     "wav", "avi", "mov", "mpeg", "ram", "m4v", "mkv", "ogg", "ogv", "pdf",
        #     "ps", "eps", "tex", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "names",
        #     "data", "dat", "exe", "bz2", "tar", "msi", "bin", "7z", "psd", "dmg", "iso",
        #     "epub", "dll", "cnf", "tgz", "sha1", "thmx", "mso", "arff", "rtf", "jar", "csv",
        #     "rm", "smil", "wmv", "swf", "wma", "zip", "rar", "gz" , "img", "war", "mpg" , "ipynb" , "ppsx"
        # ]

        # Check if the parsed domain matches any of the allowed domains
        # domain_check = any(parsed.netloc.endswith("." + domain) or parsed.netloc == domain for domain in domains)

        # pdf_check = "pdf" not in url.lower()

        # Check if the path doesn't have invalid extensions
        # extension_check = not any(parsed.path.lower().endswith("." + filetype) for filetype in invalid)

        # return the boolean expression determined by the logical AND of domain_match and extension_match
        # if the url exists in our valid domains and does not fall under any of the invalid extensions, return True, else return False

        # NEW ADD
        # return domain_check and extension_check and pdf_check
        return True
        # NEW ADD

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
    for tags in soup(['script','style']):
        tags.extract()
    
    # Get text
    newContent = soup.get_text()

    # Use regex to count the number of words in the content
    words = [word for word in re.findall(r'\w+', newContent) if not word.isnumeric()]

    return len(words)


def not_similar(url):
    parsed = urlparse(url)
    query_similarity = 0

    for stored_url, components in domainSet.items():
        domain_similarity = SequenceMatcher(None, parsed.netloc, components["netloc"]).ratio()
        path_similarity = SequenceMatcher(None, parsed.path, components["path"]).ratio()
        if domain_similarity == 1 and path_similarity > 0.6:
            return False
        if parsed.netloc == components["netloc"] and parsed.path == components["path"]:
            query_similarity = SequenceMatcher(None, parsed.query, components["query"]).ratio()
            
            if query_similarity >= 0.7:
                # If at least one item in domainSet has similar query, return False
                return False
        

    # If the loop finishes and no similar query was found, return True
    return True

#
#
# LOCAL DRIVER

def print_deliverables():
    if linkSet:
        print("NUMBER OF UNIQUE PAGES - ", len(linkSet))

    if pageWordCounts:
        longest_page_url = max(pageWordCounts, key=pageWordCounts.get)
        print("LONGEST PAGE URL - ", longest_page_url, " - WITH WORD COUNT: - ", pageWordCounts[longest_page_url])
    
    if wordCounter:
        most_common_words = wordCounter.most_common(50)
        print("50 MOST COMMON WORDS:", most_common_words)

    if sorted_subdomains:
        print("SORTED SUBDOMAINS: ", sorted_subdomains)
    else:
        print("NO SUBDOMAINS")

test_urls = [
    # These are all for validity checker
    # "https://www.ics.uci.edu/page",
    # "http://cs.uci.edu/page",
    # "https://informatics.uci.edu/page",
    # "https://stat.uci.edu/page",
    # "https://www.google.com/page",
    # "ftp://invalid-url.com/ftp-page",
    # "https://www.linkedin.com/feed/",
    # "https://drive.google.com/drive/u/0/my-drive",
    # "https://www.youtube.com/watch?v=_ITiwPMUzho&ab_channel=LofiGhostie",
    # "https://www.youtube.com/watch?v=TUEju_i3oWE&ab_channel=Insomniac",
    # "https://github.com/gregkhanoyan/IR23F-A2-G33#things-to-keep-in-mind",
    # "https://canvas.eee.uci.edu/courses/58552/assignments/1243743",
    # These are actual links that can be crawled
    # "https://ics.uci.edu/academics/undergraduate-academic-advising/",
    # "https://ics.uci.edu/academics/undergraduate-academic-advising/change-of-major/",
    # "https://grape.ics.uci.edu/wiki/public/wiki/cs122b-2019-winter",
    # "https://wics.ics.uci.edu/",
    "https://ics.uci.edu/events",
    # "https://sami.ics.uci.edu/"
]

while test_urls:
    url = test_urls.pop(0)  # Get the first URL from the list
    resp = requests.get(url)
    urlsss = scraper(url, resp)
    test_urls.extend(urlsss)  # Add the new URLs to the end of the list
    print(url)
print_deliverables()

# url1 = "https://wics.ics.uci.edu/events/2022-01-28/"
# url2 = "https://wics.ics.uci.edu/events/2022-02-19"
# url1 = "https://ics.uci.edu/happening/news/?filter%5Baffiliation_posts%5D=1990"
# url2 = "https://ics.uci.edu/happening/news/?filter%5Bresearch_areas_ics%5D=1994"
# url1 = "https://grape.ics.uci.edu/wiki/public/timeline?from=2019-03-13T22%3A33%3A25-07%3A00&precision=second"
# url2 = "https://grape.ics.uci.edu/wiki/public/timeline?from=2019-01-09T23%3A07%3A19-08%3A00&precision=second"

# test_urls = [
#     # These are all for validity checker
#     # "https://www.ics.uci.edu/page",
#     # "http://cs.uci.edu/page",
#     # "https://informatics.uci.edu/page",
#     # "https://stat.uci.edu/page",
#     # "https://www.google.com/page",
#     # "ftp://invalid-url.com/ftp-page",
#     # "https://www.linkedin.com/feed/",
#     # "https://drive.google.com/drive/u/0/my-drive",
#     # "https://www.youtube.com/watch?v=_ITiwPMUzho&ab_channel=LofiGhostie",
#     # "https://www.youtube.com/watch?v=TUEju_i3oWE&ab_channel=Insomniac",
#     # "https://github.com/gregkhanoyan/IR23F-A2-G33#things-to-keep-in-mind",
#     # "https://canvas.eee.uci.edu/courses/58552/assignments/1243743",
#     # These are actual links that can be crawled
#     "https://ics.uci.edu/academics/undergraduate-academic-advising/",
#     "https://ics.uci.edu/academics/undergraduate-academic-advising/change-of-major/",
#     "https://grape.ics.uci.edu/wiki/public/wiki/cs122b-2019-winter",

#     "http://www.ics.uci.edu",
#     "https://sami.ics.uci.edu/"
# ]

# for url in test_urls:
#     if is_valid(url):
#         print("Testing URL: " , url)
#         try:
#             resp = requests.get(url)
#         except:
#             print("Timeout")
#         # Store number of unique pages
#         links = extract_next_links(url, resp)

#         if links is not None:
#             for link in links:
#                 if link not in linkSet:
#                     test_urls.append(link)
#         else:
#             print("No more links here! Moving on...")

#         test_urls.remove(url)

#         print("Extracted Links:")
#         if(links is not None):
#             linkSet.update(links)
#             # Find number of unique pages
#             uniquePages = len(linkSet)
#             print("Number of Unique Pages: ", uniquePages)


#         # Store word count for the current URL
#         content = resp.text
#         pageWordCounts[url] = count_words(content)

#         # Update wordCounter for each tokenized word, not including stop words
#         tokens = tokenize(content)
#         for word in tokens:
#             if word not in stopWords:
#                 wordCounter[word] += 1

#         parsed_url = urlparse(url)
#         if parsed_url.netloc.endswith('ics.uci.edu'):
#             # Extract the subdomain part
#             subdomain = parsed_url.netloc.rsplit('.', 2)[0]

#             if subdomain == 'ics':
#                 subdomain = parsed_url.netloc.rsplit('.', 3)[1]

#             # Increment count for the subdomain or initialize it if it doesn't exists
#             subdomainCounts[subdomain] = subdomainCounts.get(subdomain, 0) + 1

#         # if links is not None:
#             # for link in links:
#         # if linkSet is not None:
#         #     for link in linkSet:
#         #         print(link)
#     else:
#         print(url, " is not a valid URL for crawling.")
