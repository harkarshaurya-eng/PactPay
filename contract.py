from algopy import ARC4Contract, Account, Txn, arc4, itxn

# 👇 WE RENAMED THIS BACK TO "HelloWorld" TO SATISFY THE SYSTEM
class HelloWorld(ARC4Contract):
    """
    A simple Escrow Contract (Disguised as Hello World).
    """

    # --- MEMORY ---
    buyer: Account
    seller: Account
    arbiter: Account

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, seller: Account, arbiter: Account) -> None:
        self.buyer = Txn.sender
        self.seller = seller
        self.arbiter = arbiter

    @arc4.abimethod
    def release_funds(self) -> None:
        # Check that only the Buyer or Arbiter can do this
        assert Txn.sender == self.buyer or Txn.sender == self.arbiter, "Unauthorized"
        
        # ✅ FORCE FEE: We set fee=1_000 (MicroAlgos) to pay for the transaction
        itxn.Payment(
            receiver=self.seller,
            amount=0,
            close_remainder_to=self.seller,
            fee=1_000 
        ).submit()

    @arc4.abimethod
    def refund_buyer(self) -> None:
        # Check that only the Seller or Arbiter can do this
        assert Txn.sender == self.arbiter or Txn.sender == self.seller, "Unauthorized"
        
        # refund the buyer
        itxn.Payment(
            receiver=self.buyer,
            amount=0,
            close_remainder_to=self.buyer,
            fee=1_000
        ).submit()