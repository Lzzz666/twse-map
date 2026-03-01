import os
import yfinance as yf
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/api/quote')
def quote():
    """批次取得價格與漲跌幅（快速，不含名稱）
    GET /api/quote?symbols=NVDA,6758.T,005930.KS
    回傳 { "NVDA": { "price": 177.19, "change": -4.16 }, ... }
    """
    raw = request.args.get('symbols', '')
    symbols = [s.strip().upper() for s in raw.split(',') if s.strip()]
    if not symbols:
        return jsonify({}), 400

    result = {}
    for symbol in symbols:
        try:
            fi = yf.Ticker(symbol).fast_info
            price = fi.last_price
            prev  = fi.previous_close
            result[symbol] = {
                'price':  round(float(price), 4) if price else None,
                'change': round((price - prev) / prev * 100, 4) if price and prev else None,
            }
        except Exception:
            result[symbol] = {'price': None, 'change': None}

    return jsonify(result)


@app.route('/api/search')
def search():
    """單一代號查詢（含名稱，用於新增時驗證）
    GET /api/search?symbol=NVDA
    回傳 { "symbol": "NVDA", "name": "NVIDIA Corporation", "price": 177.19, "change": -4.16 }
    """
    symbol = request.args.get('symbol', '').strip().upper()
    if not symbol:
        return jsonify({'error': 'symbol required'}), 400

    try:
        t     = yf.Ticker(symbol)
        fi    = t.fast_info
        price = fi.last_price
        prev  = fi.previous_close

        if not price:
            return jsonify({'error': f'找不到代號 {symbol}'}), 404

        info = t.info
        name = info.get('shortName') or info.get('longName') or symbol

        return jsonify({
            'symbol': symbol,
            'name':   name,
            'price':  round(float(price), 4),
            'change': round((price - prev) / prev * 100, 4) if prev else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404


if __name__ == '__main__':
    print('啟動中  →  http://localhost:3001')
    app.run(host='127.0.0.1', port=3001, debug=False)
