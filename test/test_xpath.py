import requests
from bs4 import BeautifulSoup
from lxml import html
import cssselect
import time
import concurrent.futures


def benchmark_scraping_methods(url, selector):
    """
    Benchmark different scraping methods for a given URL and selector
    """

    def measure_time(func):
        start = time.time()
        result = func()
        return time.time() - start, result

    # Method 1: BeautifulSoup with CSS selectors
    def bs4_css():
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.select(selector)

    # Method 2: BeautifulSoup with find/find_all
    def bs4_find():
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Parse selector to determine method (this is a simplified example)
        if '.' in selector:
            return soup.find_all(class_=selector.replace('.', ''))
        elif '#' in selector:
            return soup.find(id=selector.replace('#', ''))
        else:
            return soup.find_all(selector)

    # Method 3: lxml with XPath
    def lxml_xpath():
        response = requests.get(url)
        tree = html.fromstring(response.content)
        # Convert CSS to XPath
        xpath = cssselect.GenericTranslator().css_to_xpath(selector)
        return tree.xpath(xpath)

    # Method 4: lxml with CSS selectors
    def lxml_css():
        response = requests.get(url)
        tree = html.fromstring(response.content)
        return tree.cssselect(selector)

    # Method 5: Parallel processing with BS4
    def parallel_bs4():
        def process_chunk(content):
            soup = BeautifulSoup(content, 'html.parser')
            return soup.select(selector)

        response = requests.get(url)
        # Split content into chunks for parallel processing
        chunk_size = len(response.content) // 4
        chunks = [response.content[i:i + chunk_size]
                  for i in range(0, len(response.content), chunk_size)]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_chunk, chunks))
        return [item for sublist in results for item in sublist]

    # Run benchmarks
    results = {}
    methods = {
        'BeautifulSoup (CSS)': bs4_css,
        'BeautifulSoup (find)': bs4_find,
        'lxml (XPath)': lxml_xpath,
        'lxml (CSS)': lxml_css,
        'Parallel BS4': parallel_bs4
    }

    for name, method in methods.items():
        try:
            duration, elements = measure_time(method)
            results[name] = {
                'duration': duration,
                'elements_found': len(elements)
            }
        except Exception as e:
            results[name] = {
                'duration': None,
                'error': str(e)
            }

    return results


# Example usage
if __name__ == "__main__":
    url = "https://acme-test.uipath.com/login"
    selector = "div.content"
    results = benchmark_scraping_methods(url, selector)

    print("\nBenchmark Results:")
    for method, data in results.items():
        if 'duration' in data and data['duration']:
            print(f"{method}:")
            print(f"  Time: {data['duration']:.4f} seconds")
            print(f"  Elements found: {data['elements_found']}")
        else:
            print(f"{method}:")
            print(f"  Error: {data['error']}")