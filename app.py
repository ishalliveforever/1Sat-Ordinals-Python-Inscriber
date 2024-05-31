from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import logging

app = Flask(__name__)

# Configuration
GORILLA_POOL_API_URL = 'https://ordinals.gorillapool.io/api/tx/submit'

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def serve_wallet_inscription():
    return send_from_directory('static', 'wallet_inscription.html')

@app.route('/inscribe', methods=['POST'])
def inscribe():
    try:
        data = request.get_json()
        logging.info(f"Received data: {data}")

        base64_data = data['base64Data']
        mime_type = data['mimeType']
        app_name = data['appName']
        data_name = data['dataName']
        destination_address = data['destinationAddress']
        wallet_data = data['walletData']
        bsv_address = wallet_data['bsvAddress']

        logging.info(f"Preparing UTXO from wallet data: {wallet_data['utxo']}")

        # Fetch UTXO from the wallet data
        utxo = wallet_data['utxo']

        # Validate and create the inscription following the ordinals envelope format
        inscription = {
            "base64Data": base64_data,
            "mimeType": mime_type,
            "map": {
                "app": app_name,
                "type": "ord",
                "name": data_name
            }
        }

        logging.info(f"Inscription created: {inscription}")

        # Create the transaction
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
                    "inscription": inscription
                }
            ]
        }

        logging.info(f"Transaction created: {raw_tx}")

        # Sign the transaction using the wallet signature received from the client
        signature = data['sig']
        raw_tx['signature'] = signature

        logging.info(f"Transaction signed with signature: {signature}")

        # Broadcast the transaction to the Gorilla Pool API
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(GORILLA_POOL_API_URL, headers=headers, data=json.dumps(raw_tx))
        response_data = response.json()

        logging.info(f"Gorilla Pool API response: {response_data}")

        if response.status_code == 200 and response_data.get('txid'):
            return jsonify({'success': True, 'txid': response_data['txid']})
        else:
            return jsonify({'success': False, 'error': response_data.get('message', 'Unknown error')})

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error: {str(e)}")
        return jsonify({'success': False, 'error': f"Network error: {str(e)}"})
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(port=5000)
