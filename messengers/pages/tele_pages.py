
SEARCH_BOX = "div.input-search > input"
FIRST_CHAT_OPTION = "#folders-container > div.scrollable.scrollable-y.tabs-tab.chatlist-parts.active > div.chatlist-top > ul > a:nth-child(1) > div.dialog-title"
USERNAME_SEARCH_RESULT__3 = "//a/div/div[text()='x']"
INPUT_TEXT_MESSAGE = "#column-center > div > div.chat.tabs-tab.can-click-date.active > div.chat-input.chat-input-main > div > div.rows-wrapper-wrapper > div > div.new-message-wrapper.rows-wrapper-row > div.input-message-container > div:nth-child(1)"
SEND_BUTTON = "#column-center > div.chats-container.tabs-container > div:last-child > div.chat-input.chat-input-main > div > div.btn-send-container > button"
NAME = "#column-center > div > div.chat.tabs-tab.can-click-date.active > div.sidebar-header.topbar.has-avatar > div.chat-info-container > div.chat-info > div > div.content > div.top > div > span"
CANVAS_GREETING = "#column-center > div > div > div.bubbles.scrolled-down > div.bubble.service.is-group-last.is-group-first.bubble-first.empty-bubble-placeholder.empty-bubble-placeholder-greeting.has-description > div > div > div > div > canvas"
BACK_BUTTON = "#column-center > div.chats-container.tabs-container > div.chat.tabs-tab.can-click-date.active > div.sidebar-header.topbar.has-avatar.is-pinned-message-shown > div.chat-info-container > button"

#ChainReach AI page
CHAIN_REACH_AI_MESSAGE = "//strong[text()='outreach way easier in Web3']"

# SafeGuard page
TAP_TO_VERIFY_BUTTON = "(//div/div/a//span[contains(text(), 'verify')])[last()]"
LAUNCH_SAFEGUARD_POPUP = "/html/body/div/div/div/button/span[text()='Launch']"
START_SAFEGUARD_ONCE = "//div[contains(@class, 'active')]/div/div/div/button/span[text()='START']"
SAFEGUARD_VERIFY_PORTAL_LINK = "(//div/div/button[span[contains(text(), 'VERIFY')]])[last()]"
SAFEGUARD_LAUNCH_BUTTON = "/html/body/div[8]/div/div[2]/button[1]/span"
LAUNCH_SAFEGUARD_BROWSER = "body > div.popup.popup-peer.popup-confirmation.active > div > div.popup-buttons > button:nth-child(1)"
SAFEGUARD_BROWSER_IFRAME = "/html/body/div/div/div/div/div/iframe"
SAFEGUARD_BROWSER_CLICK_HERE_BUTTON = "//button[contains(text(), 'Click here')]"
SAFEGUARD_ONE_TIME_GROUP_LINK = "(//section/div/div/div/div[1]/div[2]/span/a)[last()]"
JOIN_GROUP_BUTTON = "body > div.popup.popup-peer.popup-join-chat-invite.active > div > div.popup-buttons > button:nth-child(1)"

# Telegram Group
OPEN_GROUP_INFO_SECTION = "//*[@id='column-center']/div[1]/div/div[2]/div[1]/div[1]/div/div[1]"
GROUP_INFO_SCROLL_SECTION = "//*[@id='column-right']/div/div/div[2]/div/div/div[6]/div[2]/div[3]/div/ul/a"
TARGET_ADMIN_A_TAG = """
//*[@id='column-right']/div/div/div[2]/div/div/div[6]/div[2]/div[3]/div/ul/a[
  (
    div[2]/div[string-length(normalize-space(text())) > 0]
    or
    div[2]/div[2]/span[string-length(normalize-space(text())) > 0]
  )
  and
  not(contains(translate(div[1]/div/span, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'users'))
  and
  not(contains(translate(div[1]/div/span, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bot'))
]
"""
TARGET_A_TAG_ROLE_TEXT_1 = "./" + "/div[2]/div[2]/span[string-length(normalize-space(text())) > 0]"
TARGET_A_TAG_ROLE_TEXT_2 = "./" + "/div[2]/div[string-length(normalize-space(text())) > 0]"
TARGET_A_TAG_NAME_TEXT_1 = "./" + "/div[2]/div[1]/span[@class='peer-title']"
TARGET_A_TAG_NAME_TEXT_2 = "./" + "/div[2]/div[1]/span/span[@class='peer-title-inner']"
GROUP_INFO_USERNAME_TEXT = "#column-right > div > div > div.sidebar-content > div > div > div:nth-child(3) > div > div > div:nth-child(2) > div.row-title"

# Schedule message
SCHEDULE_MESSAGE_BUTTON = "//*[@id='column-center']/div[1]/div[last()]/div[4]/div/div[5]/div[4]/div[2]/div[2]/span[text()='Schedule Message']"
MONTH_YEAR_TEXT = "body > div.popup.popup-date-picker.popup-schedule.active > div > div > div.popup-header > div.date-picker-month-title > span"
NEXT_MONTH_BUTTON = "body > div.popup.popup-date-picker.popup-schedule.active > div > div > div.popup-header > div.date-picker-controls > button.btn-icon.date-picker-next.primary"
DAY_BUTTON__3 = "//div[contains(@class, 'popup-date-picker') and contains(@class, 'active')]//div[contains(@class, 'date-picker-months')]//button[not(@disabled) and text()='x']"
HOUR_INPUT = "div.popup-body > div.date-picker-time > div:nth-child(1) > input"
MINUTE_INPUT = "div.popup-body > div.date-picker-time > div:nth-child(3) > input"
SCHEDULE_SEND_BUTTON = "div.popup-body > button"

