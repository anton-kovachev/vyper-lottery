import pytest
from moccasin.config import get_active_network
from moccasin.boa_tools import VyperContract
from script.deploy import deploy_raffle
from moccasin.moccasin_account import MoccasinAccount
import boa


@pytest.mark.staging
@pytest.mark.ignore_isolation
def test_raffle_owner_enters_raffle_should_fail_live():
    active_network = get_active_network()
    account = active_network.get_default_account().address
    vrf_coordinator_contract: VyperContract = active_network.manifest_named(
        "vrf_coordinator"
    )

    raffle_contract: VyperContract = deploy_raffle(vrf_coordinator_contract.address)
    entrance_fee = raffle_contract.get_i_entrance_fee()

    with boa.reverts("Raffle__Owner_Cannot_Participate"):
        raffle_contract.enter_raffle(value=entrance_fee, sender=account)


@pytest.mark.staging
@pytest.mark.ignore_isolation
def test_raffle_player_enters_raffle_success_live():
    active_network = get_active_network()

    # Get second account from keychain (different from deployer)
    # Make sure you have a second account named "player1" in your keychain
    # Or replace with your second account name
    player_account = MoccasinAccount(
        keystore_path_or_account_name="player1",
        password_file_path=active_network.unsafe_password_file,
    )

    vrf_coordinator_contract: VyperContract = active_network.manifest_named(
        "vrf_coordinator"
    )

    # Deploys with default account (index 0)
    raffle_contract: VyperContract = deploy_raffle(vrf_coordinator_contract.address)
    entrance_fee = raffle_contract.get_i_entrance_fee()

    if hasattr(boa.env, "_accounts"):
        boa.env._accounts[player_account.address] = player_account
    else:
        raise Exception(
            "Boa environment does not support accounts dictionary for testing"
        )
    # Player enters with different account
    with boa.env.prank(player_account.address):
        raffle_contract.enter_raffle(value=entrance_fee)
    assert raffle_contract.get_s_player_has_entered(player_account.address) == True
