# NOTE: this code is kinda buns

from google import genai

from selenium import webdriver
from selene import browser, query, be
from selene.core.entity import Element

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from bs4 import BeautifulSoup
from bs4.element import PageElement, NavigableString, Tag

## magic values ----------------------
input_textbox = '.css-14n74r0'
mcq_option_button = '.css-aaf0c9'
submit_button = '.css-k008qs'
next_button = '.css-3tczsx'
keepPracticing_button = '.css-1vcvnis'
question_text = '.css-2xu9yf'
expression_text = '.css-1oh6uy8'
previous_answers_text = '.css-14mgtrt'
loaded_check = '.css-5hicrt'
multi_answer_check = '.css-5514lj'
last_question_check = '.css-14peahi'
close_milo_button = '.css-152rhn5'    # i wish there was a way to disable milo its genuinely annoying

container_classes = [
    "xBQ2HyCNJoo33_Z_K6va",
    "prefix", 
    "mq-math-mode", 
    "mq-root-block",
    "mq-non-leaf"
]
## -----------------------------------

#prevInteractionId = None

def solve(text: str) -> str | None:
    try:
        with genai.Client() as client:
            #global prevInteractionId

            #kwargs = {}
            #if prevInteractionId is not None and browser.element('css-5514lj').wait_until(be.present):
            #    kwargs["previous_interaction_id"] = prevInteractionId

            response = client.interactions.create(
                model="gemini-3.5-flash-lite",
                system_instruction=
                   "\nProvide strictly the answer and no formating, as characters typable on a keyboard (including ^)."
                +  "\nIt should be an answer that a grade 8 student would give with BODMAS in its simplest form (unless the question says otherwise) (e.g. l*w*h as lwh)."
                + f"\nProvide {Keys.RIGHT} in the answer after an exponent or fraction to indicate where it stops if it is applicable (e.g. 2^2{Keys.RIGHT}+4, 1/6{Keys.RIGHT}*4)."
                + f"\nTo type a mixed fraction, simply type 'mixed' and provide {Keys.RIGHT} at the end of each number (e.g. 1 and 2/3 -> mixed1{Keys.RIGHT}2{Keys.RIGHT}3{Keys.RIGHT}"
                +  "\nIf you are provided a list of options, respond with only the index number."
                +  "\nMultiple answers are seperated with a comma."
                ,
                generation_config={
                    "thinking_level": "high"
                },
                input=text,
                #**kwargs
            )

            #prevInteractionId = response.id 

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

    if classes == ["math-inline"]:
        return soup_node.text

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

    if classes == [] or any(cls in classes for cls in container_classes):
            fragment = ""
            for child in soup_node.children:
                fragment += parse_mq(child)
    
            return fragment.replace("−", "-").replace("÷​", "/").replace("+​", "+").replace("×", "*").replace("\u200b", "")

    if soup_node.has_attr('mathquill-command-id'):
        return soup_node.text 

    return ""
    
def parse_html(element: Element):
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

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)

browser.config.driver = driver

actions = ActionChains(browser.driver)

while True:
    try:
        # tries to close milo
        if browser.element(close_milo_button).with_(timeout=1).matching(be.present):
            browser.element(close_milo_button).click()

        browser.element(loaded_check).should(be.present)

        # extracts the questions and parses their html for ai
        question = parse_html(browser.element(question_text))
        expression = ""
        prev_answers = ""

        if browser.element(expression_text).matching(be.present):
            expression = parse_html(browser.all(expression_text).element(-1)) 

        if browser.element(previous_answers_text).matching(be.present):
            for prev_answer in browser.all(previous_answers_text):
                prev_answers += parse_html(prev_answer.element("./*")) + "\n"

        full_question = f"{question}\n{prev_answers}\n{expression}"

        if browser.element(input_textbox).with_(timeout=1).matching(be.present):
            print(full_question)
            answer = solve(full_question)

            actions.send_keys(Keys.BACKSPACE) # clears the text field
            actions.perform()

            browser.element(input_textbox).click() # highlights text field (incase it wasnt before)

            actions.send_keys(answer or "")
            actions.perform()
        elif browser.element(mcq_option_button).matching(be.present):
            ##print(browser.element(mcq_option_button).element(".."))
            option_list: list[Element] = []

            for index, button in enumerate(browser.all(mcq_option_button)):
                full_question += "\n"
                option_list.append(button)
                full_question += str(index) + " " + parse_html(button)

            print(full_question)
            answers = solve(full_question) or ""

            for answer in answers.split(","):
                answer = int(answer.strip())
                print(answer)
                option_list[answer].element("..").click()

        browser.element(submit_button).with_(timeout=2).click()

        # checks if there are follow up questions and clicks the next button if there isnt
        if not browser.element(multi_answer_check).wait_until(be.present):
            browser.element(next_button).with_(timeout=16).click()
        elif not browser.element(last_question_check).wait_until(be.present):
            browser.element(next_button).with_(timeout=16).click()
        else:
            browser.element(submit_button).should(be.clickable)

        if browser.element(keepPracticing_button).with_(timeout=2).wait_until(be.clickable):
            browser.element(keepPracticing_button).click()

    except Exception as e:
        print(type(e).__name__)
        print(e)
        pass

        
# TODO(sometime in the future): implement features related the following
# normal tables and fill in the blank tables
# fill in the blanks
# pictures
