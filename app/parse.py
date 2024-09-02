import csv
import os
import time
from dataclasses import dataclass, astuple, fields
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/laptops/"
)
TABLETS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/tablets/"
)
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.float-end").text.split()[0]
        ),
    )


def get_page_products(url: str) -> List[Product]:
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    products_soup = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_soup]


def get_page_products_with_buttons(url: str) -> List[Product]:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service)
    driver.get(url)
    products = []

    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        products_soup = soup.select(".thumbnail")
        products.extend(
            [parse_single_product(product) for product in products_soup]
        )

        try:
            more_button = WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(4)
        except Exception:
            break

    driver.quit()
    return products


def write_to_csv(products: List[Product], filename: str) -> None:
    with open(os.path.join(os.pardir, filename), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = {
        HOME_URL: ("home.csv", False),
        COMPUTERS_URL: ("computers.csv", False),
        PHONES_URL: ("phones.csv", False),
        LAPTOPS_URL: ("laptops.csv", True),
        TABLETS_URL: ("tablets.csv", True),
        TOUCHES_URL: ("touch.csv", True),
    }

    for url, (filename, with_buttons) in urls.items():
        if with_buttons:
            products = get_page_products_with_buttons(url)
        else:
            products = get_page_products(url)
        write_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
