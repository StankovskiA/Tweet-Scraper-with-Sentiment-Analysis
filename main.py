import csv
from time import sleep
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer
from nltk.tokenize import regexp
from textblob import TextBlob

stop_words = stopwords.words("english")
stemmer = SnowballStemmer("english", ignore_stopwords=True)
lemmatizer = WordNetLemmatizer()
word_tokenizer = regexp.WhitespaceTokenizer()



def get_tweet_data(card):
    username = card.find_element_by_xpath('.//span').text
    handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    try:
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except NoSuchElementException:
        return
    comment = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    responding = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    text = comment + responding
    reply_cnt = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    retweet_cnt = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    like_cnt = card.find_element_by_xpath('.//div[@data-testid="like"]').text

    tweet = (username, handle, postdate, text, reply_cnt, retweet_cnt, like_cnt)
    return  tweet


driver = Firefox()
driver.get('https://www.twitter.com/login')
driver.maximize_window()
sleep(2)
username = driver.find_element_by_xpath('//input[@name="session[username_or_email]"]')
username.send_keys('INSERT-USERNAME/EMAIL-HERE')

my_password = 'INSERT-PASSWORD-HERE'
password = driver.find_element_by_xpath('//input[@name="session[password]"]')
password.send_keys(my_password)
password.send_keys(Keys.RETURN)
sleep(3)
search_input = driver.find_element_by_xpath('//input[@aria-label="Search query"]')
#Change $btc to any word/hashtag you want to search
search_input.send_keys("$btc")
search_input.send_keys(Keys.RETURN)
sleep(3)
#Uncomment this line if you want to get tweets from Latest page, leave if you want the top tweets
#driver.find_element_by_link_text('Latest').click()

data = []
tweet_ids = set()
last_position = driver.execute_script("return window.pageYOffset;")
scrolling = True
count=0

while True:
    count += 1
    sleep(3)
    page_cards = driver.find_elements_by_xpath('//div[@data-testid="tweet"]')
    for card in page_cards:
        tweet = get_tweet_data(card)
        if tweet:
            tweet_id = ''.join(tweet)
            if tweet_id not in tweet_ids:
                tweet_ids.add(tweet_id)
                data.append(tweet)
    scroll_attempt = 0

    while True:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        sleep(1)
        curr_position = driver.execute_script('return window.pageYOffset;')
        if last_position == curr_position:
            scroll_attempt += 1

            if scroll_attempt >= 3:
                scrolling = False
                break
            else:
                sleep(2)
        else:
            last_position = curr_position
            break
    if count == 4:
        break

with open("btc_tweets.csv",'w',newline='', encoding='utf-8') as f:
    header = ['UserName', 'Handle', 'Timestamp', 'Comments', 'Likes', 'Retweets', 'Text', 'Polarity', 'Subjectivity']
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data)

df = pd.read_csv('btc_tweets.csv')
for index, row in df.iterrows():
    text = row['Comments']
    tokenized_text = [word.lower() for word in word_tokenizer.tokenize(text)]
    words = [lemmatizer.lemmatize(w) for w in tokenized_text if w not in stop_words]
    stem_text = " ".join([stemmer.stem(i) for i in words])
    analysis = TextBlob(text)
    df.loc[index, 'Polarity'] = analysis.sentiment.polarity
    df.loc[index, 'Subjectivity'] = analysis.sentiment.subjectivity


print("Overall sentiment of the analyzed tweets: " + df['Polarity'].mean())
