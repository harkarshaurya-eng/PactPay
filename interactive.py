import algokit_utils
from algokit_utils import AlgorandClient
from smart_contracts.artifacts.hello_world.hello_world_client import (
    HelloWorldFactory, 
    CreateApplicationArgs, 
    HelloWorldMethodCallCreateParams
)

# --- 1. SETUP & LOGIN ---
print("\n--- 🏦 WELCOME TO THE HACKATHON ESCROW CLI ---")
print("Initializing LocalNet connection...")

# Connect to your local blockchain
algorand = AlgorandClient.default_localnet()
dispenser = algorand.account.localnet_dispenser()

# Create wallets for the demo
buyer = algorand.account.random()
seller = algorand.account.random()
arbiter = algorand.account.random()

# Give the Buyer some fake money to start
print(f"💰 Funding Buyer Wallet: {buyer.address}...")
algorand.send.payment(
    algokit_utils.PaymentParams(
        sender=dispenser.address,
        receiver=buyer.address,
        amount=algokit_utils.AlgoAmount.from_algo(100),
        signer=dispenser.signer
    )
)
print("✅ Buyer is funded with 100 ALGO.")
print("-" * 60)

# --- 2. INPUT: START THE DEAL ---
print("👨‍💻 SELLER: 'I am ready to start the project.'")
start_input = input("👉 Press Enter to DEPLOY the Escrow Contract... ")

print("\n🚀 Deploying Contract...")
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
app_id = app_client.app_id
print(f"✅ Contract Deployed! App ID: {app_id}")
print(f"🌍 View on Explorer: https://lora.algokit.io/localnet/application/{app_id}")
print("-" * 60)

# --- 3. INPUT: DEPOSIT MONEY ---
print(f"💳 BUYER: You need to lock funds for the Seller.")
while True:
    try:
        amount_str = input("👉 Enter amount to deposit (e.g. 10): ")
        deposit_amount = int(amount_str)
        break
    except ValueError:
        print("❌ Please enter a valid number.")

print(f"\n💸 Sending {deposit_amount} ALGO to the Escrow Box...")
algorand.send.payment(
    algokit_utils.PaymentParams(
        sender=buyer.address,
        receiver=app_client.app_address,
        amount=algokit_utils.AlgoAmount.from_algo(deposit_amount),
        signer=buyer.signer
    )
)
print(f"🔒 FUNDS LOCKED. The Seller can see the money but cannot touch it.")
print("-" * 60)

# --- 4. INPUT: THE FINAL DECISION ---
print("\n⏳ ... FAST FORWARD 1 WEEK ... ⏳")
print("📩 The Developer (Seller) has emailed you the project code.")
print("🤔 You are reviewing the work now...")

decision = input("👉 Did they do a good job? Type 'yes' to pay, 'no' to refund: ")

if decision.lower() == "yes":
    print("\n👍 APPROVED! Releasing funds to Seller...")
    
    try:
        # THIS IS THE "APPROVE" BUTTON CLICK
        app_client.send.release_funds(
            send_params=algokit_utils.SendParams(
                fee=algokit_utils.AlgoAmount.from_micro_algo(2000)
            )
        )
        print(f"✅ SUCCESS! {deposit_amount} ALGO sent to {seller.address}")
        print(f"🎉 Proof: https://lora.algokit.io/localnet/account/{seller.address}")
    except Exception as e:
        print(f"❌ Error releasing funds: {e}")

else:
    print("\n🛑 REJECTED! You are unhappy with the work.")
    print("📞 Calling the Arbiter to resolve the dispute...")
    # In a real app, this would trigger the 'refund_buyer' function by the Arbiter
    print(f"(Arbiter {arbiter.address} has been notified)")

print("\n--- DEMO COMPLETE ---")