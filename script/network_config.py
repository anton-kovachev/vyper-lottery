"""
Network configuration for Raffle deployment.
Centralizes all network-specific settings.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from moccasin.config import Network, Address

# Zero address constant
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@dataclass
class DeploymentConfig:
    """Configuration for deploying Raffle on a specific network."""

    vrf_coordinator: Address
    subscription_id: int
    key_hash: bytes
    entrance_fee: int
    raffle_interval: int
    use_network_account: bool
    verify_contract: bool
    fee_collector: Address

    @classmethod
    def from_network(
        cls, network: Network, defaults: Dict[str, Any]
    ) -> "DeploymentConfig":
        """
        Create config from network, with fallback to defaults.
        Reads from network.extra_data if available.
        """
        extra_data = network.extra_data or {}

        return cls(
            vrf_coordinator=Address(ZERO_ADDRESS),
            subscription_id=int(
                extra_data.get("subscription_id", defaults["subscription_id"])
            ),
            key_hash=bytes.fromhex(
                extra_data.get("key_hash", defaults["key_hash"]).removeprefix("0x")
            ),
            entrance_fee=int(extra_data.get("entrance_fee", defaults["entrance_fee"])),
            raffle_interval=int(
                extra_data.get("raffle_interval", defaults["raffle_interval"])
            ),
            use_network_account=not network.is_local_or_forked_network(),
            verify_contract=not network.is_local_or_forked_network()
            and network.has_explorer(),
            fee_collector=extra_data.get("raffle_fee_collector"),
        )


# Chain-specific overrides (for values that can't go in TOML)
CHAIN_SPECIFIC_CONFIG: Dict[int, Dict[str, Any]] = {
    # Sepolia
    11155111: {
        "subscription_id": 98318959468081398324484698785631282469515943806038881563842469977866837146565,
    },
    # Mainnet
    1: {
        "subscription_id": 123456789,
        "entrance_fee": 5 * (10**8),  # Higher fee on mainnet
        "raffle_interval": 86400,  # 1 day
        "fee_collector": "0xD13F0BD22AFF8176761AEFBFC052A7490BDE268E",
    },
}


def get_deployment_config(network: Network) -> DeploymentConfig:
    """
    Get deployment configuration for the active network.

    Priority:
    1. Network extra_data from moccasin.toml
    2. Chain-specific config from CHAIN_SPECIFIC_CONFIG
    3. Default values
    """
    # Default values
    defaults = {
        "subscription_id": 1,
        "key_hash": "0x9e1344a1247c8a1785d0a4681a27152bffdb43666ae5bf7d14d24a5efd44bf71",
        "entrance_fee": 1 * (10**8),
        "raffle_interval": 60,
        "fee_collector": ZERO_ADDRESS,
    }

    # Merge with chain-specific overrides
    chain_config = CHAIN_SPECIFIC_CONFIG.get(network.chain_id, {})
    defaults.update(chain_config)

    # Create config with network data taking precedence
    return DeploymentConfig.from_network(network, defaults)


# Network name mapping for logging
NETWORK_NAMES = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    31337: "Local Anvil",
    300: "zkSync Sepolia",
}


def get_network_name(network: Network) -> str:
    """Get human-readable network name."""
    return NETWORK_NAMES.get(network.chain_id, f"Unknown Network ({network.chain_id})")
