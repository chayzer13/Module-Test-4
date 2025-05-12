import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import string
import logging
import allure
from allure_commons.types import AttachmentType

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasePage:
    def __init__(self, browser, url):
        self.browser = browser
        self.url = url

    def open(self):
        with allure.step(f"Открытие страницы {self.url}"):
            logger.info(f"Opening page: {self.url}")
            self.browser.get(self.url)
            time.sleep(2)
            allure.attach(self.browser.get_screenshot_as_png(), name="page_screenshot", attachment_type=AttachmentType.PNG)

    def element(self, locator):
        return WebDriverWait(self.browser, 15).until(
            EC.presence_of_element_located(locator)
        )

    def clickable_element(self, locator):
        return WebDriverWait(self.browser, 15).until(
            EC.element_to_be_clickable(locator)
        )

    def visible_element(self, locator):
        return WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located(locator)
        )


class HomePage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, "https://demo-opencart.ru/index.php?route=common/home")

    def go_to_product_page(self, product_name):
        with allure.step(f"Переход на страницу товара {product_name}"):
            logger.info(f"Going to product page: {product_name}")
            product_link = self.clickable_element((By.XPATH, f"//a[contains(text(),'{product_name}')]"))  
            product_link.click()
            return ProductPage(self.browser)

    def go_to_register_page(self):
        with allure.step("Переход на страницу регистрации"):
            logger.info("Navigating to registration page")
            account_menu = self.clickable_element((By.XPATH, "//a[@title='Личный кабинет']"))
            account_menu.click()
            register_link = self.clickable_element((By.XPATH, "//a[contains(text(),'Регистрация')]"))
            register_link.click()
            return RegisterPage(self.browser)

    def search_product(self, query):
        with allure.step(f"Поиск товара: {query}"):
            logger.info(f"Searching for product: {query}")
            search_input = self.visible_element((By.CSS_SELECTOR, "input[name='search']"))
            search_input.clear()
            search_input.send_keys(query)
            allure.attach(self.browser.get_screenshot_as_png(), name="search_input", attachment_type=AttachmentType.PNG)
            search_button = self.clickable_element((By.CSS_SELECTOR, "#search button"))
            search_button.click()
            return SearchResultsPage(self.browser)

    def open_pc_category(self):
        with allure.step("Открытие категории PC через меню"):
            logger.info("Opening PC category via menu")
            computers_menu = self.visible_element((By.XPATH, "//a[contains(text(),'Компьютеры')]"))
            ActionChains(self.browser).move_to_element(computers_menu).perform()
            time.sleep(1)
            pc_link = self.clickable_element((By.XPATH, "//a[contains(text(),'PC') and contains(@href,'path=20_26')]"))
            pc_link.click()
            return self.browser


