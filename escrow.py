from pyteal import *

def escrow_contract():
    # Global state keys
    client_key = Bytes("client")
    freelancer_key = Bytes("freelancer")
    amount_key = Bytes("amount")
    platform_fee_key = Bytes("platform_fee")
    deadline_key = Bytes("deadline")
    auto_release_key = Bytes("auto_release")
    status_key = Bytes("status")
    platform_addr_key = Bytes("platform")
    deal_id_key = Bytes("deal_id")
    
    # Status values
    STATUS_PENDING = Bytes("pending")
    STATUS_FUNDED = Bytes("funded")
    STATUS_RELEASED = Bytes("released")
    STATUS_DISPUTED = Bytes("disputed")
    STATUS_REFUNDED = Bytes("refunded")
    
    # Initialize contract
    @Subroutine(TealType.none)
    def initialize():
        return Seq([
            App.globalPut(deal_id_key, Txn.application_args[0]),
            App.globalPut(client_key, Txn.application_args[1]),
            App.globalPut(freelancer_key, Txn.application_args[2]),
            App.globalPut(amount_key, Btoi(Txn.application_args[3])),
            App.globalPut(deadline_key, Btoi(Txn.application_args[4])),
            App.globalPut(platform_fee_key, Btoi(Txn.application_args[5])),
            App.globalPut(platform_addr_key, Txn.application_args[6]),
            App.globalPut(status_key, STATUS_PENDING),
            Approve()
        ])
    
    # Fund escrow
    @Subroutine(TealType.none)
    def fund_escrow():
        total_amount = App.globalGet(amount_key) + App.globalGet(platform_fee_key)
        
        # Calculate auto-release time: deadline + 72 hours (in seconds)
        # using Python int for 72 hours = 72 * 60 * 60 = 259200
        auto_release_time = App.globalGet(deadline_key) + Int(259200)
        
        return Seq([
            # Verify sender is client
            Assert(Txn.sender() == App.globalGet(client_key)),
            
            # Verify status is pending
            Assert(App.globalGet(status_key) == STATUS_PENDING),
            
            # Verify payment amount (Gtxn[1] is the payment transaction)
            Assert(Gtxn[1].amount() == total_amount),
            Assert(Gtxn[1].receiver() == Global.current_application_address()),
            
            # Update state
            App.globalPut(status_key, STATUS_FUNDED),
            App.globalPut(auto_release_key, auto_release_time),
            
            Approve()
        ])
    
    # Approve and release payment
    @Subroutine(TealType.none)
    def approve_release():
        freelancer_amount = App.globalGet(amount_key)
        platform_fee = App.globalGet(platform_fee_key)
        
        return Seq([
            # Verify sender is client
            Assert(Txn.sender() == App.globalGet(client_key)),
            
            # Verify status is funded
            Assert(App.globalGet(status_key) == STATUS_FUNDED),
            
            # Transfer to freelancer
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(freelancer_key),
                TxnField.amount: freelancer_amount,
            }),
            InnerTxnBuilder.Submit(),
            
            # Transfer platform fee
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(platform_addr_key),
                TxnField.amount: platform_fee,
            }),
            InnerTxnBuilder.Submit(),
            
            # Update status
            App.globalPut(status_key, STATUS_RELEASED),
            
            Approve()
        ])
    
    # Auto-release if deadline passed
    @Subroutine(TealType.none)
    def auto_release():
        current_time = Global.latest_timestamp()
        freelancer_amount = App.globalGet(amount_key)
        platform_fee = App.globalGet(platform_fee_key)
        
        return Seq([
            # Verify auto-release time has passed
            Assert(current_time >= App.globalGet(auto_release_key)),
            
            # Verify status is funded
            Assert(App.globalGet(status_key) == STATUS_FUNDED),
            
            # Transfer to freelancer
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(freelancer_key),
                TxnField.amount: freelancer_amount,
            }),
            InnerTxnBuilder.Submit(),
            
            # Transfer platform fee
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(platform_addr_key),
                TxnField.amount: platform_fee,
            }),
            InnerTxnBuilder.Submit(),
            
            # Update status
            App.globalPut(status_key, STATUS_RELEASED),
            
            Approve()
        ])
    
    # Raise dispute
    @Subroutine(TealType.none)
    def raise_dispute():
        return Seq([
            # Verify sender is client or freelancer
            Assert(Or(
                Txn.sender() == App.globalGet(client_key),
                Txn.sender() == App.globalGet(freelancer_key)
            )),
            
            # Verify status is funded or released (could dispute after release? usually not in this model)
            # Assuming dispute only during funded state
            Assert(App.globalGet(status_key) == STATUS_FUNDED),
            
            # Update status to disputed
            App.globalPut(status_key, STATUS_DISPUTED),
            
            Approve()
        ])
    
    # Resolve dispute (admin only)
    @Subroutine(TealType.none)
    def resolve_dispute():
        # Args: [method, client_amount, freelancer_amount]
        client_amount = Btoi(Txn.application_args[1])
        freelancer_amount = Btoi(Txn.application_args[2])
        platform_fee = App.globalGet(platform_fee_key)
        
        return Seq([
            # Verify sender is platform admin
            Assert(Txn.sender() == App.globalGet(platform_addr_key)),
            
            # Verify status is disputed
            Assert(App.globalGet(status_key) == STATUS_DISPUTED),
            
            # Verify amounts add up correctly (total blocked - fee)
            Assert(client_amount + freelancer_amount == App.globalGet(amount_key)),
            
            # Transfer to client if any
            If(client_amount > Int(0),
                Seq([
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields({
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.receiver: App.globalGet(client_key),
                        TxnField.amount: client_amount,
                    }),
                    InnerTxnBuilder.Submit(),
                ])
            ),
            
            # Transfer to freelancer if any
            If(freelancer_amount > Int(0),
                Seq([
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields({
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.receiver: App.globalGet(freelancer_key),
                        TxnField.amount: freelancer_amount,
                    }),
                    InnerTxnBuilder.Submit(),
                ])
            ),
            
            # Transfer platform fee
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(platform_addr_key),
                TxnField.amount: platform_fee,
            }),
            InnerTxnBuilder.Submit(),
            
            # Update status
            App.globalPut(status_key, STATUS_RELEASED), # Or STATUS_RESOLVED
            
            Approve()
        ])
    
    # Refund (before funding or by admin)
    @Subroutine(TealType.none)
    def refund():
        total_amount = App.globalGet(amount_key) + App.globalGet(platform_fee_key)
        
        return Seq([
            # Verify sender is client or platform admin
            Assert(Or(
                Txn.sender() == App.globalGet(client_key),
                Txn.sender() == App.globalGet(platform_addr_key)
            )),
            
            # Verify status allows refund (pending or funded)
            Assert(Or(
                App.globalGet(status_key) == STATUS_PENDING,
                App.globalGet(status_key) == STATUS_FUNDED
            )),
            
            # Transfer full amount back to client (only if funded)
            If(App.globalGet(status_key) == STATUS_FUNDED,
                Seq([
                     InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields({
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.receiver: App.globalGet(client_key),
                        TxnField.amount: total_amount,
                    }),
                    InnerTxnBuilder.Submit(),
                ])
            ),
            
            # Update status
            App.globalPut(status_key, STATUS_REFUNDED),
            
            Approve()
        ])
    
    # Main program routing
    program = Cond(
        [Txn.application_id() == Int(0), initialize()],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))], # Disallow delete
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))], # Disallow update
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(0))],
        [Txn.on_completion() == OnComplete.NoOp, Cond(
            [Txn.application_args[0] == Bytes("fund"), fund_escrow()],
            [Txn.application_args[0] == Bytes("approve"), approve_release()],
            [Txn.application_args[0] == Bytes("auto_release"), auto_release()],
            [Txn.application_args[0] == Bytes("dispute"), raise_dispute()],
            [Txn.application_args[0] == Bytes("resolve"), resolve_dispute()],
            [Txn.application_args[0] == Bytes("refund"), refund()],
        )]
    )
    
    return program

if __name__ == "__main__":
    with open("escrow.teal", "w") as f:
        compiled = compileTeal(escrow_contract(), Mode.Application, version=8)
        f.write(compiled)
