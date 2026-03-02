import os
from functools import wraps

import yfinance as yf
from flask import Flask, jsonify, request, send_from_directory
from supabase import create_client

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL         = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY    = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

_supa = None


def _get_supa():  
    global _supa  
    if _supa is None:  
        try:  
            _supa = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  
        except Exception as e:  
            print(f"Warning: Supabase initialization failed: {e}")  
            _supa = None  
    return _supa  


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            user = _get_supa().auth.get_user(token)
            request.user_id = user.user.id
        except Exception:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/api/config')
def api_config():
    """前端初始化 Supabase 用的公開設定（anon key 可公開）"""
    return jsonify({
        'supabase_url':      SUPABASE_URL,
        'supabase_anon_key': SUPABASE_ANON_KEY,
    })


@app.route('/api/state', methods=['GET'])
@require_auth
def get_state():
    row = (
        _get_supa()
        .table('user_data')
        .select('sectors,notes')
        .eq('user_id', request.user_id)
        .maybe_single()
        .execute()
    )
    if row.data:
        return jsonify(row.data)
    return jsonify({'sectors': [], 'notes': {}})


@app.route('/api/state', methods=['POST'])
@require_auth
def save_state():
    data = request.get_json()
    _get_supa().table('user_data').upsert(
        {
            'user_id': request.user_id,
            'sectors': data.get('sectors', []),
            'notes':   data.get('notes', {}),
        },
        on_conflict='user_id',
    ).execute()
    return '', 204


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
