from scrapers.cmc.main_cmc_scraper import scrape_new_cmc_page

if __name__ == "__main__":
    chrome_profile = "telegram_1"
    cmc_page_num = 1

    scrape_new_cmc_page(cmc_page_num, chrome_profile)