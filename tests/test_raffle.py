import boa
import pytest
from moccasin.boa_tools import VyperContract

from conftest import (
    Raffle,
    RAFFLE_OWNER,
    RAFFLE_FEE_COLLECTOR,
    RAFFLE_PLAYER_ONE,
    RAFFLE_PLAYER_TWO,
    RAFFLE_PLAYER_THREE,
    RAFFLE_PLAYER_FOUR,
    ZERO_ADDRESS,
    RaffleState,
)


def test_deploy_raffle_success(deployment_config):

    raffle_contract: VyperContract = Raffle.deploy(
        RAFFLE_FEE_COLLECTOR,
        deployment_config.entrance_fee,
        deployment_config.raffle_interval,
        deployment_config.vrf_coordinator,
        deployment_config.subscription_id,
        deployment_config.key_hash,
        sender=RAFFLE_OWNER,
    )

    assert RAFFLE_OWNER == raffle_contract.get_i_owner()
    assert RAFFLE_FEE_COLLECTOR == raffle_contract.get_i_fee_collector()
    assert deployment_config.vrf_coordinator == raffle_contract.get_i_vrf_coordinator()


def test_deploy_raffle_with_zero_address_for_fee_collector_should_fail(
    deployment_config,
):
    with boa.reverts("Raffle_Invalid_Fee_Collector"):
        raffle_contract: VyperContract = Raffle.deploy(
            ZERO_ADDRESS,
            deployment_config.entrance_fee,
            deployment_config.raffle_interval,
            deployment_config.vrf_coordinator,
            deployment_config.subscription_id,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_deploy_raffle_with_owner_address_for_fee_collector_should_fail(
    deployment_config,
):
    with boa.reverts("Raffle_Fee_Collector_Should_Be_Different_From_Owner"):
        raffle_contract: VyperContract = Raffle.deploy(
            RAFFLE_OWNER,
            deployment_config.entrance_fee,
            deployment_config.raffle_interval,
            deployment_config.vrf_coordinator,
            deployment_config.subscription_id,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_deploy_raffle_with_zero_address_for_vrf_coordinator_should_fail(
    deployment_config,
):
    with boa.reverts("Raffle_Invalid_VRF_Coordinator"):
        raffle_contract: VyperContract = Raffle.deploy(
            RAFFLE_FEE_COLLECTOR,
            deployment_config.entrance_fee,
            deployment_config.raffle_interval,
            ZERO_ADDRESS,
            deployment_config.subscription_id,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_deploy_raffle_with_zero_for_entrance_fee_should_fail(deployment_config):
    with boa.reverts("Raffle_Invalid_Entrance_Fee"):
        raffle_contract: VyperContract = Raffle.deploy(
            RAFFLE_FEE_COLLECTOR,
            0,
            deployment_config.raffle_interval,
            ZERO_ADDRESS,
            deployment_config.subscription_id,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_deploy_raffle_with_shorter_than_the_minimum_time_interval_should_fail(
    deployment_config,
):
    with boa.reverts("Raffle__Invalid_Interval"):
        raffle_contract: VyperContract = Raffle.deploy(
            RAFFLE_FEE_COLLECTOR,
            deployment_config.entrance_fee,
            59,
            deployment_config.vrf_coordinator,
            deployment_config.subscription_id,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_deploy_raffle_zro_value_for_subscription_id_should_fail(deployment_config):
    with boa.reverts("Raffle_Invalid_Subscription_ID"):
        raffle_contract: VyperContract = Raffle.deploy(
            RAFFLE_FEE_COLLECTOR,
            deployment_config.entrance_fee,
            deployment_config.raffle_interval,
            deployment_config.vrf_coordinator,
            0,
            deployment_config.key_hash,
            sender=RAFFLE_OWNER,
        )


def test_owner(raffle_contract):
    assert RAFFLE_OWNER == raffle_contract.get_i_owner()


def test_set_raffle_interval_success(raffle_contract):
    new_interval = 120
    raffle_contract.set_raffle_interval(new_interval, sender=RAFFLE_OWNER)
    assert new_interval == raffle_contract.get_s_interval()


def test_enter_raffle_emit_enter_event_success(deployment_config, raffle_contract):
    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee)
    raffle_contract.enter_raffle(
        sender=RAFFLE_PLAYER_ONE, value=deployment_config.entrance_fee
    )
    event = raffle_contract.get_logs()[0]

    # assert event.event_type.name == "RaffleEntered"
    assert (
        RAFFLE_PLAYER_ONE,
        boa.env.evm.patch.timestamp,
        deployment_config.entrance_fee,
    ) == (
        event.player,
        event.timestamp,
        event.entrance_fee,
    )


def test_set_raffle_interval_not_owner_should_fail(raffle_contract):
    new_interval = 120
    with boa.reverts("Raffle__NotOwner"):
        raffle_contract.set_raffle_interval(new_interval, sender=RAFFLE_PLAYER_ONE)


def test_set_raffle_interval_shorter_than_minimum_interval_should_fail(raffle_contract):
    new_interval = 59
    with boa.reverts("Raffle__InvalidInterval"):
        raffle_contract.set_raffle_interval(new_interval, sender=RAFFLE_OWNER)


def test_enter_raffle_with_sending_more_eth_than_balance_should_fail(
    deployment_config, raffle_contract
):
    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee - 1)
    with pytest.raises(Exception):
        raffle_contract.enter_raffle(
            sender=RAFFLE_PLAYER_ONE, value=deployment_config.entrance_fee
        )


def test_enter_raffle_without_enough_eth_should_false(
    deployment_config, raffle_contract
):
    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee - 1)
    with boa.reverts("Raffle__NotEnoughETH"):
        raffle_contract.enter_raffle(
            sender=RAFFLE_PLAYER_ONE, value=deployment_config.entrance_fee - 1
        )


def test_enter_raffle_while_calculating_should_fail(
    deployment_config, raffle_contract_with_upkeep
):
    boa.env.set_balance(RAFFLE_PLAYER_FOUR, deployment_config.entrance_fee)
    with boa.reverts("Raffle__Not_Opened"):
        raffle_contract_with_upkeep.enter_raffle(
            sender=RAFFLE_PLAYER_FOUR, value=deployment_config.entrance_fee
        )


def test_accumulated_prize_before_any_players_have_entered_should_be_zero(
    raffle_contract,
):
    assert 0 == raffle_contract.get_s_accumulated_prize()


def test_collected_fees_before_any_players_have_entered_should_be_zero(
    raffle_contract,
):
    assert 0 == raffle_contract.get_s_collected_fees()


def test_enter_raffle_should_succeed(deployment_config, raffle_contract):
    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee)
    with boa.env.prank(RAFFLE_PLAYER_ONE):
        raffle_contract.enter_raffle(value=deployment_config.entrance_fee)

    assert (
        boa.env.get_balance(raffle_contract.address) == deployment_config.entrance_fee
    )


def test_enter_raffle_owner_should_fail(deployment_config, raffle_contract):
    owner = raffle_contract.get_i_owner()
    boa.env.set_balance(owner, deployment_config.entrance_fee)
    with boa.env.prank(owner):
        with boa.reverts("Raffle__Owner_Cannot_Participate"):
            raffle_contract.enter_raffle(value=deployment_config.entrance_fee)


def test_enter_raffle_second_time_should_fail(
    deployment_config, raffle_contract_with_players
):
    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee)
    with boa.reverts("Raffle__Player_Already_Entered"):
        raffle_contract_with_players.enter_raffle(
            sender=RAFFLE_PLAYER_ONE, value=deployment_config.entrance_fee
        )


