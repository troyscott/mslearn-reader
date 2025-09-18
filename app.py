import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import traceback

app = Flask(__name__)

class MSLearnParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.default_url = "https://learn.microsoft.com/en-us/training/modules/get-started-data-warehouse/"

    def fetch_module(self, url):
        """Fetch and parse a Microsoft Learning module"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self.parse_content(response.text, url)
        except Exception as e:
            raise Exception(f"Failed to fetch module: {str(e)}")

    def parse_content(self, html, base_url):
        """Parse HTML content and extract module structure"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Microsoft Learning Module"
        
        # Find navigation structure
        nav_sections = self.extract_navigation(soup)
        
        # Extract main content
        main_content = self.extract_main_content(soup, base_url)
        
        return {
            'title': title,
            'sections': nav_sections if nav_sections else [{'title': 'Main Content', 'content': main_content, 'id': 'main'}],
            'url': base_url
        }

    def extract_navigation(self, soup):
        """Extract navigation structure from Microsoft Learn module page"""
        sections = []
        
        # Look for the unit list following the correct path
        unit_list = soup.find('ul', {'id': 'unit-list'})
        
        if unit_list:
            units = unit_list.find_all('li', class_='module-unit')
            print(f"Found {len(units)} module units")
            
            for i, unit in enumerate(units):
                # Follow path: module-unit -> barLink -> a
                bar_link = unit.find('div', class_='barLink')
                if bar_link:
                    link = bar_link.find('a')
                    if link:
                        title = link.get_text().strip()
                        href = link.get('href', '')
                        print(f"Unit {i}: title='{title}', href='{href}'")
                        
                        if title and len(title) > 3:
                            sections.append({
                                'title': title,
                                'content': '',
                                'id': f'section-{i}',
                                'href': href
                            })
        
        # Fallback if no units found
        if not sections:
            print("No module units found, using fallback")
            sections = [
                {'title': 'Introduction', 'content': '', 'id': 'section-0', 'href': '#intro'},
                {'title': 'Main Content', 'content': '', 'id': 'section-1', 'href': '#main'}
            ]
        
        print(f"Final sections found: {[s['title'] for s in sections]}")
        return sections

    def extract_main_content(self, soup, base_url):
        """Extract and clean main content"""
        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            elem.decompose()
        
        # Find main content area
        content_selectors = [
            'main',
            '[role="main"]',
            '.content',
            '.main-content',
            'article',
            '.markdown-body'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Clean and format content
        return self.clean_content(main_content, base_url)

    def clean_content(self, content, base_url):
        """Clean and format content for display"""
        if not content:
            return "<p>No content found</p>"
        
        # Convert to string and clean
        html_content = str(content)
        
        # Fix relative URLs
        html_content = self.fix_relative_urls(html_content, base_url)
        
        # Parse and clean structure
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Debug: Check for images before cleaning
        images = soup.find_all('img')
        print(f"DEBUG: Found {len(images)} images in content")
        for i, img in enumerate(images):
            print(f"  Image {i}: src='{img.get('src')}', alt='{img.get('alt')}'")
        
        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            elem.decompose()
        
        # Remove empty paragraphs and divs (but preserve those with images)
        for elem in soup.find_all(['p', 'div']):
            if not elem.get_text().strip() and not elem.find('img'):
                elem.decompose()
        
        # Remove the first h1 to avoid duplicate titles
        first_h1 = soup.find('h1')
        if first_h1:
            first_h1.decompose()
        
        # Remove achievement boxes, progress indicators, and completion sections
        for elem in soup.find_all(['div'], class_=['achievements', 'progress', 'completion', 'module-completion']):
            elem.decompose()
        
        # Clean attributes but keep essential ones
        for elem in soup.find_all():
            allowed_attrs = ['href', 'src', 'alt', 'title', 'class', 'colspan', 'rowspan', 'data-linktype']
            elem.attrs = {k: v for k, v in elem.attrs.items() if k in allowed_attrs}
        
        # Debug: Check for images after cleaning
        final_images = soup.find_all('img')
        print(f"DEBUG: {len(final_images)} images after cleaning")
        for i, img in enumerate(final_images):
            print(f"  Final Image {i}: src='{img.get('src')}', alt='{img.get('alt')}'")
        
        return str(soup)

    def extract_section_content(self, soup, heading):
        """Extract content following a heading"""
        content_parts = []
        current = heading.next_sibling
        
        while current:
            if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3']:
                break
            
            if hasattr(current, 'name') and current.name in ['p', 'ul', 'ol', 'div', 'pre', 'blockquote']:
                content_parts.append(str(current))
            
            current = current.next_sibling
        
        return ''.join(content_parts) if content_parts else ''

    def fix_relative_urls(self, html, base_url):
        """Fix relative URLs to absolute ones"""
        soup = BeautifulSoup(html, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src')
            print(f"Found image src: '{src}'")
            if src and not src.startswith(('http', 'data:')):
                if src.startswith('../'):
                    # Use urljoin with the section URL to properly resolve relative paths
                    new_src = urljoin(base_url, src)
                    print(f"Converting relative image: {src} -> {new_src}")
                    img['src'] = new_src
                else:
                    new_src = urljoin(base_url, src)
                    print(f"Converting image: {src} -> {new_src}")
                    img['src'] = new_src
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and not href.startswith(('http', '#', 'mailto:')):
                link['href'] = urljoin(base_url, href)
        
        return str(soup)

    def fetch_section_content(self, section_url):
        """Fetch content from a specific section/unit page"""
        try:
            print(f"Fetching section from: {section_url}")
            response = self.session.get(section_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for main content area
            main_content = soup.find('main') or soup.find('[role="main"]')
            if not main_content:
                # Try other content selectors
                main_content = soup.find('div', class_='content') or soup.find('article')
            
            if main_content:
                print(f"Found main content, processing...")
                return self.clean_content(main_content, section_url)
            else:
                print("No main content found")
                return "<p>Content not found on this page</p>"
                
        except Exception as e:
            print(f"Error in fetch_section_content: {e}")
            raise Exception(f"Failed to fetch section content: {str(e)}")

# Initialize parser
parser = MSLearnParser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load-module', methods=['POST'])
def load_module():
    url = request.form.get('url', '').strip()
    
    if not url:
        return '<div class="error">Please provide a valid URL</div>', 400
    
    if not ('learn.microsoft.com' in url or 'docs.microsoft.com/learn' in url):
        return '<div class="error">Please provide a valid Microsoft Learning URL</div>', 400
    
    try:
        print(f"Attempting to load URL: {url}")
        module_data = parser.fetch_module(url)
        print(f"Module data loaded: {len(module_data['sections'])} sections found")
        
        # Return both navigation and content
        nav_html = render_template('navigation.html', sections=module_data['sections'], url=url)
        content_html = render_template('content.html', 
                                     content=module_data['sections'][0]['content'] if module_data['sections'] else '',
                                     title=module_data['title'])
        
        return f'''
        <div hx-swap-oob="innerHTML:#navigation">{nav_html}</div>
        <div hx-swap-oob="innerHTML:#main-content">{content_html}</div>
        <div class="success">Module loaded successfully!</div>
        '''
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error loading module: {error_msg}")
        print(traceback.format_exc())
        return f'<div class="error">Error: {error_msg}</div>', 500

@app.route('/load-section')
def load_section():
    section_id = request.args.get('section_id')
    url = request.args.get('url')
    
    print(f"=== LOAD SECTION DEBUG ===")
    print(f"section_id: {section_id}")
    print(f"url: {url}")
    
    if not section_id:
        return '<div class="error">Missing section ID</div>', 400
    
    try:
        section_index = int(section_id.split('-')[-1]) if 'section-' in section_id else 0
        print(f"section_index: {section_index}")
        
        if url:
            print("Re-fetching module data...")
            module_data = parser.fetch_module(url)
            print(f"Module has {len(module_data['sections'])} sections")
            
            if section_index < len(module_data['sections']):
                section = module_data['sections'][section_index]
                print(f"Loading section {section_index}: {section['title']}")
                print(f"Section href: '{section['href']}'")
                
                # If section has an href, fetch that page's content
                if section['href'] and not section['href'].startswith('#'):
                    print("Section has valid href, building URL...")
                    # Convert relative URL to absolute
                    if section['href'].startswith('/'):
                        section_url = 'https://learn.microsoft.com' + section['href']
                    else:
                        section_url = urljoin(url, section['href'])
                    
                    print(f"Original href: {section['href']}")
                    print(f"Full section URL: {section_url}")
                    print(f"Attempting to fetch content...")
                    
                    try:
                        section_content = parser.fetch_section_content(section_url)
                        print(f"Content fetched successfully, length: {len(section_content)}")
                        return render_template('content.html', 
                                             content=section_content, 
                                             title=section['title'])
                    except Exception as e:
                        print(f"Error fetching section content: {e}")
                        print(f"Full traceback: {traceback.format_exc()}")
                        return render_template('content.html', 
                                             content=f"<p>Error loading content for {section['title']}: {str(e)}</p>", 
                                             title=section['title'])
                else:
                    print(f"No valid href found for section: '{section['href']}'")
                
                # Use stored content if available
                print("Using fallback content")
                content = section['content'] if section['content'] else f"<p>Content for {section['title']}</p>"
                return render_template('content.html', content=content, title=section['title'])
            else:
                print(f"Section index {section_index} out of range")
        
        return '<div class="error">Section not found</div>', 404
            
    except Exception as e:
        print(f"Exception in load_section: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return f'<div class="error">Error loading section: {str(e)}</div>', 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))