"""
Script to compile and deploy the BugBounty smart contract.

This script uses web3.py and solcx to compile and deploy the contract to
an Ethereum-compatible network.  Before running it, install the
dependencies:

    pip install web3 py-solc-x

You must also have access to an RPC endpoint (e.g., Ganache, Hardhat node
or Infura) and a funded account to pay deployment gas.  Configure the
`RPC_URL` and private key or use environment variables as shown below.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple

try:
    from web3 import Web3
    import solcx
except ImportError:
    raise SystemExit(
        "web3 and py-solc-x are required for this script. Install them via 'pip install web3 py-solc-x'."
    )

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "smart_contract" / "BugBounty.sol"
RPC_URL = os.environ.get("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.environ.get("DEPLOYER_PRIVATE_KEY")


def compile_contract() -> Tuple[str, str]:
    """Compile the Solidity contract and return bytecode and ABI."""
    source_code = CONTRACT_PATH.read_text()
    solcx.install_solc("0.8.20")
    compiled = solcx.compile_source(
        source_code,
        output_values=["abi", "bin"],
        solc_version="0.8.20",
    )
    contract_id, contract_interface = compiled.popitem()
    abi = contract_interface["abi"]
    bytecode = contract_interface["bin"]
    return abi, bytecode


def deploy_contract() -> str:
    """Deploy the BugBounty contract to the configured network."""
    if not PRIVATE_KEY:
        raise SystemExit("Set DEPLOYER_PRIVATE_KEY environment variable with your account's private key")
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = web3.eth.account.from_key(PRIVATE_KEY)
    abi, bytecode = compile_contract()
    BugBounty = web3.eth.contract(abi=abi, bytecode=bytecode)
    # Build transaction
    nonce = web3.eth.get_transaction_count(account.address)
    tx = BugBounty.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': web3.eth.gas_price,
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Deployment transaction sent: {tx_hash.hex()}")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at address: {receipt.contractAddress}")
    return receipt.contractAddress


if __name__ == "__main__":
    deploy_contract()