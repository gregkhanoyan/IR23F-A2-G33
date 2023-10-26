How We Take a W On This Project
==============
    
# Current Code Breakdown:

  Currently, the driver code at the bottom first takes a list of URL's to test. The first marked portion of those URL's
  are invalid URL's used to test the 'is_valid(url)' function, which works as so:

  **is_valid(url):**
  
      The function takes a URL 'url' of type string. It then parses the URL into a URL scheme object, which basically means it is now an object with
      recognized URL structure, 'parsed'. We check if it is not an 'http' or 'https' URL, and if it is not, we return False.

      Next, we recognize a list of invalid filetype extensions we want to ignore, which was provided in the skeleton code. We also recognize a list of
      valid domains we can crawl in. These are the ones provided to us by the assignment specifications. 

      We then check whether or not the parsed URL object we created, 'parsed' contains the valid domains we can crawl in. We do this by checking the network
      location aspect of the URL, 'netloc', and checking if it ends with .'domain', or if it simply exists here, whatever the valid domain in this case may be.
      We do the same for checking if any extensions are invalid.

      Next, we return the boolean expression determined by the logical AND of domain_check and extension_check. 
      If the url exists in our valid domains and does not fall under any of the invalid extensions, return True, else return False.
   
  The driver code iterates through each URL in the testing list and uses the 'requests' library to retrieve a 'Response' object, which we need for our HTML parsing.
  We pass this 'Response' object, 'resp' and a string URL 'url', into the 'extract_next_links(url, resp)' function, which works as so:

  **extract_next_links(url, resp):**
  
      We first create an empty list to store our list of links, 'link_list'. We then check for a valid status code of 200, which means we successfully retrieve the
      page we want. 
      
      Next we use the BeautifulSoup library to parse the request HTML, using 'resp.text' as our source parameter to be parsed through. Our goal of this
      function is to extract every link from this webpage, so we need to find every element in the HTML with an <a> tag, as that corresponds to an href (HTML hyperlink).
      For every <a> tag, we want to return the corresponding href. 
      
      We then 'urllib.parse: urljoin' in order to combine the relative URL's with our base URL in order to get our final URL (a bit confused on this, need more 
      explanation on what this means lmao). 

      We then defragment the URL, that is, remove everything after any "#" characters in the URL, as we ignore fragments for this assignment.

      Finally, we check the validity of our final URL, by using the 'is_valid(url)' function. If the URL is valid, we can append it to our list of URL's, 'link_list'.

      We check for errors and finally return our list of links/URL's, extracting from each page/URL we are parsing, as 'link_list'.

  We then print all of the links just to see our code in action and ensure everything looks good.
  We also print whether or not a link is valid and can be crawled.

  **NEED TO DO:**

  ***MISC.***
  - Deal with duplicate links in 'extract_next_links(url, resp)' function

 # Deliverables:
 
  - Determine how many unique pages we found (unique = URL - fragment)
      - should be easy, since we already defragment in 'extract_next_links(url, resp)'
  - Determine the longest page in terms of the number of words (HTML markup doesn't count as words)
      - Need to find a way to calculate word number without HTML markup code
      - can def use some library for this (explore BeautifulSoup)
      - Word Length count printed?
  - Determine the 50 most common words in the entire set of pages crawled under these domains. Submit list in order of frequency
      - Use Assignment 1 Code
      - Ignore "English Stop Words: https://www.ranks.nl/stopwords"
  - Determine how many subdomains we found in the 'ics.uci.edu' domain. Submit list of subdomains ordered alphabetically and 
  number of unique pages detected in each subdomain. 
      - Content should be like so: {URL, number} e.g. {http://vision.ics.edu, 10}
  
  
  **Scraper Function:**
  
  I feel like some of what needs to be in the 'scraper(url, resp)' function is already in 'extract_next_links(url, resp)'.
      
  I will look soon and try to move it around. This is what the scraper function is supposed to do:
      
  - Receive a URL and corresponding Web Response (url, resp)
  - Parse the Web Response
      - extract information from the page (if valid) to answer deliverable questions above ^^^^
      - return a list of URL's scrapped from that page
          - make sure to only return URL's that are within the domains allowed (is_valid(url) function deals w/ this)
          - Defragment URL's - done in 'extract_next_links(url, resp)' but triple check cuz this is major
  
  **Politeness**
  
  I haven't even looked at what we need to do to obey politeness rules.
      
  - Learn how to implement robots.txt politeness policies
  
  # Check for a Correct Crawl - HARD PART - READ ALL!
  
  - Honor politeness delay for each site (robots.txt)
  - Crawl all pages with high textual information content
      - not sure what defines high here
  - Detect and avoid infinite traps
  - Detect and avoid sets of similar pages w/ no information
      - Decide and discuss a reasonable definition for low information page + defend it in the TA talk
  - Detect redirects and if the page redirects your crawler, index the redirected content
  - Detect and avoid deal URL's that return a 200 status but no data
      - https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html                   could be useful here
  - Detect and avoid crawling very large files, esp. if they have low information content
  - Transform relative URL's to absolute URL's - I think I did this in 'extract_next_links(url, resp)'
  - Ensure we send the server a request with ASCII URL
      - make sure that the URL being requested is ics.uci.edu, not <a href="ics.uci.edu">
  - Write simple automatic trap detection systems (???)
  - Use openlab/tmux (??? on tmux, never used it before)
  
  ***CRAWLER MUST BEHAVE CORRECTLY BY:*** Friday, 10/27 by 9:00 PM
  
  ***DEPLOYMENT STAGE:*** Monday, 10/30 to Friday, 11/3 by 9:00 PM
      - Crawler must crawl 3 times during deployment stage