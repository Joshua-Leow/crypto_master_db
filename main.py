from scrapers.cmc.main_cmc_scraper import scrape_new_cmc_page
from scrapers.coingecko.main_cg_scraper import scrape_cg_page

if __name__ == "__main__":
    chrome_profile = "telegram_1"
    page_num = 2

    # scrape_new_cmc_page(page_num, chrome_profile)
    scrape_cg_page(page_num, chrome_profile)