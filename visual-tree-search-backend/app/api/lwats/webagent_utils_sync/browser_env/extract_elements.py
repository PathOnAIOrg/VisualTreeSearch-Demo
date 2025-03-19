import logging
import time
from playwright.sync_api import Page
from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR

logger = logging.getLogger(__name__)

class MarkingError(Exception):
    pass

def extract_interactive_elements(page: Page):
    """
    Synchronously locates and returns a list of interactive elements (with bounding box info, text, etc.)
    filtered by the custom browsergym ID attribute.
    """
    # Example usage of query_selector in sync mode
    ddelement = page.query_selector(f'[data-unique-test-id="{2020}"], [id="{2020}"]')

    js_code = """
    (browsergymIdAttribute) => {
        const customCSS = `
            ::-webkit-scrollbar {
                width: 10px;
            }
            ::-webkit-scrollbar-track {
                background: #27272a;
            }
            ::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 0.375rem;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        `;

        const styleTag = document.createElement("style");
        styleTag.textContent = customCSS;
        document.head.append(styleTag);

        function generateSelector(element) {
            let selector = element.tagName.toLowerCase();
            if (element.id) {
                selector += `#${element.id}`;
            } else {
                if (typeof element.className === 'string' && element.className.trim()) {
                    selector += `.${element.className.trim().split(/\\s+/).join('.')}`;
                }
                let sibling = element;
                let nth = 1;
                // Fixed while loop:
                while ((sibling = sibling.previousElementSibling)) {
                    if (sibling.tagName.toLowerCase() === selector.split('.')[0]) nth++;
                }
                if (nth > 1) {
                    selector += `:nth-of-type(${nth})`;
                }
            }
            return selector;
        }

        function isInteractive(element) {
            const interactiveTags = [
                'a', 'button', 'input', 'select', 'textarea', 'summary', 'video', 'audio',
                'iframe', 'embed', 'object', 'menu', 'label', 'fieldset', 'datalist', 'output',
                'details', 'dialog', 'option', 'cu-user-item'
            ];
            const interactiveRoles = [
                'button', 'link', 'checkbox', 'radio', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
                'option', 'listbox', 'textbox', 'combobox', 'slider', 'spinbutton', 'scrollbar',
                'tabpanel', 'treeitem', 'switch', 'searchbox', 'grid', 'gridcell', 'row',
                'rowgroup', 'rowheader', 'columnheader', 'tab', 'tooltip', 'application',
                'dialog', 'alertdialog', 'progressbar'
            ];

            return interactiveTags.includes(element.tagName.toLowerCase()) ||
                   interactiveRoles.includes(element.getAttribute('role')) ||
                   element.onclick != null ||
                   element.onkeydown != null ||
                   element.onkeyup != null ||
                   element.onkeypress != null ||
                   element.onchange != null ||
                   element.onfocus != null ||
                   element.onblur != null ||
                   element.getAttribute('tabindex') !== null ||
                   element.getAttribute('contenteditable') === 'true';
        }

        function getRealBoundingClientRect(element) {
            const rect = element.getBoundingClientRect();
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            return {
                top: rect.top + scrollTop,
                left: rect.left + scrollLeft,
                right: rect.right + scrollLeft,
                bottom: rect.bottom + scrollTop,
                width: rect.width,
                height: rect.height
            };
        }

        // Get full document dimensions
        const docHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.offsetHeight,
            document.body.clientHeight,
            document.documentElement.clientHeight
        );
        const docWidth = Math.max(
            document.body.scrollWidth,
            document.documentElement.scrollWidth,
            document.body.offsetWidth,
            document.documentElement.offsetWidth,
            document.body.clientWidth,
            document.documentElement.clientWidth
        );

        var items = Array.prototype.slice
            .call(document.querySelectorAll("*"))
            .map(function (element) {
                var bid = element.getAttribute(browsergymIdAttribute) || "";

                // Only process elements with a non-empty browsergymIdAttribute AND that are interactive
                if (bid === "" || !isInteractive(element)) {
                    return null;
                }

                var textualContent = element.textContent.trim().replace(/\\s{2,}/g, " ");
                var elementType = element.tagName.toLowerCase();
                var ariaLabel = element.getAttribute("aria-label") || "";

                // Get real position including scroll
                var realRect = getRealBoundingClientRect(element);
                var rects = [{
                    left: realRect.left,
                    top: realRect.top,
                    right: realRect.right,
                    bottom: realRect.bottom,
                    width: realRect.width,
                    height: realRect.height
                }];

                var area = realRect.width * realRect.height;

                return {
                    include: true,
                    area: area,
                    rects: rects,
                    text: textualContent,
                    type: elementType,
                    ariaLabel: ariaLabel,
                    bid: bid,
                    tag: elementType,
                    id: element.id || null,
                    class: typeof element.className === 'string' ? element.className : null,
                    href: element.getAttribute("href") || null,
                    title: element.getAttribute("title") || null
                };
            })
            .filter((item) => item !== null && item.area >= 20);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x !== y && document.querySelector(`[id="${y.bid}"]`) && document.querySelector(`[id="${y.bid}"]`).contains(document.querySelector(`[id="${x.bid}"]`)))
        );

        return items;
    }
    """

    # Evaluate the JS code in a synchronous manner
    return page.evaluate(js_code, BID_ATTR)

