import algokit_utils
from algokit_utils import AlgorandClient
from smart_contracts.artifacts.hello_world.hello_world_client import (
    HelloWorldFactory, 
    CreateApplicationArgs, 
    HelloWorldMethodCallCreateParams
)

# --- 1. SETUP: Connect to LOCALNET (Your Private Blockchain) ---
# This looks for the server running on your laptop (localhost)
algorand = AlgorandClient.default_localnet()

# --- 2. GET FREE MONEY (Infinite Glitch) ---
# In LocalNet, we use 'localnet_dispenser()' to get the rich account.
dispenser = algorand.account.localnet_dispenser()

# Create a random account for you (The Buyer)
buyer = algorand.account.random()

# Transfer 100 ALGO from Dispenser -> Buyer
print(f"💸 Dispensing 100 fake ALGO to {buyer.address}...")
algorand.send.payment(
    algokit_utils.PaymentParams(
        sender=dispenser.address,
        receiver=buyer.address,
        amount=algokit_utils.AlgoAmount.from_algo(100),
        signer=dispenser.signer
    )
)
print(f"😎 Buyer is rich! Address: {buyer.address}")

# Setup Fake Friends
seller = algorand.account.random()
arbiter = algorand.account.random()

# --- 3. DEPLOY THE CONTRACT ---
print("\n🚀 Deploying Escrow Contract to LocalNet...")

factory = HelloWorldFactory(
    algorand=algorand,
    app_name="EscrowApp",
    default_sender=buyer.address,
    default_signer=buyer.signer, # LocalNet accounts come with signers attached!
)

try:
    args = CreateApplicationArgs(seller=seller.address, arbiter=arbiter.address)
    
    deploy_result = factory.deploy(
        create_params=HelloWorldMethodCallCreateParams(args=args)
    )
    
    app_client = deploy_result[0]
    app_id = app_client.app_id
    print(f"✅ Contract Active! App ID: {app_id}")
    
    # LINK TO LOCAL EXPLORER (Show this to judges!)
    print(f"🌍 See it live: https://lora.algokit.io/localnet/application/{app_id}")

except Exception as e:
    print(f"❌ Deploy Failed: {e}")
    exit()

# --- 4. FUND THE CONTRACT ---
print("\n💰 Buyer depositing 1 ALGO into Escrow...")

try:
    algorand.send.payment(
        algokit_utils.PaymentParams(
            sender=buyer.address,
            receiver=app_client.app_address,
            amount=algokit_utils.AlgoAmount.from_algo(1),
            signer=buyer.signer
        )
    )
    print(f"✅ Money is in the box: {app_client.app_address}")
except Exception as e:
    print(f"⚠️ Deposit failed: {e}")

# --- 5. RELEASE FUNDS ---
print("\n🔓 Releasing funds to Seller...")
try:
    app_client.send.release_funds(
        send_params=algokit_utils.SendParams(
            fee=algokit_utils.AlgoAmount.from_micro_algo(2000)
        )
    )
    print("✅ SUCCESS! Money moved to Seller.")
    print(f"🎉 Proof: https://lora.algokit.io/localnet/account/{seller.address}")

except Exception as e:
    print(f"❌ Failed to release: {e}")