import datetime
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from time import sleep
from random import randint,shuffle

def get_html(url):
    html_content = ''
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(req).read()
        html_content = BeautifulSoup(html_page, "html.parser")
    except: 
        pass
        
    return html_content

def get_categories(url):
    items = []
    try:
        html = get_html(url)
        category_items = html.find_all('div', attrs={'style': 'margin-left: 0px'})
        for category_item in category_items:
            item = category_item.find('a').get('href').replace('../', 'https://www.candlishmccleery.com/')
            items.append(item)
    except: 
        pass

    return items

def get_page_items(url):
    
    items = []
    next_url = ''
    category_name = ''

    try:
        html = get_html(url)
    except:
        return items, next_url

    try:
        category_name = html.select("#mainColumn h1")[0].get_text()
    except:
        pass
    
    try:
        for item in html.select('.categoryProduct'):
            items.append(item)
    except: 
        pass


    try:
        next_items = html.select('.pageNumbers a')
        for next_item in next_items:
            next_item_text = next_item.get_text()
            if 'Next' in next_item_text:
                next_url = 'https://www.candlishmccleery.com/' + next_item.get('href')
                break
    except:
        pass
    
    shuffle(items)

    return items, next_url, category_name

def get_details(html, category_name):
    
    stamp = {}

    try:
        price_cont = html.find_all("div", {"class":"productPrice"})[0]
        price = get_value('</span>', '<input', price_cont)
        price = price.replace('£','').strip()
        stamp['price'] = price
    except:
        stamp['price'] = None

    try:
        sku = html.find_all("span", {"class":"productRef"})[0].get_text()
        sku = sku.replace("Ref.", "").strip()
        stamp['sku'] = sku
    except:
        stamp['sku'] = None

    try:
        raw_text = html.find_all("div")[0].get_text().strip()
        stamp['raw_text'] = raw_text
    except:
        stamp['raw_text'] = None

    stamp['category'] = category_name

    stamp['currency'] = 'GBP'

    # image_urls should be a list
    images = []
    try:
        image_items = html.find_all('img', {'class': 'productImage'})
        for image_item in image_items:
            img = image_item.get('src').replace('thumbs', 'images')
            img = img.replace('../', 'https://www.candlishmccleery.com/')
            images.append(img)
    except:
        pass

    stamp['image_urls'] = images 

    # scrape date in format YYYY-MM-DD
    scrape_date = datetime.date.today().strftime('%Y-%m-%d')
    stamp['scrape_date'] = scrape_date

    print(stamp)
    print('+++++++++++++')
    sleep(randint(22,99))
    
    return stamp

def get_value(sep1,sep2, string):
    string = str(string)
    parts1 = string.split(sep1)
    parts2 = parts1[1].split(sep2)
    return parts2[0]

# start url
start_url = 'https://www.candlishmccleery.com/page/home.php'

# loop through all categories
categories = get_categories(start_url)
for category in categories:
    while(category):
        page_items, category, category_name = get_page_items(category)
        # loop through all items on current page
        for page_item in page_items:
            stamp = get_details(page_item, category_name)