def test_player_has_entered_success(raffle_contract_with_players):
    assert (
        raffle_contract_with_players.get_s_player_has_entered(RAFFLE_PLAYER_ONE) is True
    )


def test_player_ha_not_entered(raffle_contract_with_players):
    assert (
        raffle_contract_with_players.get_s_player_has_entered(RAFFLE_PLAYER_FOUR)
        is False
    )


def test_exit_raffle_success(raffle_contract_with_players):
    raffle_contract_with_players.exit_raffle(sender=RAFFLE_PLAYER_ONE)

    assert (
        raffle_contract_with_players.get_s_player_has_entered(RAFFLE_PLAYER_ONE)
        is False
    )
    assert len(raffle_contract_with_players.get_players()) == 2


def test_exit_raffle_emit_exit_event_success(raffle_contract_with_players):
    raffle_contract_with_players.exit_raffle(sender=RAFFLE_PLAYER_ONE)
    event = raffle_contract_with_players.get_logs()[0]
    assert (RAFFLE_PLAYER_ONE, boa.env.evm.patch.timestamp) == (
        event.player,
        event.timestamp,
    )


def test_exit_raffle_check_balance_success(
    deployment_config, raffle_contract_with_players
):
    starting_balance = boa.env.get_balance(RAFFLE_PLAYER_ONE)
    raffle_fee_percentage = raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE()
    raffle_fee_precision = (
        raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE_PRECISION()
    )
    lottery_fee_amount = (
        deployment_config.entrance_fee * raffle_fee_percentage
    ) // raffle_fee_precision
    raffle_contract_with_players.exit_raffle(sender=RAFFLE_PLAYER_ONE)

    ending_balance = boa.env.get_balance(RAFFLE_PLAYER_ONE)
    assert (
        starting_balance + deployment_config.entrance_fee - lottery_fee_amount
        == ending_balance
    )


