from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import os
import pandas as pd
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from bs4 import BeautifulSoup
import requests
import itertools
import re
import numpy as np
import urllib3
import warnings
warnings.filterwarnings("ignore")

# 创建 Dash 应用
app = Dash(__name__)

fig = px.scatter()

# 设置布局
app.layout = html.Div([
    html.H1(children='Hotel Data Dashboard', style={'textAlign': 'center'}),
    dcc.Input(id='location-input', type='text', placeholder='Enter location: '),
    
    dcc.DatePickerSingle(
        id='checkin-date-picker',
        date='2023-12-01',  # 设置默认日期
        display_format='YYYY-MM-DD'
    ),
    
    dcc.DatePickerSingle(
        id='checkout-date-picker',
        date='2023-12-02',  # 设置默认日期
        display_format='YYYY-MM-DD'
    ),
    html.Button('Scrape Data', id='scrape-button', n_clicks=0),
    dcc.Graph(id='graph-content', figure=fig)
])

def clean_distance(value):
    try:
        if 'k' in value:
            value = value.replace('km', '')
            value = value.replace('k', '')
            return float(value.strip())
        else:
            value = value.replace('m', '')
            return float(value.strip()) / 1000
    except:
        return np.nan

def clean_rating(value):
    try:
        return float(value)
    except:
        return np.nan
        
def clean_price(value):
    if type(value) == int or type(value) == float:
        return value
    else:
        return int(value.replace('TWD', '').replace(',', ''))
    
@app.callback(
    Output('graph-content', 'figure'),
    Input('scrape-button', 'n_clicks'),
    State('location-input', 'value'),
    State('checkin-date-picker', 'date'),
    State('checkout-date-picker', 'date')
)
def update_graph(n_clicks, location, checkin_date, checkout_date):
    if n_clicks > 0:
        df = scrape_data(location, checkin_date, checkout_date)
        fig = create_graph(df)
        return fig
    else:
        return px.scatter()


def scrape_data(location, checkin_date, checkout_date):
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'https://www.booking.com/index.en-gb.html',
    }
    df = pd.DataFrame(columns=['name','address', 'distance', 'rating', 'comment', 'price'])
    numberHotel = 0
    error = 0
    n = 0
    print(location, checkin_date, checkout_date)
    while True:
        url = f'https://www.booking.com/searchresults.zh-tw.html?ss={location}&checkin={checkin_date}&checkout={checkout_date}&group_adults=2&selected_currency=TWD&lang=en-us&soz=1&order=distance_from_search&offset={numberHotel}'
        response = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        hotel_items = soup.find_all('div', {'data-testid': 'property-card-container'})  # 假设每个酒店条目都有这个类名

        for item in hotel_items:
            name_element = item.find('div', {'data-testid': 'title'})  # 查找酒店名称
            address_element = item.find('span', {'data-testid': 'address'})
            distance_element = item.find('span', {'data-testid': 'distance'})  # 查找距离
            rating_element = item.find('div', {'class': "a3b8729ab1 d86cee9b25"})  # 查找评分
            comment_element = item.find('div', {'class': 'a3b8729ab1 e6208ee469 cb2cbb3ccb'})
            price_element = item.find('span', {'data-testid': 'price-and-discounted-price'})
            if name_element:
                try:
                    name = name_element.text.strip()
                    address = address_element.text.strip()
                    distance = distance_element.text[0:5].strip()
                    rating = rating_element.text.strip()
                    comment = comment_element.text.strip()
                    price = price_element.text.strip()
                    data_dict = {'name': name,'address':address, 'distance': distance, 'rating': rating, 'comment': comment, 'price': price}
                    df = df.append(data_dict, ignore_index=True)
                    n += 1
                except:
                    error += 1

            else:
                break
        try:
            totalHotel = int(soup.find('div', {'class': 'd8f77e681c'}).text.strip()[-20:-17])  # 假设每个酒店条目都有这个类名
        except:
            break
        numberHotel += 25
        if n + error == totalHotel:
            break
        # if numberHotel == 200:
        #     break
        print(df.info())
    
    df['distance'] = df['distance'].apply(clean_distance)
    df['price'] = df['price'].apply(clean_price)
    df['rating'] = df['rating'].apply(clean_rating)
    return df

def create_graph(df):
    fig = px.scatter(df, x='price', y='distance', hover_data=['name','comment'], color='rating')
    fig.update_traces(hovertemplate='Name: %{customdata[0]}<br>Distance: %{y}<br>Price: %{x}<br>Comment: %{customdata[1]}')
    total_hotels_text = f'Total Hotels: {len(df)}'
    fig.update_layout(title_text=total_hotels_text, title_x=0.5, title_font=dict(size=20))
    return fig

if __name__ == '__main__':
    app.run(debug=True)
