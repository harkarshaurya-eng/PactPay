import sys
import os

# --- PATH FIX: This tells Python to look 2 folders up for 'smart_contracts' ---
# Current Location: smart_contracts/hello_world/api.py
# We need to go up to: .../projects/Aglokittest/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, request, jsonify
import algokit_utils
from algokit_utils import AlgorandClient

# Now Python can find this module because we fixed the path above
from smart_contracts.artifacts.hello_world.hello_world_client import (
    HelloWorldFactory, CreateApplicationArgs, HelloWorldMethodCallCreateParams
)

app = Flask(__name__)

# --- 1. SETUP: Connect to LocalNet ---
print("--- 🔄 Initializing Server ---")
algorand = AlgorandClient.default_localnet()
dispenser = algorand.account.localnet_dispenser()

# Create wallets for the demo (In memory)
buyer = algorand.account.random()
seller = algorand.account.random()
arbiter = algorand.account.random()
app_client = None  # We will save the deployed contract here

# Fund the buyer automatically when the server starts
print(f"💰 Funding Buyer Wallet: {buyer.address}...")
algorand.send.payment(
    algokit_utils.PaymentParams(
        sender=dispenser.address,
        receiver=buyer.address,
        amount=algokit_utils.AlgoAmount.from_algo(100),
        signer=dispenser.signer
    )
)
print("✅ Server Ready! Waiting for Flutter App...")

# --- ENDPOINT 1: DEPLOY CONTRACT ---
# Flutter calls this to start the deal
@app.route('/deploy', methods=['POST'])
def deploy_contract():
    global app_client
    print("\n📞 Received request: /deploy")
    try:
        factory = HelloWorldFactory(
            algorand=algorand,
            app_name="EscrowApp",
            default_sender=buyer.address,
            default_signer=buyer.signer,
        )

        deploy_result = factory.deploy(
            create_params=HelloWorldMethodCallCreateParams(
                args=CreateApplicationArgs(seller=seller.address, arbiter=arbiter.address)
            )
        )
        app_client = deploy_result[0]
        
        print(f"✅ Contract Deployed: {app_client.app_id}")
        return jsonify({
            "status": "success",
            "message": "Contract Deployed!",
            "app_id": app_client.app_id,
            "seller_address": seller.address
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT 2: DEPOSIT MONEY ---
# Flutter calls this to send money
@app.route('/deposit', methods=['POST'])
def deposit_money():
    print("\n📞 Received request: /deposit")
    data = request.json
    amount = data.get('amount', 0)
    
    try:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                sender=buyer.address,
                receiver=app_client.app_address,
                amount=algokit_utils.AlgoAmount.from_algo(int(amount)),
                signer=buyer.signer
            )
        )
        print(f"💸 Deposited {amount} ALGO")
        return jsonify({
            "status": "success",
            "message": f"{amount} ALGO locked in escrow.",
            "contract_address": app_client.app_address
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT 3: RELEASE FUNDS ---
# Flutter calls this to finish the deal
@app.route('/release', methods=['POST'])
def release_funds():
    print("\n📞 Received request: /release")
    data = request.json
    decision = data.get('decision', 'no')
    
    if decision == "yes":
        try:
            app_client.send.release_funds(
                send_params=algokit_utils.SendParams(
                    fee=algokit_utils.AlgoAmount.from_micro_algo(2000)
                )
            )
            print("✅ Funds Released!")
            return jsonify({
                "status": "success",
                "message": "Funds released to Seller!",
                "explorer_link": f"https://lora.algokit.io/localnet/account/{seller.address}"
            })
        except Exception as e:
            print(f"❌ Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        print("🛑 Deal Rejected")
        return jsonify({"status": "held", "message": "Funds kept in contract."})

if __name__ == '__main__':
    # Start the server on 0.0.0.0 so your friends can connect
    app.run(host='0.0.0.0', port=5000)