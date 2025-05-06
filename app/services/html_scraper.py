import random
from bs4 import BeautifulSoup
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.logger import setup_logger
import os

SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL")
STATE = os.getenv("STATE")
logger = setup_logger("scraper")


async def generate_random_user_agent():
    browsers = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0',
    ]
    return random.choice(browsers)
async def fetch_company_details(url: str) -> dict:
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-agent={await generate_random_user_agent()}')
        options.add_argument("--headless=new")
        options.add_argument(f'--lang=en-US')
        options.add_argument("--start-maximized")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
        options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")
        options.add_argument("--disable-features=DnsOverHttps")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--no-first-run")
        options.add_argument("--no-sandbox")
        options.add_argument("--test-type")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.set_capability("goog:loggingPrefs", {
            "performance": "ALL",
            "browser": "ALL"
        })
        driver = webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options
        )
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type, attrs) {
                            const ctx = getContext.apply(this, arguments);
                            if (type === '2d') {
                                const originalToDataURL = this.toDataURL;
                                this.toDataURL = function() {
                                    return "data:image/png;base64,fake_canvas_fingerprint";
                                };
                            }
                            return ctx;
                        };
                        """
        })
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                  '''
        })
        driver.get(url)
        wait = WebDriverWait(driver, 15)  # Ожидаем до 15 секунд
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR,
             "#Form1 > section.content-holder.b-none.inner_content.inner_page > section > section > section > section.span9.panel2 > section > div > div.panel > div.panel-body")))
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR,
             "#accordion2")))
        table = driver.find_element(By.CSS_SELECTOR, '#Form1 > section.content-holder.b-none.inner_content.inner_page > section > section > section > section.span9.panel2 > section > div > div.panel')
        html = table.get_attribute('outerHTML')
        return await parse_html_details(html)
    except Exception as e:
        logger.error(f"Error fetching data for url '{url}': {e}")
        return {}
    finally:
        if driver:
            driver.quit()
async def fetch_company_data(query: str) -> list[dict]:
    driver = None
    try:
        url = "https://wyobiz.wyo.gov/Business/FilingSearch.aspx"
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-agent={await generate_random_user_agent()}')
        options.add_argument(f'--lang=en-US')
        options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
        options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-features=DnsOverHttps")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options
        )
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type, attrs) {
                            const ctx = getContext.apply(this, arguments);
                            if (type === '2d') {
                                const originalToDataURL = this.toDataURL;
                                this.toDataURL = function() {
                                    return "data:image/png;base64,fake_canvas_fingerprint";
                                };
                            }
                            return ctx;
                        };
                        """
        })
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                  '''
        })
        driver.get(url)
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#MainContent_txtFilingName")))
        input_field.send_keys(query)
        input_field.send_keys(Keys.RETURN)
        wait = WebDriverWait(driver, 15)  # Ожидаем до 15 секунд
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#Ol1")))
        table = driver.find_element(By.CSS_SELECTOR,'#Ol1')
        html = table.get_attribute('outerHTML')
        return await parse_html_search(html)
    except Exception as e:
        logger.error(f"Error fetching data for query '{query}': {e}")
        return []
    finally:
        if driver:
            driver.quit()

async def parse_html_search(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for li in soup.select('ol#Ol1 > li'):
        a = li.find('a')
        if not a:
            continue
        name_tag = a.find('span', class_='resFile1')
        if not name_tag:
            continue
        id_span = name_tag.find('span', style='white-space:nowrap;')
        biz_id = id_span.text.strip() if id_span else ""
        status_tag = a.find('span', class_='resFile2')
        status = status_tag.text.replace('Status: ', '').strip() if status_tag else ""
        href = a.get('href')
        full_url = 'https://wyobiz.wyo.gov/Business/' + href.replace('&amp;', '&')
        results.append({
            "state": STATE,
            "name": name_tag.text.strip(),
            "status": status,
            "id": biz_id,
            "url": full_url,
        })
    return results


async def parse_html_details(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    async def get_text(selector):
        el = soup.select_one(selector)
        if selector == "#divParties li .resHist2" or selector=="#divParties li .resHist3":
            return list(el.stripped_strings)[-1] if el else None
        return el.get_text(strip=True) if el else None

    async def parse_files():
        history_items = []
        history_sections = soup.select('#divHistorySummary .fhContainer')
        for item in history_sections:
            type_block = item.select_one('.fhRef')
            date_block = item.select_one('.fhDate')
            pdf_icon = item.select_one('.fhPdf.fh_On')

            if not pdf_icon or 'onclick' not in pdf_icon.attrs:
                continue  # пропускаем, если нет PDF
            try:
                parts = pdf_icon['onclick'].split('"')
                sid = parts[1]
                stid = parts[3]
                pdf_link = f'https://wyobiz.wyo.gov/Business/GetImages.aspx?sid={sid}&stid={stid}'
            except (IndexError, ValueError):
                continue  # пропускаем, если что-то пошло не так

            history_items.append({
                "name": type_block.get_text(strip=True) if type_block else None,
                "date": date_block.get_text(strip=True).replace('Date:', '').strip() if date_block else None,
                "link": pdf_link
            })

        return history_items

    return {
        "state": STATE,
        "name": await get_text('#txtFilingName2'),
        "registration_number": await get_text('#txtFilingNum'),
        "entity_type": await get_text('#txtFilingType'),
        "status": await get_text('#txtStatus'),
        "date_registered": await get_text('#txtInitialDate'),
        "agent_name": await get_text('#txtAgentName'),
        "agent_address": await get_text('#txtAgentAddress'),
        "organizer": await get_text('#divParties li .resHist1'),
        "organization": await get_text('#divParties li .resHist2'),
        "organizer_address": await get_text('#divParties li .resHist3'),
        "history": await parse_files()
    }