def highlight_elements(page: Page, elements, max_retries=3, retry_delay=1000):
    """
    Synchronously highlights elements that are actually visible on the page, with the same logic:
      - If the element's tag name is <cu-user-item>, skip the topmost covering check and highlight anyway.
      - Otherwise:
        - Not scrolled out of view
        - Not display:none or visibility:hidden
        - Not completely covered by another element at the center of its bounding box
        - Ignores any element (and its ancestors) that has 'overlay' in their class name
        - Ignores any element (and its ancestors) that has an attribute named '_ngcontent-ng-c1666608104'
    """

    js_code = r"""
    (elements) => {
        // --- Setup / Cleanup ---
        if (!window.litewebagentLabels) {
            window.litewebagentLabels = [];
        }

        function unmarkPage() {
            for (const label of window.litewebagentLabels) {
                if (label && label.parentNode) {
                    label.parentNode.removeChild(label);
                }
            }
            window.litewebagentLabels.length = 0;
        }

        // Removes all existing highlights
        unmarkPage();

        // Create a container for highlights that follows scroll
        const container = document.createElement('div');
        container.style.position = 'absolute';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '2147483647';
        document.body.appendChild(container);

        // --- Helper functions ---

        // 1) Checks if element's computed style is visible
        function isStyleVisible(elem) {
            const style = window.getComputedStyle(elem);
            return (
                style &&
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                parseFloat(style.opacity) > 0
            );
        }

        // 2) Checks if an element or any of its ancestors has "overlay" in its class name
        function hasOverlayClassInAncestors(el) {
            let current = el;
            while (current) {
                if (
                    typeof current.className === 'string' &&
                    current.className.toLowerCase().includes('overlay')
                ) {
                    return true;
                }
                current = current.parentElement;
            }
            return false;
        }

        // 3) Checks if the element or any of its ancestors has an attribute
        //    specifically named "_ngcontent-ng-c1666608104"
        function hasSpecificNgAttribute(el) {
            let current = el;
            while (current) {
                if (current.hasAttributes()) {
                    for (const attr of current.attributes) {
                        // Exact match only
                        if (attr.name === '_ngcontent-ng-c1666608104') {
                            return true;
                        }
                    }
                }
                current = current.parentElement;
            }
            return false;
        }

        // 4) Checks if an element (or ancestors) has the matching data-unique-test-id or id
        function hasMatchingBidInAncestors(elem, bid) {
            while (elem) {
                if (
                    elem.getAttribute &&
                    (elem.getAttribute('data-unique-test-id') === bid ||
                     elem.getAttribute('id') === bid)
                ) {
                    return true;
                }
                elem = elem.parentElement;
            }
            return false;
        }

        /**
         * 5) Use elementsFromPoint to get *all* elements under that point.
         *    Return the first one that:
         *      - does NOT have 'overlay' in its ancestry
         *      - does NOT have attribute name of '_ngcontent-ng-c1666608104'
         */
        function elementFromPointIgnoringOverlaysAndSpecificNg(x, y) {
            const stack = document.elementsFromPoint(x, y);
            for (const el of stack) {
                // Skip if it (or its ancestry) has 'overlay' or the specific _ngcontent attribute
                if (!hasOverlayClassInAncestors(el) && !hasSpecificNgAttribute(el)) {
                    return el;
                }
            }
            return null;
        }

        /**
         * 6) Main visibility check:
         *    (a) bounding box is within the viewport
         *    (b) If the element's tag is <cu-user-item>, skip the topmost coverage check and return true
         *    (c) Otherwise, the topmost valid element at the box center must match our bid
         */
        function isElementTrulyVisible(bbox, bid, domElement) {
            const viewWidth = window.innerWidth || document.documentElement.clientWidth;
            const viewHeight = window.innerHeight || document.documentElement.clientHeight;

            // (a) If bounding box is completely outside the viewport, skip
            if (
                bbox.bottom < 0 ||
                bbox.top > viewHeight ||
                bbox.right < 0 ||
                bbox.left > viewWidth
            ) {
                return false;
            }

            // (b) If it's a <cu-user-item>, ignore coverage checks
            if (
                domElement.tagName &&
                domElement.tagName.toLowerCase() === 'cu-user-item'
            ) {
                // Still want to ensure the bounding box is in the visible area
                return true;
            }

            // (c) For all other elements, do the topmost coverage check
            const centerX = Math.floor(bbox.left + bbox.width / 2);
            const centerY = Math.floor(bbox.top + bbox.height / 2);

            // If the center is offscreen, skip
            if (centerX < 0 || centerY < 0 || centerX > viewWidth || centerY > viewHeight) {
                return false;
            }

            const topElem = elementFromPointIgnoringOverlaysAndSpecificNg(centerX, centerY);
            if (!topElem) return false;

            // Check if that topmost element (or an ancestor) has the same bid
            return hasMatchingBidInAncestors(topElem, bid);
        }

        // --- Main logic ---

        let highlightedCount = 0;
        console.log('Length of elements is: ', elements.length);

        elements.forEach((item) => {
            // Locate the DOM element by data-unique-test-id or id
            let domElement =
                document.querySelector('[data-unique-test-id="' + item.bid + '"]') ||
                document.getElementById(item.bid);

            if (!domElement) {
                // Could not find the actual DOM element; skip
                return;
            }

            // Confirm none of its ancestors is hidden
            let ancestor = domElement;
            let chainHidden = false;
            while (ancestor) {
                if (!isStyleVisible(ancestor)) {
                    chainHidden = true;
                    break;
                }
                ancestor = ancestor.parentElement;
            }
            if (chainHidden) {
                return;
            }

            // For each rectangle in this item's bounding box list
            item.rects.forEach((bbox) => {
                //if (!isElementTrulyVisible(bbox, item.bid, domElement)) {
                //    return;
                //}

                // Highlight it
                const newElement = document.createElement("div");
                const borderColor = "#" + Math.floor(Math.random() * 16777215).toString(16);
                newElement.style.outline = `2px dashed ${borderColor}`;
                newElement.style.position = "absolute";
                newElement.style.left = `${bbox.left}px`;
                newElement.style.top = `${bbox.top}px`;
                newElement.style.width = `${bbox.width}px`;
                newElement.style.height = `${bbox.height}px`;
                newElement.style.pointerEvents = "none";
                newElement.style.boxSizing = "border-box";

                // Label showing the BID
                const label = document.createElement("span");
                label.textContent = item.bid;
                label.style.position = "absolute";
                label.style.top = "-19px";
                label.style.left = "0px";
                label.style.background = borderColor;
                label.style.color = "white";
                label.style.padding = "2px 4px";
                label.style.fontSize = "12px";
                label.style.borderRadius = "2px";

                newElement.appendChild(label);
                container.appendChild(newElement);
                window.litewebagentLabels.push(newElement);
                highlightedCount++;
            });
        });
        return highlightedCount;
    }
    """

    highlighted_count = 0
    for attempt in range(max_retries):
        highlighted_count = page.evaluate(js_code, elements)
        total_rects = sum(len(e["rects"]) for e in elements)

        if highlighted_count == total_rects:
            logger.info(f"All element rects ({highlighted_count}) highlighted successfully.")
            return

        logger.info(
            f"Attempt {attempt + 1}: Highlighted {highlighted_count} out of {total_rects}. "
            f"Retrying in {retry_delay}ms..."
        )
        time.sleep(retry_delay / 1000.0)

    logger.info(
        f"Warning: Only {highlighted_count} rects were highlighted after {max_retries} attempts."
    )