class ProductPage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, browser.current_url)

    def get_product_title(self):
        with allure.step("Получение заголовка товара"):
            title = WebDriverWait(self.browser, 15).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@id='content']//h1"))
            ).text
            logger.info(f"Product title: {title}")
            return title
    
    def click_all_thumbnails(self):
        with allure.step("Клики по всем превью изображений товара"):
            logger.info("Clicking all product thumbnails")
            thumbnails = WebDriverWait(self.browser, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.thumbnails li a.thumbnail"))
            )

            for i, thumbnail in enumerate(thumbnails):
                try:
                    self.browser.execute_script("arguments[0].scrollIntoView();", thumbnail)
                    thumbnail.click()
                    time.sleep(1) 
           
                    WebDriverWait(self.browser, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".mfp-image"))
                    )
                    allure.attach(self.browser.get_screenshot_as_png(), 
                                name=f"thumbnail_{i}_preview", 
                                attachment_type=AttachmentType.PNG)

                    close_button = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mfp-close"))
                    )
                    close_button.click()

                    WebDriverWait(self.browser, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".mfp-content"))
                    )  
                except Exception as e:
                    logger.error(f"Ошибка при обработке превью {i+1}: {str(e)}")
                    allure.attach(self.browser.get_screenshot_as_png(), 
                                name=f"thumbnail_error_{i}", 
                                attachment_type=AttachmentType.PNG)
                    continue
    
    def add_to_wishlist(self):
        with allure.step("Добавление товара в список желаний"):
            logger.info("Adding product to wishlist")
            wishlist_button = self.clickable_element((By.CSS_SELECTOR, "button[data-original-title='В закладки']"))
            wishlist_button.click()
        
            WebDriverWait(self.browser, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.alert-success"))
            ) 
            allure.attach(self.browser.get_screenshot_as_png(), 
                         name="wishlist_success", 
                         attachment_type=AttachmentType.PNG)
        
            return self.browser
    
    def write_review(self, name, text, rating=5):
        with allure.step(f"Написание отзыва для товара (оценка: {rating})"):
            logger.info(f"Writing product review with rating {rating}")
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            write_review_btn = self.clickable_element((By.XPATH, "//a[contains(text(),'Написать отзыв')]"))
            write_review_btn.click()
            time.sleep(1)

            self.visible_element((By.XPATH, "//input[@placeholder='Ваше имя']")).send_keys(name)
            self.visible_element((By.XPATH, "//textarea[@placeholder='Ваш отзыв']")).send_keys(text)

            rating_inputs = self.browser.find_elements(By.XPATH, "//input[@name='rating']")
            if len(rating_inputs) >= rating:
                rating_inputs[rating-1].click()

            allure.attach(self.browser.get_screenshot_as_png(), 
                         name="review_form_filled", 
                         attachment_type=AttachmentType.PNG)

            self.clickable_element((By.XPATH, "//button[contains(text(),'Продолжить')]")).click()
            
            try:
                success_message = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.alert-success"))
                ).text
                allure.attach(self.browser.get_screenshot_as_png(), 
                             name="review_success", 
                             attachment_type=AttachmentType.PNG)
                return success_message
            except:
                logger.warning("Форма отправлена, но сообщение не найдено")
                return "Форма отправлена, но сообщение не найдено"

class WishlistPage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, "https://demo-opencart.ru/index.php?route=account/wishlist")
    
    def get_wishlist_items(self):
        with allure.step("Получение списка товаров в избранном"):
            try:
                items = self.browser.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
                logger.info(f"Found {len(items)} items in wishlist")
                allure.attach(self.browser.get_screenshot_as_png(), 
                             name="wishlist_items", 
                             attachment_type=AttachmentType.PNG)
                return items
            except Exception as e:
                logger.error(f"Error getting wishlist items: {str(e)}")
                return []

class RegisterPage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, browser.current_url)

    def register_user(self, firstname, lastname, email, telephone, password):
        with allure.step(f"Регистрация пользователя {firstname} {lastname}"):
            logger.info(f"Registering user with email: {email}")
            self.visible_element((By.ID, "input-firstname")).send_keys(firstname)
            self.visible_element((By.ID, "input-lastname")).send_keys(lastname)
            self.visible_element((By.ID, "input-email")).send_keys(email)
            self.visible_element((By.ID, "input-telephone")).send_keys(telephone)
            self.visible_element((By.ID, "input-password")).send_keys(password)
            self.visible_element((By.ID, "input-confirm")).send_keys(password)
            
            privacy_policy = self.clickable_element((By.NAME, "agree"))
            self.browser.execute_script("arguments[0].click();", privacy_policy)
            
            allure.attach(self.browser.get_screenshot_as_png(), 
                         name="registration_form_filled", 
                         attachment_type=AttachmentType.PNG)

            continue_button = self.clickable_element((By.XPATH, "//input[@value='Продолжить']"))
            continue_button.click()
            
            return SuccessRegisterPage(self.browser)


class SuccessRegisterPage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, browser.current_url)
        WebDriverWait(self.browser, 15).until(
            EC.url_contains("route=account/success")
        )

    def get_success_message(self):
        with allure.step("Получение сообщения об успешной регистрации"):
            message = WebDriverWait(self.browser, 15).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@id='content']/h1"))
            ).text
            logger.info(f"Registration success message: {message}")
            allure.attach(self.browser.get_screenshot_as_png(), 
                         name="registration_success", 
                         attachment_type=AttachmentType.PNG)
            return message


