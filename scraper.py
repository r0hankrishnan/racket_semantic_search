import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import logging

# Helper function to get all brand page URLs
# from the side navbar
def get_brand_URLs(shop_all_URL: str) -> list[str]:
    webpage = requests.get(shop_all_URL)
    soup = BeautifulSoup(webpage.content, "html.parser")
    sidebar_links = soup \
        .find_all("ul", attrs = {"class": "left_menu-section"})
    brand_elements = sidebar_links[1].find_all("li")
    
    brand_pointer_list = []
    
    for brand in brand_elements:
        brand_pointer = brand.find("a").get("href")
        brand_pointer_list.append(brand_pointer)
    
    brand_page_URLs = ["https://www.tennis-warehouse.com"+ pointer for pointer in brand_pointer_list]
    
    return brand_page_URLs


# Helper function to generate a list of all product page URLs
# from a given brand page URL
def get_product_page_URLs(brand_page_URL: str)->list[str]:
    webpage = requests.get(brand_page_URL)
    soup = BeautifulSoup(webpage.content, "html.parser")
    product_elements = soup \
        .find_all("a", attrs = {"class": "cattable-wrap-cell-info"})
    
    product_page_URLs = []
    for product_element in product_elements:
        product_URL = product_element.get("href")
        if "https://www.tennis-warehouse.com/" in product_URL:
            product_page_URLs.append(product_URL)
        else:
            pass
        
    return product_page_URLs


# Helper function to extract racquet specs from the product's
# soup object
def get_racquet_specs(soup: BeautifulSoup) -> dict:
    racquet_specs = {}
    
    if soup.find("tbody"):
        racquet_spec_elements = soup.find("tbody")\
            .find_all("td", class_ = re.compile("Specs")) # type:ignore
        
        for spec in racquet_spec_elements:
            if spec.find("strong"):
                label = spec.find("strong").text.split(":")[0].strip()
                value = spec.text.split(":")[1].strip()
            else:
                label = "Other"
                value = spec.text.strip()
                
                racquet_specs[label] = value
    else:
        racquet_specs = {"Head Size": np.nan,
                  "Length": np.nan,
                  "Strung Weight": np.nan,
                  'Balance:': np.nan,
                  'Swingweight:': np.nan,
                  'Stiffness:': np.nan,
                  'Beam Width:': np.nan,
                  'Composition:': np.nan,
                  'Power Level:': np.nan,
                  'Stroke Style:': np.nan,
                  'Swing Speed:': np.nan,
                  'Racquet Colors:': np.nan,
                  'Grip Type:': np.nan,
                  'String Pattern:': np.nan,
                  'String Tension:': np.nan}
    
    return racquet_specs


#Get racquet features from a product page and return a DataFrame
def get_racquet_features(product_page_URL: str) -> pd.DataFrame:
    webpage = requests.get(product_page_URL)
    soup = BeautifulSoup(webpage.content, "html.parser")
    
    # Extract features from top part of page
    racquet_info = {}
    
    racquet_info["racquet_img"] = soup \
        .find("img", attrs = {"class": "main_image is-zoomable"}) \
            .get("src") # type:ignore
    racquet_info["racquet_name"] = soup \
        .find("h1", attrs = {"class": "h2 desc_top-head-title"}).text # type:ignore
    
    # Check if the racket has ratings, if not assign the rating as NA
    if soup.find("div", attrs = {"class": "review_agg"}):
        racquet_info["racquet_rating"] = float(soup \
            .find("div", attrs = {"class": "review_agg"}).text) # type:ignore
    else:
        racquet_info["racquet_rating"] = np.nan

    ## The code below doesn't work because it throws an error when a racket has no ratings
    #racquet_info["racquet_rating"] = float(soup.find("div", attrs = {"class": "review_agg"}).text)
    
    racquet_info["racquet_price"] = float(soup \
        .find("span", attrs = {"class": "afterpay-full_price"}).text) # type:ignore
    
    racquet_info["racquet_desc"] = soup \
        .find("div", attrs = {"class": "check_read-inner"}).text # type:ignore
    
    # Use get_racquet_specs helper function
    racquet_specs = get_racquet_specs(soup)
    
    #Combine top info and specs dictionaries
    racquet_info.update(racquet_specs)
    
    racquet_info_df = pd.DataFrame(racquet_info, index=[0])
    
    return racquet_info_df


# Get racquet features for all products listed on a brand page
# and return a DataFrame with all of the information
def scrape_brand_page(brand_page_URL):
    product_URLs = get_product_page_URLs(brand_page_URL= brand_page_URL)
    
    total_racquet_info_df = pd.DataFrame()
    for product_URL in product_URLs:
        racquet_info_df = get_racquet_features(product_URL)
        total_racquet_info_df = pd.concat([total_racquet_info_df,
                                           racquet_info_df])
 
    return total_racquet_info_df


# Run scraping functions over all brand pages and store results 
# in a single DataFrame
def scrape_all_brand_pages(brand_page_URLs: list[str]) -> pd.DataFrame:
    i = 0
    final_df = pd.DataFrame()
    for brand_URL in brand_page_URLs:
        df = scrape_brand_page(brand_URL)
        final_df = pd.concat([final_df, df])
        
        logging.debug(f"Completed brand {i}")
        i += 1
    
    logging.info(f"Successfully scraped all {i} brands \
        (if this works on the first try it'd be a miracle)!")
    return final_df


# Main function
if __name__ == "__main__":
    shop_all_URL = "https://www.tennis-warehouse.com/shop-all-racquets/"
    
    brand_page_URLs = get_brand_URLs(shop_all_URL = shop_all_URL)
    
    complete_racquet_info_df = pd.DataFrame()
    
    for brand_URL in brand_page_URLs:
        brand_df = scrape_brand_page(brand_page_URL = brand_URL)
        complete_racquet_info_df = pd.concat(
            [complete_racquet_info_df, brand_df]
        )
    
    print("Scraping complete. Congrats on not messing up!")
    print("--------------------------") 
    print(complete_racquet_info_df.shape)
    print("--------------------------") 
    print(complete_racquet_info_df.head(5))
    
    save_toggle = input("Do you want to save this \
                        dataframe to a CSV file? (y/n): ")
    
    if save_toggle.lower().strip() == "y":
        filename = input("Enter the file name (including .csv and path): ")
        complete_racquet_info_df.to_csv(f"{filename}", 
                                        index = False, sep = ",")
    
    else:
        print("Ogei bye.")