#################
# in route /new #
#################
NEW_BUTTON = "//ul[@data-role='Tabs']/li/div/div/span[text()='New']"
DEXSCAN_BUTTON = "//div/div/div/div/div/div/div/div/ul/li/div/div/b[text()='DexScan']"
FILTERS_BUTTON = "//div/div/div/div/div/div/button/div/div/span[text()='Filters']"
DEXSCAN_FILTERS_MIN_1_SOCIAL_ACCOUNT_CHECKBOX = "//input[@label='Minimum 1 social account']/following-sibling::span"
DEXSCAN_FILTERS_MIN_LIQUIDITY_INPUT = "//div[div[text()='Liquidity']]//input[@placeholder='Min']"
DEXSCAN_FILTERS_MAX_AGE_INPUT = "//div[div[text()='Age']]//input[@placeholder='Max']"
DEXSCAN_FILTERS_APPLY_BUTTON = "/html/body/div/div/div/div/div/button/div/div[text()='Apply']"

DEXSCAN_PROJECT_SOURCE_LINK = "td[2]/div/div/div/div[1]/a"
DEXSCAN_PROJECT_NAME = "td[2]/div/div/div/div[1]/a/strong/span"
DEXSCAN_PROJECT_SOCIALS_LINKS = "td[2]/div/div/div/div[2]/div[2]/div/a"
DEXSCAN_PROJECT_MCAP_TEXT = "td[4]/span"
DEXSCAN_PROJECT_LIQUIDITY_TEXT = "td[5]/span"

FIRST_HYPERLINK = "#__next > div.sc-f9c982a5-1.bVsWPX.global-layout-v2 > div > div.cmc-body-wrapper > div > div.sc-936354b2-2.iyOdZW > table > tbody > tr:nth-child(1) > td:nth-child(3) > a"

# Pagination
PAGE_NUMBERS = "(//ul[@class='pagination'])[last()]/li/a"

#################################
# in route /currencies/currency #
#################################

COIN_NAME_TEXT = "#section-coin-overview > div.sc-65e7f566-0.gLzlll > h1 > span"
COIN_SYMBOL_TEXT = "#section-coin-overview > div.sc-65e7f566-0.gLzlll > h1 > div.sc-65e7f566-0.cBEDwf.coin-symbol-wrapper > span"
CMC_RANK_TEXT = "#section-coin-overview > div.sc-65e7f566-0.gLzlll > h1 > div.BasePopover_base__T5yOf.popover-base > div > span.BaseChip_btnContentWrapper__5wLR1 > div > span"

IMPORTANT_TEXT = "#__next > div.sc-f9c982a5-1.bVsWPX.global-layout-v2 > div > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.ljtNVi.notice-container > section > div > div > span"

PROJECT_NAME_TEXT = "//span[@data-role='coin-name']"
PROJECT_TICKER_TEXT = "//span[@data-role='coin-symbol']"
MARKET_CAP_TEXT = "//div[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'market cap']/ancestor::dt/following-sibling::dd//span[contains(text(), '$')]"
FDV_TEXT = "//div[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'fdv']/ancestor::dt/following-sibling::dd//span[contains(text(), '$')]"
TWENTYFOUR_HR_VOL_TEXT = "#section-coin-stats > div > div > dl > div:nth-child(2) > div > dd > div > div.CoinMetrics_overflow-content__tlFu7 > div > span"
FDV_TEXT = "#section-coin-stats > div > div > dl > div:nth-child(3) > div > dd > div > div > div > span"
TWENTYFOUR_HR_VOL_DIVIDE_MARKET_CAP_TEXT = "#section-coin-stats > div > div > dl > div:nth-child(4) > div > dd > div > div"
TOTAL_SUPPLY_TEXT = "#section-coin-stats > div > div > dl > div:nth-child(5) > div > dd > div > div > div > span"
MAX_SUPPLY_TEXT = "#section-coin-stats > div > div > dl > div:nth-child(6) > div > div.sc-65e7f566-0.eQBACe.StatsInfoBox_content-wrapper__onk_o > div > div > div > span"
CIRCULATING_SUPPLY_TEXT = "#section-coin-stats > div > div > dl > div.sc-65e7f566-0.eQBACe.CoinMetrics_group-item-full__ncOjB > div > dd > div > div:nth-child(1) > span"

WEBSITE_LINK = "div.CoinInfoLinks_info-items-wrapper__dHVKe > div:nth-child(1) > div.InfoBarItem_value__au1BG > div > div > div > a"
SOCIALS_LINKS = "div.CoinInfoLinks_info-items-wrapper__dHVKe > div:nth-child(2) > div.InfoBarItem_value__au1BG > div > div > div > div > a"
ABOUT_TEXT = "#section-coin-about > div.sc-4fc2860f-0.eyGmhU > div:nth-child(2) > section > div"
# ABOUT_TEXT = "#section-coin-about > div.sc-4fc2860f-0.eyGmhU > div:nth-child(2) > section > div > div > div > div > div > div or span"
SHOW_ALL_TAGS_BUTTON = "#__next > div.sc-f9c982a5-1.bVsWPX.global-layout-v2 > div > div.cmc-body-wrapper > div > div > div.sc-4c05d6ef-0.sc-da3461a8-0.dlQYLv.iwYbsh.coin-stats > div > div.sc-65e7f566-0.eGAMZw > section > div > div.sc-65e7f566-0.fFHGof.coin-tags > div.sc-65e7f566-0.eQBACe > div > span.sc-65e7f566-0.sc-9ee74f67-1.ckjyAl.izfTnl"
TAGS = "div.coin-tags > div > div > span:nth-child(1) > a"
TAGS_SECTION = "//div[contains(@class, 'coin-tags')]/div/div/span"
TAGS_MODAL = "//div[contains(@class, 'cmc-modal')]/div/div/div/span/a"
TAGS_MODAL_2 = "//div[contains(@class, 'cmc-modal')]/div/div/div/div/span[text()]"
EXCHANGE_ROWS_OPTION = "//span[text()='Show rows']/following-sibling::div"
EXCHANGE_ROWS_100 = "//div[@class='tippy-content']/div/div/button[text()='100']"
EXCHANGE_LINK_12 = "//div[@id='section-coin-markets']/section/div/div/div/div/table/tbody/tr[x]/td/span/a"
# NEXT_PAGE_BUTTON = "(//ul[@class='pagination'])[last()]/li[@class='next']/a"
NEXT_PAGE_BUTTON = "(//ul[@class='pagination'])[1]/li[@class='next']/a"

MARKETS_TABLE = "#section-coin-markets > section > div > div > div.sc-40bc2850-0.fARwNm > div.sc-936354b2-2.cXaKXy > table.cmc-table"
SHOW_ALL_MARKET_BUTTON = "#section-coin-markets > section > div > div > div:nth-child(1) > div > div > div > div:nth-child(1) > button:nth-child(2)"
SHOW_CEX_BUTTON = 'li[data-role="Tab"][data-index="tab-cex"]'
SHOW_DEX_BUTTON = "#section-coin-markets > section > div > div > div:nth-child(1) > div > div > div > div:nth-child(1) > button:nth-child(4)"
NO_DATA_TEXT = "table.cmc-table > tbody > tr > td > div > h2"
# enumerate from nth-child(2) onwards

MARKET_TITLE_TEXT = "table.cmc-table > tbody > tr > td > span > a > div > div > p"
VOL_PERC_TEXT = "table.cmc-table > tbody > tr:nth-child(2) > td:nth-child(8) > span"
LIQUIDITY_TEXT = "table.cmc-table > tbody > tr:nth-child(2) > td:nth-child(10) > span"