def test_exit_raffle_while_calculating_should_fail(raffle_contract_with_upkeep):
    with boa.reverts("Raffle__Not_Opened"):
        raffle_contract_with_upkeep.exit_raffle(sender=RAFFLE_PLAYER_ONE)


def test_exit_raffle_player_not_entered_should_fail(raffle_contract_with_players):
    with boa.reverts("Raffle__Player_Not_Entered"):
        raffle_contract_with_players.exit_raffle(sender=RAFFLE_PLAYER_FOUR)


def test_check_upkeep_before_any_players_entered_should_be_false(
    raffle_contract,
):
    boa.env.time_travel(raffle_contract.get_s_interval() + 1)
    assert (False, b"") == raffle_contract.check_upkeep(b"")


def test_check_upkeep_with_one_player_entered_after_time_interval_expires_should_be_false(
    deployment_config,
    raffle_contract,
):
    boa.env.time_travel(raffle_contract.get_s_interval() + 1)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number + raffle_contract.get_s_interval() + 1
    )

    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee)
    raffle_contract.enter_raffle(
        value=deployment_config.entrance_fee, sender=RAFFLE_PLAYER_ONE
    )
    assert (False, b"") == raffle_contract.check_upkeep(b"")


def test_check_upkeep_with_two_players_entered_after_time_interval_expires_should_be_true(
    deployment_config,
    raffle_contract,
):
    boa.env.time_travel(raffle_contract.get_s_interval() + 1)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number + raffle_contract.get_s_interval() + 1
    )

    boa.env.set_balance(RAFFLE_PLAYER_ONE, deployment_config.entrance_fee)
    raffle_contract.enter_raffle(
        value=deployment_config.entrance_fee, sender=RAFFLE_PLAYER_ONE
    )

    boa.env.set_balance(RAFFLE_PLAYER_TWO, deployment_config.entrance_fee)
    raffle_contract.enter_raffle(
        value=deployment_config.entrance_fee, sender=RAFFLE_PLAYER_TWO
    )

    assert (True, b"") == raffle_contract.check_upkeep(b"")


def test_check_upkeep_before_time_expires_should_be_false(raffle_contract_with_players):
    boa.env.time_travel(raffle_contract_with_players.get_s_interval())
    upkeep_needed, _ = raffle_contract_with_players.check_upkeep(b"")
    assert upkeep_needed is False


