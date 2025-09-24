from scrapers.cmc.main_cmc_scraper import scrape_cmc_page
from scrapers.coingecko.main_cg_scraper import scrape_cg_page

if __name__ == "__main__":
    chrome_num = input("Enter browser number (1-7)")
    chrome_profile = "telegram_" + chrome_num

    # page_num = int(input("Enter page number (1-96)"))
    # print(f"starting scrape for page {page_num} with profile {chrome_profile}")
    # scrape_cmc_page(page_num, chrome_profile)

    # page_num = int(input("Enter page number (1-189)"))
    for page_num in range(7, 12):
        print(f"starting scrape for page {page_num} with profile {chrome_profile}")
        scrape_cg_page(page_num, chrome_profile)