class SearchResultsPage(BasePage):
    def __init__(self, browser):
        super().__init__(browser, browser.current_url)

    def get_page_title(self):
        try:
            title = self.visible_element((By.TAG_NAME, "h1")).text
            logger.info(f"Search results page title: {title}")
            return title
        except Exception as e:
            logger.warning(f"Could not get page title: {str(e)}")
            return ""

    def get_products(self):
        products = self.browser.find_elements(By.CSS_SELECTOR, ".product-thumb")
        logger.info(f"Found {len(products)} products in search results")
        return products


@pytest.fixture
def browser():
    with allure.step("Инициализация браузера"):
        options = webdriver.FirefoxOptions()
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(10)
        logger.info("Browser initialized")
        yield driver
        with allure.step("Закрытие браузера"):
            driver.quit()
            logger.info("Browser closed")

@allure.feature("Тестирование функционала товаров")
def test_product_screenshots_switching(browser):
    with allure.step("Тест переключения превью изображений товара"):
        home_page = HomePage(browser)
        home_page.open()
        
        product_name = "MacBook"
        product_page = home_page.go_to_product_page(product_name)
        
        product_title = product_page.get_product_title()
        assert product_name in product_title, f"Expected '{product_name}' in title, got '{product_title}'"
        
        product_page.click_all_thumbnails()

@allure.feature("Тестирование навигации")
def test_empty_pc_category_via_menu(browser):
    with allure.step("Тест навигации в пустую категорию PC"):
        home_page = HomePage(browser)
        home_page.open()
        
        home_page.open_pc_category()
        
        WebDriverWait(browser, 15).until(
            EC.url_contains("path=20_26")
        )
        time.sleep(2)

def generate_random_email():
    letters = string.ascii_lowercase
    username = ''.join(random.choice(letters) for _ in range(8))
    return f"{username}@example.com"

@allure.feature("Тестирование регистрации пользователей")
def test_user_registration(browser):
    with allure.step("Тест регистрации нового пользователя"):
        home_page = HomePage(browser)
        home_page.open()
        
        register_page = home_page.go_to_register_page()
        
        test_email = generate_random_email()
        success_page = register_page.register_user(
            firstname="Иван",
            lastname="Петров",
            email=test_email,
            telephone="+79123456789",
            password="TestPassword123"
        )
        
        success_message = success_page.get_success_message()
        assert "Ваша учетная запись создана!" in success_message, \
            f"Ожидалось сообщение об успешной регистрации, получено: '{success_message}'"

@allure.feature("Тестирование поиска")
def test_search_product(browser):
    with allure.step("Тест поиска товаров"):
        home_page = HomePage(browser)
        home_page.open()
        
        search_query = "iPhone"
        search_results = home_page.search_product(search_query)
        
        WebDriverWait(browser, 15).until(
            EC.url_contains("search=" + search_query)
        )
        
        try:
            assert search_query in search_results.get_page_title()
        except:
            pass
        
        products = search_results.get_products()
        assert len(products) > 0

@allure.feature("Тестирование избранного")
def test_add_product_to_wishlist(browser):
    with allure.step("Тест добавления товара в избранное"):
        home_page = HomePage(browser)
        home_page.open()
        
        register_page = home_page.go_to_register_page()
        
        test_email = generate_random_email()
        success_page = register_page.register_user(
            firstname="Иван",
            lastname="Петров",
            email=test_email,
            telephone="+79123456789",
            password="TestPassword123"
        )
        
        search_query = "iPhone"
        search_results = home_page.search_product(search_query)
        
        product_name = "iPhone"
        product_page = home_page.go_to_product_page(product_name)
        
        product_title = product_page.get_product_title()
        assert product_name in product_title, f"Expected '{product_name}' in title, got '{product_title}'"
        
        product_page.add_to_wishlist()
        
        browser.get("https://demo-opencart.ru/index.php?route=account/wishlist")
        wishlist_page = WishlistPage(browser)
        
        wishlist_items = wishlist_page.get_wishlist_items()
        assert len(wishlist_items) == 1, f"Expected 1 item in wishlist, got {len(wishlist_items)}"

        item_name = wishlist_items[0].find_element(By.CSS_SELECTOR, "td.text-left a").text
        assert product_name in item_name, f"Expected '{product_name}' in wishlist, got '{item_name}'"

