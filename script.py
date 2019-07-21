import re
import datetime
import os
import sqlite3
from fake_useragent import UserAgent
import shutil
from stem import Signal
from stem.control import Controller
import socket
import socks
import requests
from random import randint, shuffle
from time import sleep
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

controller = Controller.from_port(port=9051)
controller.authenticate()

def connectTor():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5 , "127.0.0.1", 9050)
    socket.socket = socks.socksocket

def renew_tor():
    controller.signal(Signal.NEWNYM)

def showmyip():
    url = "http://www.showmyip.gr/"
    r = requests.Session()
    page = r.get(url)
    soup = BeautifulSoup(page.content, "lxml")
    ip_address = soup.find("span",{"class":"ip_address"}).text.strip()
    print(ip_address)
    
UA = UserAgent(fallback='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2')

hdr = {'User-Agent': "'"+UA.random+"'",
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

def get_html(url):
    html_content = ''
    try:
        req = Request(url, headers=hdr)
        html_page = urlopen(req).read()
        html_content = BeautifulSoup(html_page, "html.parser")
    except: 
        pass
    return html_content

def get_categories():
    
    url = 'https://www.candlishmccleery.com/page/home.php'
    
    items = {}
    try:
        html = get_html(url)
        category_items = html.find_all('div', attrs={'style': 'margin-left: 0px'})
        for category_item in category_items:
            item_url = category_item.find('a').get('href').replace('../', 'https://www.candlishmccleery.com/')
            item_text = category_item.find('a').get_text().strip()
            items[item_text] = item_url
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

def file_names(stamp):
    file_name = []
    rand_string = "RAND_ze"+str(randint(0,100000))
    file_name = [rand_string+"-" + str(i) + ".png" for i in range(len(stamp['image_urls']))]
    return(file_name)

def query_for_previous(stamp):
    # CHECKING IF Stamp IN DB
    os.chdir("/Volumes/stamps_copy/")
    conn1 = sqlite3.connect('Reference_data.db')
    c = conn1.cursor()
    col_nm = 'url'
    col_nm2 = 'raw_text'
    unique = stamp['url']
    unique2 = stamp['raw_text']
    c.execute('SELECT * FROM zeboose WHERE "{col_nm}" LIKE "{unique}%" AND "{col_nm2}" LIKE "{unique2}%"')
    all_rows = c.fetchall()
    conn1.close()
    price_update=[]
    price_update.append((stamp['url'],
    stamp['raw_text'],
    stamp['scrape_date'], 
    stamp['price'], 
    stamp['currency']))
    
    if len(all_rows) > 0:
        print ("This is in the database already")
        conn1 = sqlite3.connect('Reference_data.db')
        c = conn1.cursor()
        c.executemany("""INSERT INTO price_list (url, raw_text, scrape_date, price, currency) VALUES(?,?,?,?,?)""", price_update)
        conn1.commit()
        conn1.close()
        print (" ")
        #url_count(count)
        sleep(randint(10,45))
        pass
    else:
        os.chdir("/Volumes/stamps_copy/")
        conn2 = sqlite3.connect('Reference_data.db')
        c2 = conn2.cursor()
        c2.executemany("""INSERT INTO price_list (url, raw_text, scrape_date, price, currency) VALUES(?,?,?,?,?)""", price_update)
        conn2.commit()
        conn2.close()
    print("Price Updated")

def db_update_image_download(stamp):  
    req = requests.Session()
    directory = "/Volumes/stamps_copy/stamps/zeboose/" + str(datetime.datetime.today().strftime('%Y-%m-%d')) +"/"
    image_paths = []
    file_name = file_names(stamp)
    image_paths = [directory + file_name[i] for i in range(len(file_name))]
    print("image paths", image_paths)
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    for item in range(0,len(file_name)):
        print (stamp['image_urls'][item])
        try:
            imgRequest1=req.get(stamp['image_urls'][item],headers=hdr, timeout=60, stream=True)
        except:
            print ("waiting...")
            sleep(randint(3000,6000))
            print ("...")
            imgRequest1=req.get(stamp['image_urls'][item], headers=hdr, timeout=60, stream=True)
        if imgRequest1.status_code==200:
            with open(file_name[item],'wb') as localFile:
                imgRequest1.raw.decode_content = True
                shutil.copyfileobj(imgRequest1.raw, localFile)
                sleep(randint(18,30))
    stamp['image_paths']=", ".join(image_paths)
    #url_count += len(image_paths)
    database_update =[]

    # PUTTING NEW STAMPS IN DB
    database_update.append((
        stamp['url'],
        stamp['raw_text'],
        stamp['title'],
        stamp['scott_num'],
        stamp['SG'],
        stamp['country'],
        stamp['year'],
        stamp['category'],
        stamp['sku'],
        stamp['scrape_date'],
        stamp['image_paths']))
    os.chdir("/Volumes/stamps_copy/")
    conn = sqlite3.connect('Reference_data.db')
    conn.text_factory = str
    cur = conn.cursor()
    cur.executemany("""INSERT INTO zeboose ('url','raw_text', 'title', 'scott_num','SG',
    'country','year','category','sku','scrape_date','image_paths') 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", database_update)
    conn.commit()
    conn.close()
    print ("all updated")
    print ("++++++++++++")
    print (" ")
    sleep(randint(45,140)) 

count = 0
connectTor()
showmyip()

# choose input category
categories = get_categories()
for category_item in categories.items():
    print(category_item)

selected_category_name = input('Make a selection: ')
category = categories[selected_category_name]

while(category):
    count += 1
    page_items, category, category_name = get_page_items(category)
    # loop through all items on current page
    for page_item in page_items:
        stamp = get_details(page_item, category_name)
        count += 1
        if count > randint(75,156):
            sleep(randint(500,2000))
            connectTor()
            showmyip()
            count = 0
        else:
            pass
        stamp = get_details(category_item, continent)
        count += len(f_names)
        query_for_previous(stamp)
        db_update_image_download(stamp)