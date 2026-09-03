# NOTE: this code is kinda buns

from time import sleep

from google import genai

from selenium import webdriver
from selene import browser, query, be
from selene.core.entity import Element

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from bs4 import BeautifulSoup
from bs4.element import PageElement, NavigableString, Tag

## ai settings -----------------------
ai_model = "gemini-3.5-flash-lite"
ai_instructions = f"""
    Provide strictly the answer and no formating, as characters typable on a keyboard (including ^).
    It should be an answer that a grade 8 student would give with BODMAS in its simplest form (unless the question says otherwise) (e.g. l*w*h as lwh).
    Provide {Keys.RIGHT} in the answer after an exponent or fraction to indicate where it stops if it is applicable (e.g. 2^2{Keys.RIGHT}+4, 1/6{Keys.RIGHT}*4).
    To type a mixed fraction, simply type 'mixed' and provide {Keys.RIGHT} at the end of each number (e.g. 1 and 2/3 -> mixed1{Keys.RIGHT}2{Keys.RIGHT}3{Keys.RIGHT}).
    If you are provided a list of options, respond with only the index number.
    Multiple answers are seperated with a comma.
"""
ai_config = {"thinking_level": "high"}
## -----------------------------------

## magic values ----------------------
input_textbox = '.css-14n74r0'
mcq_option_button = '.css-aaf0c9'
figure_image = '.css-k3trc9'
submit_button = '.css-k008qs'
next_button = '.css-3tczsx'
continue_button = '.css-1gomreu'
keepPracticing_button = '.css-1vcvnis'
question_text = '.css-2xu9yf'
expression_text = '.css-1oh6uy8'
previous_answers_text = '.css-14mgtrt'
loaded_check = '.css-5hicrt'
multi_answer_check = '.css-5514lj'
last_question_check = '.css-14peahi'
close_milo_button = '.css-152rhn5'    # i wish there was a way to disable milo its genuinely annoying
## -----------------------------------

client = genai.Client()

def solve(text: str, imageb64: str | None = None) -> str | None:
    try:
        kwargs = {}
        kwargs["model"] = ai_model
        kwargs["system_instruction"] = ai_instructions
        kwargs["generation_config"] = ai_config
        
        kwargs["input"] = [{"type": "text", "text": text}]

        image = None
        if imageb64 is not None:
            if image is not None:
                kwargs["input"].append(
                    {
                        "type": "image", 
                        "data": imageb64,
                        "mime_type": "image/png"
                    }
                )

        response = client.interactions.create(**kwargs) 

        return response.output_text # type: ignore

    except Exception as e:
        print(f"error: {e}")

def parse_mq(soup_node: Tag | NavigableString | PageElement) -> str: 
    if not isinstance(soup_node, Tag | NavigableString):
        return ""

    if isinstance(soup_node, NavigableString):
        return str(soup_node)

    classes = soup_node.get("class") or []

    if classes == ["mq-selectable"]:
        return ""

    if "mq-paren" in classes:
        return soup_node.text 

    if "mq-fraction" in classes:
        num = ""
        deno = ""

        for child in soup_node.children:
            if not isinstance(child, Tag):
                return ""

            child_classes = child.get("class") or []
            
            if "mq-numerator" in child_classes:
                for child_children in child.children:
                    num += parse_mq(child_children)

            elif "mq-denominator" in child_classes:
                for child_children in child.children:
                    deno += parse_mq(child_children)

        return f"(({num})/({deno}))"

    if "mq-sup" in classes:
        exp = ""

        for child in soup_node.children:
            exp += parse_mq(child)

        return f"^({exp})"

    if "mq-sqrt-stem" in classes:
        sqrt = ""

        for child in soup_node.children:
            sqrt += parse_mq(child)

        return f"√({sqrt})"

    if soup_node.name == "figure":
        for child in soup_node.children:
            if isinstance(child, Tag) and child.name == "figcaption":
                return parse_mq(child)

    if soup_node.name == "img":
        return "https://mathspace.co" + str(soup_node.get("src"))

    if soup_node.has_attr('mathquill-command-id'):
        return soup_node.text 

    # if none apply
    fragment = ""
    for child in soup_node.children:
        fragment += parse_mq(child)

    return fragment.replace("−", "-").replace("÷​", "/").replace("+​", "+").replace("×", "*").replace("\u200b", "")
    
