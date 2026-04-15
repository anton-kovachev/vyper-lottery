from src import Raffle
from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network, Network
from boa.util.abi import Address
import boa

from script.network_config import (
    get_deployment_config,
    get_network_name,
    DeploymentConfig,
)

# Test accounts (only used for local networks)
RAFFLE_OWNER = boa.env.generate_address("raffle_owner")
RAFFLE_FEE_COLLECTOR = boa.env.generate_address("raffle_fee_collector")
CHAINLINK_NODE = boa.env.generate_address("chainlink_node")

RAFFLE_PLAYER_ONE = boa.env.generate_address("player_one")
RAFFLE_PLAYER_TWO = boa.env.generate_address("player_two")
RAFFLE_PLAYER_THREE = boa.env.generate_address("player_three")
RAFFLE_PLAYER_FOUR = boa.env.generate_address("player_four")


def deploy_raffle(vrf_coordinator: Address) -> VyperContract:
    """
    Deploy Raffle contract with network-specific configuration.

    Configuration is loaded from:
    1. moccasin.toml [networks.<name>.extra_data]
    2. script/network_config.py CHAIN_SPECIFIC_CONFIG
    3. Default values
    """
    global RAFFLE_VRF_COORDINATOR
    active_network: Network = get_active_network()

    # Get network-specific configuration
    config: DeploymentConfig = get_deployment_config(active_network)

    # Log deployment info
    network_name = get_network_name(active_network)
    print(f"\n{'='*60}")
    print(f"Deploying Raffle to {network_name}")
    print(f"Chain ID: {active_network.chain_id}")
    print(f"Subscription ID: {config.subscription_id}")
    print(f"Entrance Fee: {config.entrance_fee}")
    print(f"Raffle Interval: {config.raffle_interval}s")
    print(f"{'='*60}\n")

    # Determine deployer and fee collector based on network
    if config.use_network_account:
        deployer_account = active_network.get_default_account().address
        fee_collector = config.fee_collector or deployer_account
        print(f"Using network account: {deployer_account}")
    else:
        deployer_account = RAFFLE_OWNER
        fee_collector = RAFFLE_FEE_COLLECTOR
        print(f"Using test account: {deployer_account}")

    # Deploy contract
    with boa.env.prank(deployer_account):
        raffle_contract: VyperContract = Raffle.deploy(
            fee_collector,
            config.entrance_fee,
            config.raffle_interval,
            vrf_coordinator,
            config.subscription_id,
            config.key_hash,
        )

        print(f"\n✅ Raffle deployed at: {raffle_contract.address}")

    # Verify contract if configured
    if config.verify_contract:
        print("\n🔍 Verifying contract on block explorer...")
        result = active_network.moccasin_verify(raffle_contract)
        result.wait_for_verification()
        print("✅ Contract verified!")

    return raffle_contract


def moccasin_main() -> VyperContract:
    """Main deployment function called by `mox run deploy`."""
    active_network: Network = get_active_network()
    network_name = get_network_name(active_network)

    print(f"\n{'='*60}")
    print(f"Starting deployment on {network_name}")
    print(f"{'='*60}\n")

    # Get VRF Coordinator from manifest
    vrf_coordinator: VyperContract = active_network.manifest_named("vrf_coordinator")
    print(f"Using VRF Coordinator at: {vrf_coordinator.address}")

    # Deploy raffle
    raffle = deploy_raffle(vrf_coordinator.address)

    print(f"\n{'='*60}")
    print("Deployment Complete!")
    print(f"Raffle Address: {raffle.address}")
    print(f"Network: {network_name}")
    print(f"{'='*60}\n")

    return raffle
