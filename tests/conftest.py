from moccasin.boa_tools import VyperContract
from moccasin.config import Network, get_active_network, Address
import pytest
import boa
from script.network_config import get_deployment_config

from script.deploy import (
    Raffle,
    deploy_raffle,
    RAFFLE_OWNER,
    RAFFLE_FEE_COLLECTOR,
    CHAINLINK_NODE,
    RAFFLE_PLAYER_ONE,
    RAFFLE_PLAYER_TWO,
    RAFFLE_PLAYER_THREE,
    RAFFLE_PLAYER_FOUR,
)

from script.deploy_vrf_coordinator_mock import deploy_vrf_coordinator_mock

# Zero address as string - required by boa's ABI encoder
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# RaffleState flag values (matches Vyper flag RaffleState)
class RaffleState:
    """Enum matching Vyper flag RaffleState."""

    OPEN = 1  # Binary: 0001
    CALCULATING = 2  # Binary: 0010


@pytest.fixture(scope="session")
def deployment_config():
    active_network = get_active_network()
    active_network_config = get_deployment_config(active_network)

    if active_network_config.vrf_coordinator == Address(ZERO_ADDRESS):
        active_network_config.vrf_coordinator = active_network.manifest_named(
            "vrf_coordinator"
        ).address

    return active_network_config


@pytest.fixture(scope="function")
def vrf_coordinator_mock() -> VyperContract:
    with boa.env.prank(RAFFLE_OWNER):
        return deploy_vrf_coordinator_mock()


@pytest.fixture(scope="function")
def raffle_contract(vrf_coordinator_mock) -> VyperContract:
    return deploy_raffle(vrf_coordinator_mock.address)


@pytest.fixture(scope="function")
def raffle_contract_with_players(deployment_config, raffle_contract) -> VyperContract:
    players = [RAFFLE_PLAYER_ONE, RAFFLE_PLAYER_TWO, RAFFLE_PLAYER_THREE]

    for player in players:
        boa.env.set_balance(player, 1 * (10**8))
        with boa.env.prank(player):
            raffle_contract.enter_raffle(value=deployment_config.entrance_fee)

    return raffle_contract


@pytest.fixture(scope="function")
def raffle_contract_with_upkeep(
    deployment_config, raffle_contract_with_players
) -> VyperContract:
    boa.env.time_travel(deployment_config.raffle_interval + 1)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number + deployment_config.raffle_interval + 1
    )

    raffle_contract_with_players.perform_upkeep()
    return raffle_contract_with_players


@pytest.fixture(scope="function")
def raffle_contract_with_winner(
    deployment_config, vrf_coordinator_mock, raffle_contract_with_upkeep
) -> VyperContract:
    request_id = 1

    # Setting block number in a way that player three will be the winner (based on blockhash and request ID)
    boa.env.evm.patch.block_number = 13
    boa.env.time_travel(raffle_contract_with_upkeep.get_s_interval() + 100)

    vrf_coordinator_mock.trigger_fullfil_random_words(request_id, sender=RAFFLE_OWNER)

    return raffle_contract_with_upkeep