def parse_html(element: Element):
    print(element)
    html = element.get(query.attribute("innerHTML"))

    #print(html)

    if html is None:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    text = ""

    for node in soup.contents:
        if isinstance(node, NavigableString):
            clean_text = str(node)
            if clean_text:
                text += clean_text
                
        elif isinstance(node, Tag):
            text += parse_mq(node)

    return text

## make sure you have your gemini api key in your environment variables
## or else geminis gonna touch you

## to let selenium see anything, you will need a chrome window with remote debugging
## "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selene_profile"

skip_err = input("skip errors? (Y/N): ").strip().lower()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)

browser.config.driver = driver

actions = ActionChains(browser.driver)

while True:
    try:
        if browser.element(next_button).matching(be.present):
            browser.element(next_button).click()

        if browser.element(keepPracticing_button).wait_until(be.clickable):
            browser.element(keepPracticing_button).click()

        # tries to close milo
        if browser.element(close_milo_button).with_(timeout=1).matching(be.present):
            browser.element(close_milo_button).click()

        browser.element(loaded_check).should(be.present)

        # extracts the questions and parses their html for ai
        question = parse_html(browser.element(question_text))
        expressions = []
        imageb64 = None

        full_question = question

        if browser.element(expression_text).matching(be.present):
            for expression in browser.all(expression_text):
                expressions.append(parse_html(expression))

        if browser.element(previous_answers_text).matching(be.present):
            for index, prev_answer_element in enumerate(browser.all(previous_answers_text)):
                prev_answer = (parse_html(prev_answer_element.element("./*")) + "\n")

                expressions_pairs = expressions[:-1]

                if browser.element(expression_text).matching(be.present):
                    if index < len(expressions_pairs):
                        full_question += f"\n{expressions_pairs[index]}\n{prev_answer}"

        if browser.element(expression_text).matching(be.present):
            full_question += f"\n{expressions[-1]}"

        if browser.element(figure_image).matching(be.present):
            imageb64 = parse_html(browser.element(figure_image))
            if imageb64.find("https://") != -1:
                imageb64 = browser.element(figure_image).locate().screenshot_as_base64
            else:
                full_question += f"\n{imageb64}"
                imageb64 = None

        if browser.element(input_textbox).with_(timeout=1).matching(be.present):
            print(full_question)
            answer = solve(full_question, imageb64)

            actions.scroll_to_element(browser.element(input_textbox).locate())
            actions.send_keys(Keys.BACKSPACE) # clears the text field
            actions.perform()

            browser.element(input_textbox).click() # highlights text field (incase it wasnt before)

            actions.send_keys(answer or "")
            actions.perform()
            
        elif browser.element(mcq_option_button).matching(be.present):
            option_list: list[Element] = []

            for index, button in enumerate(browser.all(mcq_option_button)):
                full_question += "\n"
                option_list.append(button)
                full_question += str(index) + " " + parse_html(button)

            print(full_question)
            answers = solve(full_question, imageb64) or ""

            for answer in answers.split(","):
                answer = int(answer.strip().replace(Keys.RIGHT, ""))
                print(answer)
                option_list[answer].element("..").click()

        browser.element(submit_button).with_(timeout=2).click()

        # checks if there are follow up questions and clicks the next button if there isnt
        if not browser.element(multi_answer_check).wait_until(be.present):
            browser.element(next_button).with_(timeout=16).click()
        elif not browser.element(last_question_check).wait_until(be.present):
            browser.element(next_button).with_(timeout=16).click()
        else:
            sleep(4)

        if browser.element(keepPracticing_button).with_(timeout=2).wait_until(be.clickable):
            browser.element(keepPracticing_button).click()
        elif browser.element(continue_button).matching(be.clickable):
            browser.element(continue_button).click()

    except Exception as e:
        # choosing to skip errors is an option
        # since most of the time the script continues to work anyway 
        if skip_err == "y":
            print(type(e).__name__)
            print(e)
        else:
            raise

        
# TODO(sometime in the future): implement features related the following
# normal tables and fill in the blank tables
# fill in the blanks