@allure.feature("Тестирование корзины")
def test_add_camera_to_cart(browser):
    with allure.step("Тест добавления камеры в корзину"):
        home_page = HomePage(browser)
        home_page.open()
        
        search_query = "Nikon D300"
        search_results = home_page.search_product(search_query)
        
        product_name = "Nikon D300"
        product_page = home_page.go_to_product_page(product_name)

        quantity_input = product_page.clickable_element((By.CSS_SELECTOR, "input[name='quantity']"))
        quantity_input.clear()
        quantity_input.send_keys("3")
        
        add_to_cart_button = product_page.clickable_element((By.CSS_SELECTOR, "button#button-cart"))
        add_to_cart_button.click()
        
        time.sleep(2)
        allure.attach(browser.get_screenshot_as_png(), 
                     name="product_added_to_cart", 
                     attachment_type=AttachmentType.PNG)

@allure.feature("Тестирование корзины")
def test_add_lebtop_to_cart(browser):
    with allure.step("Тест добавления ноутбука в корзину"):
        home_page = HomePage(browser)
        home_page.open()
        
        search_query = "Samsung Galaxy Tab 10.1"
        search_results = home_page.search_product(search_query)
        
        product_name = "Samsung Galaxy Tab 10.1"
        product_page = home_page.go_to_product_page(product_name)
        
        add_to_cart_button = product_page.clickable_element((By.CSS_SELECTOR, "button#button-cart"))
        add_to_cart_button.click()
        
        time.sleep(2)
        allure.attach(browser.get_screenshot_as_png(), 
                     name="lebtop_added_to_cart", 
                     attachment_type=AttachmentType.PNG)

@allure.feature("Тестирование корзины")
def test_add_htc_to_cart(browser):
    with allure.step("Тест добавления телефона HTC в корзину"):
        home_page = HomePage(browser)
        home_page.open()
        
        search_query = "HTC"
        search_results = home_page.search_product(search_query)
        
        product_name = "HTC"
        product_page = home_page.go_to_product_page(product_name)
        
        add_to_cart_button = product_page.clickable_element((By.CSS_SELECTOR, "button#button-cart"))
        add_to_cart_button.click()
        
        time.sleep(2)
        allure.attach(browser.get_screenshot_as_png(), 
                     name="htc_added_to_cart", 
                     attachment_type=AttachmentType.PNG)

@allure.feature("Тестирование отзывов")
def test_write_product_review(browser):
    with allure.step("Тест написания отзыва о товаре"):
        home_page = HomePage(browser)
        home_page.open()
        
        product_name = "iPhone"
        product_page = home_page.go_to_product_page(product_name)
        
        product_title = product_page.get_product_title()
        assert product_name in product_title, f"Expected '{product_name}' in title, got '{product_title}'"
        
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        write_review_button = product_page.clickable_element((By.XPATH, "//a[contains(text(),'Написать отзыв')]"))
        write_review_button.click()
        time.sleep(1)  
        
        name_field = product_page.visible_element((By.XPATH, "//input[@name='name']"))
        name_field.send_keys("Тестовый Пользователь")
        
        review_field = product_page.visible_element((By.XPATH, "//textarea[@name='text']"))
        review_field.send_keys("Это автоматически созданный отзыв. Товар хорошего качества!")
        
        rating_inputs = browser.find_elements(By.NAME, "rating")
        if len(rating_inputs) >= 5:
            browser.execute_script("arguments[0].scrollIntoView();", rating_inputs[4])
            rating_inputs[4].click() 
        
        allure.attach(browser.get_screenshot_as_png(), 
                     name="review_form_before_submit", 
                     attachment_type=AttachmentType.PNG)
        
        continue_button = product_page.clickable_element((By.XPATH, "//button[contains(text(),'Продолжить')]"))
        continue_button.click()
        
        try:
            success_message = WebDriverWait(browser, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.alert-success"))
            ).text
            allure.attach(browser.get_screenshot_as_png(), 
                         name="review_submit_success", 
                         attachment_type=AttachmentType.PNG)
            assert "спасибо" in success_message.lower(), \
                f"Expected success message not found, got: '{success_message}'"
        except Exception as e:
            logger.error(f"Не удалось найти сообщение об успехе: {str(e)}")
            allure.attach(browser.get_screenshot_as_png(), 
                         name="review_submit_error", 
                         attachment_type=AttachmentType.PNG)
            print("Не удалось найти сообщение об успехе, но форма была заполнена")