def test_check_upkeep_after_time_expires_should_be_true(raffle_contract_with_players):
    boa.env.time_travel(raffle_contract_with_players.get_s_interval() + 1)
    upkeep_needed, _ = raffle_contract_with_players.check_upkeep(b"")
    assert upkeep_needed is True


def test_accumulated_prize_before_any_players_have_entered_should_be_product_of_the_entrance_fee_minus_lottery_fee(
    deployment_config,
    raffle_contract_with_players,
):
    raffle_fee_percentage = raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE()
    raffle_fee_precision = (
        raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE_PRECISION()
    )
    number_of_players = len(raffle_contract_with_players.get_players())
    expected_accumulated_prize = (
        (deployment_config.entrance_fee * number_of_players)
        * (raffle_fee_precision - raffle_fee_percentage)
    ) // raffle_fee_precision

    assert (
        expected_accumulated_prize
        == raffle_contract_with_players.get_s_accumulated_prize()
    )


def test_accumulated_prize_before_any_players_have_entered_should_be_product_of_the__lottery_fee_and_the_number_of_players(
    deployment_config,
    raffle_contract_with_players,
):
    raffle_fee_percentage = raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE()
    raffle_fee_precision = (
        raffle_contract_with_players.get_RAFFLE_FEE_PERCENTAGE_PRECISION()
    )
    number_of_players = len(raffle_contract_with_players.get_players())
    expected_collected_fees = (
        (deployment_config.entrance_fee * number_of_players) * (raffle_fee_percentage)
    ) // raffle_fee_precision

    assert (
        expected_collected_fees == raffle_contract_with_players.get_s_collected_fees()
    )


def test_withdraw_fees_without_any_fees_should_fail(raffle_contract):
    with boa.reverts("Raffle_No_Fees_Collected"):
        raffle_contract.withdraw_fees(sender=RAFFLE_OWNER)


def test_withdraw_fees_success(raffle_contract_with_players):
    collected_fees = raffle_contract_with_players.get_s_collected_fees()
    fee_collector_starting_balance = boa.env.get_balance(RAFFLE_FEE_COLLECTOR)

    raffle_contract_with_players.withdraw_fees(sender=RAFFLE_OWNER)

    fee_collector_ending_balance = boa.env.get_balance(RAFFLE_FEE_COLLECTOR)
    print(
        "STARTNG ",
        fee_collector_starting_balance,
        "Ending ",
        fee_collector_ending_balance,
    )
    assert fee_collector_starting_balance < fee_collector_ending_balance
    collected_fees_af = raffle_contract_with_players.get_s_collected_fees()


def test_withdraw_fees_not_the_owner_should_fail(raffle_contract_with_players):
    with boa.reverts("Raffle__NotOwner"):
        raffle_contract_with_players.withdraw_fees(sender=RAFFLE_FEE_COLLECTOR)


def test_perform_upkeep_success(raffle_contract_with_players):
    boa.env.time_travel(raffle_contract_with_players.get_s_interval() + 1)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number
        + raffle_contract_with_players.get_s_interval()
        + 1
    )
    request_id = raffle_contract_with_players.perform_upkeep(sender=RAFFLE_OWNER)
    assert request_id == 1


def test_perform_upkeep_without_enough_players_should_fail(raffle_contract):
    boa.env.time_travel(raffle_contract.get_s_interval() + 1)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number + raffle_contract.get_s_interval() + 1
    )
    with boa.reverts("Raffle__Upkeep_Conditions_Not_Met"):
        raffle_contract.perform_upkeep(sender=RAFFLE_OWNER)


def test_perform_upkeep_time_not_passed_should_fail(raffle_contract_with_players):
    boa.env.time_travel(raffle_contract_with_players.get_s_interval() - 10)
    boa.env.evm.patch.block_number = (
        boa.env.evm.patch.block_number
        + raffle_contract_with_players.get_s_interval()
        + 1
    )
    with boa.reverts("Raffle__Upkeep_Conditions_Not_Met"):
        raffle_contract_with_players.perform_upkeep(sender=RAFFLE_OWNER)


