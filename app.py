import json
import asyncio
import requests
from flask import Flask, request, jsonify
from utils import crawl_multiple_urls, is_related_to_topic, auth_token

app = Flask(__name__)

urls = [
    'https://decrypt.co/news',
    'https://cryptoslate.com/news/'
]

@app.route('/scrape', methods=['POST'])
def scrape_and_summarize():
    data = request.get_json(force=True)
    topic = data.get('topic')

    results = asyncio.run(crawl_multiple_urls(urls))

    processed_results = []

    for i, result in enumerate(results):
        if result.success:
            try:
                page_summary = json.loads(result.extracted_content)
                for article in page_summary:
                  if topic:
                    if not is_related_to_topic(article, topic):
                      continue
                  processed_results.append({
                      "title": article['title'],
                      "short_description": article['short_description'],
                      "category": article['category'],
                      "url": article['url']
                        })
            except json.JSONDecodeError:
                processed_results.append({
                    "url": urls[i],
                    "error": "Failed to parse JSON content"
                })
            except Exception as e:
                processed_results.append({
                    "url": urls[i],
                    "error": str(e)
                })
        else:
            processed_results.append({
                "url": urls[i],
                "error": result.error_message
            })

    return jsonify(processed_results)

@app.route('/candlestick', methods=['GET'])
def get_candlestick_data():
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1d')
    limit = request.args.get('limit', 500)

    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # processed_data = []
        # for candle in data:
        #     processed_data.append({
        #         "open_time": candle[0],
        #         "open": float(candle[1]),
        #         "high": float(candle[2]),
        #         "low": float(candle[3]),
        #         "close": float(candle[4]),
        #         "volume": float(candle[5]),
        #         "close_time": candle[6],
        #         "quote_asset_volume": float(candle[7]),
        #         "number_of_trades": int(candle[8])
        #     })
        
        return jsonify(data)
    
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch data from Binance: {str(e)}"}), 500

@app.route('/cryptopanic', methods=['GET'])
def get_cryptopanic_data():
    if not auth_token:
        return jsonify({"error": "CRYPTOPANIC_AUTH_TOKEN not set in environment variables"}), 500

    base_url = "https://cryptopanic.com/api/free/v1/posts/"
    
    # Get query parameters
    kind = request.args.get('kind', 'news')
    currencies = request.args.get('currencies')
    filter_param = request.args.get('filter')
    page = request.args.get('page', '1')

    # Construct the API URL
    params = {
        'auth_token': auth_token,
        'kind': kind,
        'page': page
    }
    if currencies:
        params['currencies'] = currencies
    if filter_param:
        params['filter'] = filter_param

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Process and format the results
        formatted_results = []
        for item in data['results']:
            formatted_item = {
                'votes': {
                    'negative': item['votes'].get('negative', 0),
                    'positive': item['votes'].get('positive', 0),
                    'important': item['votes'].get('important', 0)
                },
                'title': item.get('title', ''),
                'published_at': item.get('published_at', '')
            }
            
            # Check if 'currencies' property exists and is not None
            if 'currencies' in item and item['currencies'] is not None:
                formatted_item['currencies'] = [{
                    'code': currency.get('code', ''),
                    'title': currency.get('title', '')
                } for currency in item['currencies']]
            else:
                formatted_item['currencies'] = []

            formatted_results.append(formatted_item)

        return jsonify(formatted_results)

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch data from CryptoPanic: {str(e)}"}), 500