def remove_highlights(page: Page):
    """
    Synchronously removes previously drawn highlights and resets the label storage.
    """
    js_code = """
    () => {
        if (window.litewebagentLabels) {
            for (const label of window.litewebagentLabels) {
                if (label && label.parentNode) {
                    label.parentNode.removeChild(label);
                }
            }
            window.litewebagentLabels.length = 0;
        }
    }
    """
    page.evaluate(js_code)

def flatten_interactive_elements_to_str(
    interactive_elements,
    indent_char: str = "\t"
):
    """
    Formats a list of interactive elements into a string, including only text, type, and bid.
    Skips elements where the type is 'html' or 'body'.

    :param interactive_elements: List of dictionaries containing interactive element data
    :param indent_char: Character used for indentation (default: tab)
    :return: Formatted string representation of interactive elements
    """

    def format_element(element):
        # Skip if element type is 'html' or 'body'
        elem_type = element.get('type', '').lower()
        if elem_type in ('html', 'body'):
            return None

        bid_part = f"[{element['bid']}] " if 'bid' in element else ""
        element_type = element.get('type', 'Unknown')
        text = element.get('text', '').replace('\n', ' ').strip()

        return f"{bid_part}{element_type} {repr(text)}"

    formatted_elements = []
    for elem in interactive_elements:
        # Only consider if explicitly included
        if elem.get('include', True):
            line = format_element(elem)
            if line is not None:
                formatted_elements.append(line)

    return "\n".join(formatted_elements)
