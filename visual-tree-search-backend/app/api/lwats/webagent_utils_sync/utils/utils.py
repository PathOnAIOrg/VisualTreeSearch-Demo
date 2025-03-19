import base64
import os
import json
import logging
from openai import OpenAI
from PIL import Image
from io import BytesIO
import requests
from dotenv import load_dotenv
_ = load_dotenv()

logger = logging.getLogger(__name__)
openai_client = OpenAI()


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_task_file(file_name):
    """
    Load and parse task information from a file.
    
    Args:
        file_name (str): Name of the file to read
        
    Returns:
        dict: Dictionary containing:
            - goal: The task goal (str)
            - starting_url: The initial URL (str)
            - step_info: Parsed JSON step information (dict)
            
    Raises:
        FileNotFoundError: If the file cannot be found
        ValueError: If file format is invalid or JSON parsing fails
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            # Split content into lines and remove empty lines
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {file_name}")
    
    # Extract goal and starting URL
    goal = lines[0]
    starting_url = lines[1]
    
    # Parse each remaining line as a separate JSON step
    steps = []
    for i, line in enumerate(lines[2:]):
        try:
            step_info = json.loads(line)
            steps.append(step_info)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format on line {i}: {str(e)}")
    
    return {
        "goal": goal,
        "starting_url": starting_url,
        "step_info": steps
    }

def query_openai_model(system_msg, prompt, screenshot, num_outputs):
    # base64_image = encode_image(screenshot_path)
    base64_image = base64.b64encode(screenshot).decode('utf-8')

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",
             "content": [
                 {"type": "text", "text": prompt},
                 {"type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}",
                      "detail": "high"
                  }
                  }
             ]
             },
        ],
        n=num_outputs
    )

    answer: list[str] = [x.message.content for x in response.choices]
    return answer


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def search_interactive_elements(interactive_elements, extracted_number):
    for element in interactive_elements:
        if element.get('bid') == extracted_number:
            return {
                'text': element.get('text'),
                'type': element.get('type'),
                'tag': element.get('tag'),
                'id': element.get('id'),
                'href': element.get('href'),
                'title': element.get('title'),
                'ariaLabel': element.get('ariaLabel')
            }
    return {}  # Return empty dictionary if no matching element is found

def locate_element(page, extracted_number: str):
    """
    Safely locate and extract information about an element using data-unique-test-id or id for initial location,
    but generates a robust unique selector using standard attributes and structure.
    
    Args:
        page: Playwright page object
        extracted_number: ID or data-unique-test-id to search for
        
    Returns:
        dict: Element information including a unique selector or empty dict if not found
    """
    try:
        # Define selectors for potentially interactive elements
        selectors = [
            'a', 'button', 'input', 'select', 'textarea', 'summary', 
            'video', 'audio', 'iframe', 'embed', 'object', 'menu', 
            'label', 'fieldset', 'datalist', 'output', 'details', 
            'dialog', 'option', '[role="button"]', '[role="link"]', 
            '[role="checkbox"]', '[role="radio"]', '[role="menuitem"]', 
            '[role="tab"]', '[tabindex]', '[contenteditable="true"]'
        ]
        
        # Verify page is valid
        if not page or not page.evaluate('() => document.readyState') == 'complete':
            print("Page is not ready or invalid")
            return {}
            
        # Search for element by data-unique-test-id or ID first
        element = page.query_selector(f'[data-unique-test-id="{extracted_number}"], [id="{extracted_number}"]')
        
        # If not found, search through individual selectors
        if not element:
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if not elements:
                        continue
                        
                    for el in elements:
                        bid = el.get_attribute('data-unique-test-id') or el.get_attribute('id') or ''
                        if bid == extracted_number:
                            element = el
                            break
                    if element:
                        break
                except Exception as e:
                    print(f"Error searching selector {selector}: {str(e)}")
                    continue
        
        if not element:
            print(f"No element found with ID {extracted_number}")
            return {}
        
        # Extract element properties
        result = {}
        try:
            # Extract common attributes
            result = {
                'text': element.inner_text(),
                'type': element.get_attribute('type'),
                'tag': element.evaluate('el => el.tagName.toLowerCase()'),
                'id': element.get_attribute('id'),
                'href': element.get_attribute('href'),
                'title': element.get_attribute('title'),
                'ariaLabel': element.get_attribute('aria-label'),
                'name': element.get_attribute('name'),
                'value': element.get_attribute('value'),
                'placeholder': element.get_attribute('placeholder'),
                'class': element.get_attribute('class'),
                'role': element.get_attribute('role')
            }
            
            # Generate a unique selector for the element
            unique_selector = element.evaluate("""
                el => {
                    // Escape special characters in class names
                    const escapeClassName = (className) => {
                        return className.replace(/[:()[\]]/g, '\\\\$&')
                                      .replace(/\\n/g, '\\\\n')
                                      .replace(/\"/g, '\\\\"');
                    };
                    
                    const getPath = (el) => {
                        if (!el) return '';
                        
                        // Try ID, but skip framework-generated IDs
                        if (el.id) {
                            // List of framework-specific patterns to avoid
                            const frameworkPatterns = [
                                'mantine',    // Mantine framework
                                'tailwind',   // Tailwind framework
                                'mui',       // Material UI
                                'ant',       // Ant Design
                                'chakra',    // Chakra UI
                                'radix',     // Radix UI
                                'nextui',    // NextUI
                                'headless',  // Headless UI
                                'vue',       // Vue.js generated IDs
                                'react',     // React generated IDs
                                'angular'    // Angular generated IDs
                            ];
                            
                            // Check if the ID contains any framework patterns
                            const containsFrameworkPattern = frameworkPatterns.some(pattern => 
                                el.id.toLowerCase().includes(pattern.toLowerCase())
                            );
                            
                            // Only use the ID if it doesn't contain framework patterns
                            if (!containsFrameworkPattern) {
                                return `#${escapeClassName(el.id)}`;
                            }
                        }
                         
                        // Try name attribute
                        if (el.getAttribute('name')) {
                            const nameSelector = `[name="${el.getAttribute('name')}"]`;
                            if (document.querySelectorAll(nameSelector).length === 1) {
                                return nameSelector;
                            }
                        }
                        
                        // Try role
                        if (el.getAttribute('role')) {
                            const roleSelector = `[role="${el.getAttribute('role')}"]`;
                            if (document.querySelectorAll(roleSelector).length === 1) {
                                return roleSelector;
                            }
                        }
                        
                        // Try building selector with tag and attributes
                        const tagName = el.tagName.toLowerCase();
                        let selector = tagName;
                        
                        // Add available attributes
                        const attrs = {
                            'type': el.getAttribute('type'),
                            'placeholder': el.getAttribute('placeholder'),
                            'title': el.getAttribute('title'),
                            'aria-label': el.getAttribute('aria-label')
                        };
                        
                        Object.entries(attrs).forEach(([key, value]) => {
                            if (value) selector += `[${key}="${value}"]`;
                        });
                        
                        // Get position among siblings
                        const parent = el.parentElement;
                        if (!parent) return selector;
                        
                        const siblings = Array.from(parent.children);
                        const sameTagSiblings = siblings.filter(e => e.tagName === el.tagName);
                        const index = sameTagSiblings.indexOf(el) + 1;
                        const nthSelector = sameTagSiblings.length > 1 ? `:nth-of-type(${index})` : '';
                        
                        // Build path
                        const parentPath = getPath(parent);
                        return `${parentPath} > ${selector}${nthSelector}`;
                    };
                    
                    try {
                        // First attempt: get path without classes
                        let selector = getPath(el);
                        if (document.querySelectorAll(selector).length === 1) {
                            return selector;
                        }
                        
                        // If not unique, try adding individual non-complex classes
                        if (el.className) {
                            const classes = Array.from(el.classList)
                                .filter(cls => !cls.includes('(') && !cls.includes(':'));  // Filter out complex classes
                            
                            if (classes.length > 0) {
                                const baseSelector = selector.split(':nth-of-type')[0];  // Remove nth-of-type if present
                                selector = `${baseSelector}.${classes.join('.')}`;
                                
                                // Verify it's valid and unique
                                document.querySelectorAll(selector);  // This will throw if invalid
                                if (document.querySelectorAll(selector).length === 1) {
                                    return selector;
                                }
                            }
                        }
                        
                        // If still not unique, return the structural selector
                        return getPath(el);
                    } catch (e) {
                        // If any error occurs, fall back to structural selector
                        return getPath(el);
                    }
                }
            """)
            result['unique_selector'] = unique_selector
            
            # Validate the selector returns exactly one element
            try:
                validation_count = page.evaluate(f"""
                    () => document.querySelectorAll(`{unique_selector}`).length
                """)
                
                if validation_count != 1:
                    print(f"Warning: Generated selector matches {validation_count} elements")
                    result['selector_uniqueness_validated'] = False
                else:
                    result['selector_uniqueness_validated'] = True
            except Exception as e:
                print(f"Error validating selector: {str(e)}")
                result['selector_uniqueness_validated'] = False
            
            # Clean up None values
            result = {k: v for k, v in result.items() if v is not None}
                    
            print(f"locate_element result: {result}")
            return result
            
        except Exception as e:
            print(f"Error extracting element properties: {str(e)}")
            return {}
                
    except Exception as e:
        print(f"Error in locate_element: {str(e)}")
        return {}

def parse_function_args(function_args):
    if not function_args or not isinstance(function_args, list):
        return None
    first_arg = function_args[0]
    return first_arg if isinstance(first_arg, str) and first_arg.replace('.', '', 1).isdigit() else None


def append_to_steps_json(result, file_path):
    json_line = json.dumps(result)
    with open(file_path, 'a') as file:
        file.write(json_line + '\n')
    print(f"Appended result to {file_path}")

def url_to_b64(image_url: str) -> str:
    # Download the image from URL
    response = requests.get(image_url)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    # Open image using PIL
    img = Image.open(BytesIO(response.content))
    
    # Convert to base64
    with BytesIO() as image_buffer:
        img.save(image_buffer, format="PNG")
        byte_data = image_buffer.getvalue()
        img_b64 = base64.b64encode(byte_data).decode("utf-8")
        img_b64 = "data:image/png;base64," + img_b64
    
    return img_b64

def urls_to_images(urls: list[str]) -> list[str]:
    images = []
    for url in urls:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Open image using PIL
        img = Image.open(BytesIO(response.content))
        
        # Convert to base64
        with BytesIO() as image_buffer:
            img.save(image_buffer, format="PNG")
            byte_data = image_buffer.getvalue()
            images.append(byte_data)
    return images