from flask import Flask, request, jsonify
app = Flask(__name__)

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    print(f'AFTER_REQUEST: origin={origin}, method={request.method}')
    response.headers['Access-Control-Allow-Origin'] = origin or '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return response

@app.route('/test', methods=['GET','POST','OPTIONS'])
def test():
    return jsonify({'ok': True})

with app.test_client() as c:
    r = c.options('/test', headers={'Origin': 'http://localhost:3001'})
    print(f'Status: {r.status_code}')
    acao = r.headers.get('Access-Control-Allow-Origin', 'MISSING')
    print(f'ACAO: {acao}')
