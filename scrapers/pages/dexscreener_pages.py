# core/scrapers/pages/dexscreener_pages.py

NEW_LINK = "https://dexscreener.com/page-1?maxAge=24&minLiq=10000&order=asc&profile=1&rankBy=pairAge"

#####################
# Main Landing Page #
#####################
FILTERS_BUTTON = "//main/div/div[3]/div/div[1]/div/div[4]/button[2]/span[text()='Filters']"
RANK_BY_BUTTON = "//span/div/span[text()='Rank by:']"

PROJECT_NAME__12 = "a:nth-child(x) > div.ds-table-data-cell.ds-dex-table-row-col-token > div.ds-dex-table-row-base-token-name > span"
PROJECT_TICKERS__12 = "a:nth-child(x) > div.ds-table-data-cell.ds-dex-table-row-col-token > span.ds-dex-table-row-base-token-symbol"
PROJECT_LIQUIDITY__12 = "a:nth-child(x) > div.ds-table-data-cell.ds-dex-table-row-col-liquidity"
PROJECT_MARKET_CAP__12 = "a:nth-child(x) > div.ds-table-data-cell.ds-dex-table-row-col-market-cap"

#################
# Filters Popup #
#################
PROFILE_BUTTON = "//button[1]/span[text()='Profile']"
MIN_LIQUIDITY_FIELD = "//span[normalize-space(text())='Liquidity:']/following-sibling::div//input[@placeholder='Min']"
MAX_PAIR_AGE_FIELD = '//span[normalize-space(text())="Pair age:"]/following-sibling::div//input[@placeholder="Max"]'
APPLY_BUTTON = "//footer/button[text()='Apply']"

#################
# Rank By Popup #
#################
RANK_BY_PAIR_AGE_BUTTON = "//button/span[text()='Pair age']"

################
# Project Page #
################
PROJECT_PAGE_LINKS__2 = "//div/div[1]/div/div/div[2]/div[2]/div/button[x]"
PROJECT_PAGE_CLOSE_BUTTON = "//header/div/button[@title='Close']"
