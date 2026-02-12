from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future import transaction
from escrow import escrow_contract
from pyteal import compileTeal, Mode
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Algorand node
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

def deploy_escrow_contract(
    creator_private_key,
    deal_id,
    client_address,
    freelancer_address,
    amount,
    deadline,
    platform_fee,
    platform_address
):
    # Compile contract
    approval_source = compileTeal(escrow_contract(), Mode.Application, version=8)
    clear_source = "#pragma version 8\nint 1" # Simple clear program
    
    approval_program = compile_program(algod_client, approval_source)
    clear_program = compile_program(algod_client, clear_source)
    
    # Get creator address
    creator_address = account.address_from_private_key(creator_private_key)
    
    # Get network params
    params = algod_client.suggested_params()
    
    # Create application
    txn = transaction.ApplicationCreateTxn(
        sender=creator_address,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=transaction.StateSchema(num_uints=5, num_byte_slices=6),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        app_args=[
            deal_id.encode(),
            client_address.encode(),
            freelancer_address.encode(),
            amount.to_bytes(8, 'big'),
            deadline.to_bytes(8, 'big'),
            platform_fee.to_bytes(8, 'big'),
            platform_address.encode()
        ]
    )
    
    # Sign and send
    signed_txn = txn.sign(creator_private_key)
    tx_id = algod_client.send_transaction(signed_txn)
    print(f"Transaction ID: {tx_id}")
    
    # Wait for confirmation
    confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
    app_id = confirmed_txn["application-index"]
    print(f"Deployed App ID: {app_id}")
    
    return app_id

if __name__ == "__main__":
    # Example usage (replace with real keys for testing)
    # deploy_escrow_contract(...)
    pass
