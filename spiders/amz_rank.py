import scrapy
import pymysql
from time import sleep
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from datetime import date, timedelta,datetime
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from selenium import webdriver
#from amazon_rank.items import AmazonRankItem

# 
result = dict()

true_rank = []

#class extract_info(scrapy.spider):
class insert_data(scrapy.Spider):
    
    name = "insert_att"
    download_delay = 2
    start_urls = []

  
            
    def parse(self, response):
        
        #date 
        today = date.today()
        today = str(today).split("-")
        today = today[0] + "-" + today[1] + "-" + today[2]
          
        sku_asin_table_head = response.xpath("""//th[@class="a-color-secondary a-size-base prodDetSectionEntry"]//text()""").extract()
        sku_asin_table_value = response.xpath("""//td[@class="a-size-base"]""")
           
        asin = 'None'
        sku = 'None'
        starcount = 0
        review_count = 0
        
        try:
            for a,b in zip(sku_asin_table_head,sku_asin_table_value):
                if a.strip() == "ASIN":
                    temp_asin= b.xpath('text()').extract()
                    temp_asin = ''.join(temp_asin).strip()
                    asin = temp_asin
                elif a.strip() == "Item model number":
                    temp_sku= b.xpath('text()').extract()
                    temp_sku = ''.join(temp_sku).strip()
                    sku = temp_sku
                elif a.strip() == "Customer Reviews":
                    temp_star= b.xpath('text()').extract()
                      
                    num_review = b.xpath("div[@id='averageCustomerReviews']//span[@class='a-declarative']//a[@id='acrCustomerReviewLink']//span[@id='acrCustomerReviewText']//text()").extract_first()
                    num_review = num_review.split()[0]
                    num_review = num_review.split(',')
                    num_review = int(''.join(num_review))
                        
                    review_count = num_review
                      
                    temp_star = ''.join(temp_star).strip()
                      
                    starcount = float(temp_star.split()[0])
        except: pass
       
        best_seller_rank = response.xpath("""//table[@id="productDetails_detailBullets_sections1"]/tr/td/span/span""")
          
        pre_rank_list = []
        for x in best_seller_rank:
           reg_text = x.xpath('text()').extract()
           link_text = x.xpath('a/text()').extract()
           pre_rank = ''
           for a,b in zip(reg_text,link_text):
              pre_rank = pre_rank + a + b
           pre_rank_list.append(pre_rank)
             
        best_seller = ")".join(pre_rank_list)
                 
         
        title = response.xpath("""//span[@id="productTitle"]//text()""").extract_first().strip()
        
        
        orig_price = response.xpath("""//td[@class='a-span12 a-color-secondary a-size-base']//span[@class='a-text-strike']/text()""").extract_first()

        if orig_price != None:
            #print(orig_price[2:])
            orig_price = float(orig_price[2:])
        else:
            orig_price = 0
         
        price = response.xpath("""//span[@id='priceblock_ourprice']//text()""").extract_first()
        
        if price == None:
            price = response.xpath("""//span[@id='priceblock_dealprice']//text()""").extract_first()

        else:
            orig_price = 0

        try :
            price = float(price[1:])
        except:
            pass


     
        try:
            stock_status = response.xpath("""//div[@id='availability']/span/text()""").extract_first().strip()
        except:
            stock_status = 'None'
        
        Arrivebefore = 'None'
        try:
            Arrivebefore = response.xpath("""///div[@class='a-section a-spacing-none']/span[@class='a-text-bold']/text()""").extract_first().strip()
        except:pass
         
        promo = 'None'
         
        try:
           promo = response.xpath("""//span[@class='apl_message']/span/span/text()""").extract_first().strip()
        except: pass
        
        
        
        seller = "None"
        try:
            seller = response.xpath("""//a[@id='bylineInfo']/text()""").extract_first().strip()
        except: pass
        
        
        

        result[response.url] = [today,seller,asin,sku,title,orig_price,price,best_seller,starcount,review_count,stock_status,Arrivebefore,promo]
        
        
        



if __name__ == "__main__":

    def first():
       
        maxs = 10
        count = 0

        
        #search_term = input("Please input search term: ")
        search_term = 'galaxy s9 case'
        chrome_path = r"C:\\Library\\chromedriver_win32\\chromedriver.exe"
        driver = webdriver.Chrome(chrome_path)
        
        sleep(1)
           
        driver.get("https://amazon.com/")
        sleep(1)
        driver.find_element_by_id("twotabsearchtextbox").send_keys(search_term)
        driver.find_element_by_class_name("nav-input").click()
        final = []
        tt= []
        asins = []
        for x in range(maxs):
            
            
            pre_links = driver.find_elements_by_xpath("""//a[@class='a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal']""")
            new_links = [x.get_attribute("href") for x in pre_links if "gp/slredirect" not in x.get_attribute("href")]
            title = [x.get_attribute("title") for x in pre_links if "gp/slredirect" not in x.get_attribute("href")]
 

            tt = tt + title
            final = final + new_links

            
            sleep(2)
            driver.find_element_by_xpath("""//span[@id='pagnNextString']""").click()

            sleep(2)

        for x in final:
            true_rank.append(x)

        print(len(true_rank))


        for x in tt:
            print(x)


        for x in final:
            yield x
 
    
    
    setattr(insert_data, 'start_urls', first())

    
    configure_logging()
    runner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(insert_data)
        reactor.stop()
    
    crawl()
   
    reactor.run()


    print(len(true_rank))
    print(len(result))

    conn = pymysql.connect(host='', port=3306, user='', passwd="", db='crawl_amazon_rank',charset="utf8", use_unicode=True)
 
    cur = conn.cursor()
    
    counter = 1
    for x in true_rank:
        for k,v in result.items():
            if x == k:
                
                cur.execute("""""",(counter,v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9],v[10],v[11],v[12]))
                conn.commit()
                counter = counter + 1

    


 
     
    
    













