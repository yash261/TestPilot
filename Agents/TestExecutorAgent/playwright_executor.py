import asyncio
from asyncio.log import logger
from typing import List
from playwright.async_api import async_playwright

class PlaywrightExecutor:
    def __init__(self,initialize=True):
        try:
            self.playwright = None  # Initialize as None
            self.browser = None
            self.page = None
            if(initialize):
                asyncio.ensure_future(self.initialize_playwright())
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Playwright: {str(e)}")
        
    async def initialize_playwright(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
    
    async def navigate(self, url: str,timeout: int = 5) -> str:
        try:
            await self.page.goto(url, timeout=timeout*1000)
            title = await self.page.title()
            url = self.page.url
            result = f"Page loaded: {url}, Title: {title}"
            return f"Navigated to {result}"
        except Exception as e:
            return f"ERROR: Failed to navigate to {url} - {str(e)}"

    async def click(self, selector: str) -> str:
        try:
            await self.page.click(selector,timeout=5000)
            return f"Clicked on {selector}"
        except Exception as e:
            return f"ERROR: Failed to click {selector} - {str(e)}"
    
    async def input_text(self, query_selector: str, text: str) -> str:
        try:
            await self.page.evaluate(
                """
                (selector) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.value = '';
                    } else {
                        console.error('Element not found:', selector);
                    }
                }
                """,
                query_selector,
            )
            await self.page.fill(query_selector, text, timeout=5000)
            return f"Entered text '{text}' into {query_selector}"
        except Exception as e:
            return f"ERROR: Failed to enter text into {query_selector} - {str(e)}"

    async def press_key(self, selector: str, key: str) -> str:
        try:
            await self.page.press(selector, key)
            return f"Pressed key '{key}' on {selector}"
        except Exception as e:
            return f"ERROR: Failed to press key {key} on {selector} - {str(e)}"

    async def close(self):
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"WARNING: Failed to close Playwright session - {str(e)}")
    
    async def wait_for_non_loading_dom_state(self,max_wait_millis: int):
        max_wait_seconds = max_wait_millis / 1000
        end_time = asyncio.get_event_loop().time() + max_wait_seconds
        while asyncio.get_event_loop().time() < end_time:
            dom_state = await self.page.evaluate("document.readyState")
            if dom_state != "loading":
                logger.debug(f"DOM state is not 'loading': {dom_state}")
                break  # Exit the loop if the DOM state is not 'loading'

            await asyncio.sleep(0.05)
    
    async def get_dom_texts_func(self) -> str:
        """
        Retrieves the text content of the active page's DOM.
        """
        logger.info("Executing Get DOM Text Command")
        await self.wait_for_non_loading_dom_state(2000)
        
        # Get filtered text content including alt text from images
        text_content = await self.get_filtered_text_content()
        return text_content
    
    async def get_filtered_text_content(self) -> str:
        """Helper function to get filtered text content from the page."""
        text_content = await self.page.evaluate("""
            () => {
                // Array of query selectors to filter out
                const selectorsToFilter = ['#tawebagent-overlay'];

                // Store the original visibility values to revert later
                const originalStyles = [];

                // Hide the elements matching the query selectors
                selectorsToFilter.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        originalStyles.push({ element: element, originalStyle: element.style.visibility });
                        element.style.visibility = 'hidden';
                    });
                });

                // Get the text content of the page
                let textContent = document?.body?.innerText || document?.documentElement?.innerText || "";

                // Get all the alt text from images on the page
                let altTexts = Array.from(document.querySelectorAll('img')).map(img => img.alt);
                altTexts = "Other Alt Texts in the page: " + altTexts.join(' ');

                // Revert the visibility changes
                originalStyles.forEach(entry => {
                    entry.element.style.visibility = entry.originalStyle;
                });
                
                return textContent + " " + altTexts;
            }
        """)
        return text_content
    
    async def get_dom_field_func(self):
            """
            Retrieves all interactive fields from the active page's DOM.
            Extracts input fields, buttons, and anchor elements.
            """
            await self.wait_for_non_loading_dom_state(2000)
            
            # Extract all interactive elements (inputs, buttons, links)
            interactive_elements = await self.page.evaluate('''
                () => {
                    const elements = [];
                    
                    // Get all input fields
                    document.querySelectorAll('input, textarea, select').forEach(el => {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            type: el.type || null,
                            name: el.name || null,
                            placeholder: el.placeholder || null,
                            value: el.value || null,
                            id: el.id || null,
                            class: el.className || null
                        });
                    });

                    // Get all buttons
                    document.querySelectorAll('button, [role="button"], input[type="submit"]').forEach(el => {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText.trim(),
                            id: el.id || null,
                            class: el.className || null
                        });
                    });

                    // Get all links
                    document.querySelectorAll('a').forEach(el => {
                        elements.push({
                            tag: 'a',
                            text: el.innerText.trim(),
                            href: el.href || null,
                            id: el.id || null,
                            class: el.className || null
                        });
                    });

                    return elements;
                }
            ''')

            return interactive_elements
    
    async def geturl(self) -> str:
        """
        Returns the full URL of the current page

        Parameters:

        Returns:
        - Full URL the browser's active page.
        """
        try:
            await self.page.wait_for_load_state("domcontentloaded")
            current_url = self.page.url
            return f"Current Page: {current_url}"

        except Exception as e:
            return f"ERROR: Failed to get the current URL - {str(e)}"