def test_perform_upkeep_not_in_open_state_should_fail(raffle_contract_with_upkeep):
    with boa.reverts("Raffle__Upkeep_Conditions_Not_Met"):
        raffle_contract_with_upkeep.perform_upkeep(sender=RAFFLE_OWNER)


def test_raffle_state_open_success(raffle_contract):
    print(f"Raffle state: {raffle_contract.get_s_raffle_state()}")
    assert RaffleState.OPEN == raffle_contract.get_s_raffle_state()


def test_raffle_state_calculating_success(raffle_contract_with_upkeep):
    print(f"Raffle state: {raffle_contract_with_upkeep.get_s_raffle_state()}")
    assert RaffleState.CALCULATING == raffle_contract_with_upkeep.get_s_raffle_state()


def test_fullfil_random_words_player_three_wins_success(
    vrf_coordinator_mock, raffle_contract_with_upkeep
):
    request_id = 1
    boa.env.evm.patch.block_number = 13
    boa.env.time_travel(raffle_contract_with_upkeep.get_s_interval() + 100)
    accumulated_prize = raffle_contract_with_upkeep.get_s_accumulated_prize()
    player_prize_amount_before = raffle_contract_with_upkeep.get_s_player_prize(
        RAFFLE_PLAYER_THREE
    )

    vrf_coordinator_mock.trigger_fullfil_random_words(request_id, sender=RAFFLE_OWNER)

    player_prize_amount_after = raffle_contract_with_upkeep.get_s_player_prize(
        RAFFLE_PLAYER_THREE
    )

    assert player_prize_amount_before + accumulated_prize == player_prize_amount_after


def test_fullfil_random_words_raffle_open_success(
    vrf_coordinator_mock, raffle_contract_with_upkeep
):
    request_id = 1
    boa.env.evm.patch.block_number = 13
    boa.env.time_travel(raffle_contract_with_upkeep.get_s_interval() + 100)

    vrf_coordinator_mock.trigger_fullfil_random_words(request_id, sender=RAFFLE_OWNER)
    assert RaffleState.OPEN == raffle_contract_with_upkeep.get_s_raffle_state()


def test_fullfil_random_words_raffle_no_players_success(
    vrf_coordinator_mock, raffle_contract_with_upkeep
):
    request_id = 1
    boa.env.evm.patch.block_number = 13
    boa.env.time_travel(raffle_contract_with_upkeep.get_s_interval() + 100)

    vrf_coordinator_mock.trigger_fullfil_random_words(request_id, sender=RAFFLE_OWNER)
    assert 0 == len(raffle_contract_with_upkeep.get_players())


def test_fullfil_random_words_raffle_start_time_equals_current_time_success(
    vrf_coordinator_mock, raffle_contract_with_upkeep
):
    request_id = 1
    boa.env.evm.patch.block_number = 13
    boa.env.time_travel(raffle_contract_with_upkeep.get_s_interval() + 100)

    vrf_coordinator_mock.trigger_fullfil_random_words(request_id, sender=RAFFLE_OWNER)
    assert boa.env.evm.patch.timestamp == raffle_contract_with_upkeep.get_s_start_time()


def test_winner_withdraw_prize_success(raffle_contract_with_winner):
    winner_prize = raffle_contract_with_winner.get_s_player_prize(RAFFLE_PLAYER_THREE)
    winner_starting_balance = boa.env.get_balance(RAFFLE_PLAYER_THREE)
    raffle_contract_with_winner.withdraw_prize(sender=RAFFLE_PLAYER_THREE)
    winner_balance_after_withdraw = boa.env.get_balance(RAFFLE_PLAYER_THREE)

    assert winner_starting_balance + winner_prize == winner_balance_after_withdraw


def test_winner_withdraw_prize_not_a_winner_should_fail(raffle_contract_with_winner):
    with boa.reverts("Raffle__NoPrizeToWithdraw"):
        raffle_contract_with_winner.withdraw_prize(sender=RAFFLE_PLAYER_ONE)
