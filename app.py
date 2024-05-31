from flask import Flask, request, jsonify, send_from_directory
import requests
import json

app = Flask(__name__)

# Configuration
GORILLA_POOL_API_URL = 'https://ordinals.gorillapool.io/api/tx/submit'

@app.route('/')
def serve_wallet_inscription():
    """
    Serve the wallet inscription HTML page.
    """
    return send_from_directory('static', 'wallet_inscription.html')

@app.route('/inscribe', methods=['POST'])
def inscribe():
    """
    Endpoint to handle the inscription request.
    """
    try:
        data = request.get_json()
        print("Received data:", data)

        base64_data = data['base64Data']
        mime_type = data['mimeType']
        app_name = data['appName']
        data_name = data['dataName']
        destination_address = data['destinationAddress']
        wallet_data = data['walletData']
        bsv_address = wallet_data['bsvAddress']

        # Fetch UTXO from the wallet data
        utxo = wallet_data['utxo']
        print("Selected UTXO:", utxo)

        # Create the ord envelope script following the correct format
        ord_envelope_script = [
            'OP_FALSE', 'OP_IF', '6f7264',  # ord
            'PUSH_DATA', 'mimeType', mime_type,
            'PUSH_DATA', 'app', app_name,
            'PUSH_DATA', 'type', 'ord',
            'PUSH_DATA', 'name', data_name,
            'OP_0', base64_data,
            'OP_ENDIF'
        ]
        print("Ord envelope script:", ord_envelope_script)

        # Create the raw transaction with the ord envelope script
        raw_tx = {
            "inputs": [
                {
                    "txid": utxo['txid'],
                    "vout": utxo['vout'],
                    "satoshis": utxo['satoshis'],
                    "script": utxo['script']
                }
            ],
            "outputs": [
                {
                    "satoshis": 1,
                    "address": destination_address,
                    "script": ord_envelope_script
                }
            ]
        }
        print("Raw transaction:", raw_tx)

        # Sign the transaction using the wallet signature received from the client
        signature = data['sig']
        raw_tx['signature'] = signature
        print("Signed transaction:", raw_tx)

        # Broadcast the transaction to the Gorilla Pool API
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(GORILLA_POOL_API_URL, headers=headers, data=json.dumps(raw_tx))
        print("Gorilla Pool response status:", response.status_code)
        response_data = response.json()
        print("Gorilla Pool response data:", response_data)

        if response.status_code == 200 and response_data.get('txid'):
            return jsonify({'success': True, 'txid': response_data['txid']})
        else:
            return jsonify({'success': False, 'error': response_data.get('message', 'Unknown error')})

    except requests.exceptions.RequestException as e:
        print("Network error:", str(e))
        return jsonify({'success': False, 'error': f"Network error: {str(e)}"})
    except Exception as e:
        print("General error:", str(e))
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(port=5000)
