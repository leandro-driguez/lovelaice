import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
from urllib.parse import urlparse
import os
from openai import OpenAI

def extract_main_content(html, url, query):
    """Extract the main content from an HTML page using an LLM."""
    try:
        # Try to get a title from the HTML using BeautifulSoup
        # This is still useful for context
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "Unknown Title"
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Remove some HTML boilerplate to reduce token usage
        # This is a simple clean-up, not full parsing
        for tag in ['script', 'style', 'svg', 'path', 'footer', 'header', 'nav']:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Get cleaned HTML
        cleaned_html = str(soup)
        return cleaned_html
#         # Construct the prompt for the LLM
#         prompt = f"""
# Task: Extract the most useful and relevant information from this webpage related to the search query.

# # Search Query: {query}
# # Webpage URL: {url}
# # Webpage Title: {title}

# # Instructions:
# # 1. Focus only on content directly relevant to the search query
# # 2. Extract key facts, definitions, explanations, and important details
# # 3. Organize the information in a coherent way
# # 4. Ignore navigation elements, ads, footers, headers, and other irrelevant parts
# # 5. If there's no relevant information, state that clearly

# # Do not rewrite the information, just extract information.

# # HTML Content:
# # {cleaned_html}

# # Extracted Information:
# # """
        
#         # Call the LLM API
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",  # or whatever model is available/preferred
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant, specialized content extraction. Your task is to extract all the relevant information from webpage HTML based on a search query."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3  # Keep temperature low for more factual extraction
#         )
        
#         # Get the extracted content from the response
#         extracted_text = response.choices[0].message.content
        
#         return extracted_text
    
    # except Exception as e:
    #     return f"Error extracting content via LLM: {str(e)}"

def fetch_webpage(url, timeout=10):
    """Fetch the webpage content with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        return response.text
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.TooManyRedirects:
        return None, "Too many redirects"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"

def is_safe_url(url):
    """Check if a URL is likely safe to request."""
    parsed = urlparse(url)
    # Avoid file:// URLs and localhost
    if parsed.scheme == 'file' or parsed.netloc in ['localhost', '127.0.0.1']:
        return False
    return True

def run_search():
    optimized_query = "deep research open source"
    
    print(f"Searching for: {optimized_query}\n")
    search_results = []
    
    count = 0
    for result in search(optimized_query, sleep_interval=2, num_results=5, advanced=True):
        print(f"\n{count+1}. {result.title}\n   {result.url}")
        
        if is_safe_url(result.url):
            print("   Fetching content...")
            
            # Fetch the webpage content
            html_content = fetch_webpage(result.url)
            
            if html_content:
                # Extract useful text from the webpage - pass the query now
                extracted_text = extract_main_content(html_content, result.url, optimized_query)
                
                # Store the result including the extracted content
                result_with_content = {
                    'title': result.title,
                    'url': result.url,
                    'content': extracted_text
                }
                search_results.append(result_with_content)
                
                # Print a preview of the extracted content
                preview = extracted_text[:500].replace('\n', ' ')
                if len(extracted_text) > 500:
                    preview += "..."
                print(f"   Content preview: {preview}")
            else:
                print(f"   Failed to fetch content")
                search_results.append({
                    'title': result.title,
                    'url': result.url,
                    'content': "Failed to fetch content"
                })
        else:
            print("   Skipping fetch: URL appears unsafe")
            
        count += 1
        # Short delay between requests to be respectful
        time.sleep(1)
    
    print("\nSearch completed with information extraction.")
    return search_results

if __name__ == "__main__":
    results = run_search()
    print("\n\n")

    for result in results:
        print(result['title'])
        print(result['url'])
        print(result['content'])
        print("\n\n")