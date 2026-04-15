# pragma version ^0.4.1
# @license MIT

from interfaces import IVRFCoordinatorV2Plus

flag RaffleState:
    OPEN
    CALCULATING

MINIMUM_INTERVAL: constant(uint256) = 60
RAFFLE_FEE_PERCENTAGE: constant(uint256) = 3
RAFFLE_FEE_PERCENTAGE_PRECISION: constant(uint256) = 100
MINIMUM_PARTICIPANTS: constant(uint256) = 2
MAXIMUM_PARTICIPANTS: constant(uint256) = 50

CALLBACK_GAS_LIMIT: constant(uint32) = 5000000

i_owner: immutable(address)
i_fee_collector: immutable(address)
i_vrf_coordinator: immutable(address)
i_entrance_fee: immutable(uint256)
i_subscription_id: immutable(uint256)
i_key_hash: immutable(bytes32)

s_raffle_state: RaffleState
s_interval: uint256
s_start_time: uint256
s_collected_fees: uint256
s_accumulated_prize: uint256

s_players: DynArray[address, MAXIMUM_PARTICIPANTS]
s_player_has_entered: HashMap[address, bool]
s_player_prize: HashMap[address, uint256]

event RaffleEntered:
    player: indexed(address)
    timestamp: uint256
    entrance_fee: uint256

event RaffleExited:
    player: indexed(address)
    timestamp: uint256

event PickWinner:
    winner: indexed(address)
    prize: uint256
    timestamp: uint256

event WithdrawPrize:
    winner: indexed(address)
    prize: uint256
    timestamp: uint256

@deploy
def __init__(_fee_collector: address, _entrance_fee: uint256, _interval: uint256, _vrf_coordinator: address, _subscription_id: uint256, _key_hash: bytes32):
    assert _fee_collector != empty(address), "Raffle_Invalid_Fee_Collector"
    assert _fee_collector != msg.sender, "Raffle_Fee_Collector_Should_Be_Different_From_Owner"
    assert _entrance_fee > 1, "Raffle_Invalid_Entrance_Fee"
    assert _vrf_coordinator != empty(address), "Raffle_Invalid_VRF_Coordinator"
    assert _interval >= MINIMUM_INTERVAL, "Raffle__Invalid_Interval"
    assert _subscription_id > 0, "Raffle_Invalid_Subscription_ID"

    i_owner = msg.sender
    i_fee_collector = _fee_collector
    i_vrf_coordinator = _vrf_coordinator
    i_entrance_fee = _entrance_fee
    i_subscription_id = _subscription_id
    i_key_hash = _key_hash

    self.s_raffle_state = RaffleState.OPEN
    self.s_start_time = block.timestamp
    self.s_interval = _interval

@external
def set_raffle_interval(_interval: uint256):
    self._only_owner()  # Apply owner check
    assert _interval > MINIMUM_INTERVAL, "Raffle__InvalidInterval"
    self.s_interval = _interval

@payable
@external
def enter_raffle():
    self._opened()
    self._not_the_owner()
    self._not_entered()
    self.s_players.append(msg.sender)
    self.s_player_has_entered[msg.sender] = True
    self.calculate_prize_and_fees()
    log RaffleEntered(player = msg.sender, timestamp = block.timestamp, entrance_fee = msg.value)

@external
def exit_raffle():
    self._opened()
    assert self.s_player_has_entered[msg.sender], "Raffle__Player_Not_Entered"
    
    # Find and remove player
    number_of_players: uint256 = len(self.s_players)
    for i: uint256 in range(number_of_players, bound=MAXIMUM_PARTICIPANTS):
        if self.s_players[i] == msg.sender:
            # Swap with last and pop
            last_idx: uint256 = len(self.s_players) - 1
            if i != last_idx:
                self.s_players[i] = self.s_players[last_idx]
            self.s_players.pop()
            break
    
    # Clear entry
    self.s_player_has_entered[msg.sender] = False
    
    # Refund but keep the 3% fee for the lottery i.e. refund 97% of the entrance fee
    refund_amount: uint256 = i_entrance_fee * (RAFFLE_FEE_PERCENTAGE_PRECISION - RAFFLE_FEE_PERCENTAGE) // RAFFLE_FEE_PERCENTAGE_PRECISION 
    log RaffleExited(player = msg.sender, timestamp = block.timestamp)
    raw_call(msg.sender, b"", value=refund_amount)

@external
def check_upkeep(data: Bytes[64]) -> (bool, Bytes[64]):
    return self._check_upkeep()

@external
def perform_upkeep() -> uint256:
    upkeep: bool = False
    data: Bytes[64] = empty(Bytes[64])
    upkeep, data = self._check_upkeep()

    assert upkeep, "Raffle__Upkeep_Conditions_Not_Met"
    self.s_raffle_state = RaffleState.CALCULATING
    request_id: uint256 = extcall IVRFCoordinatorV2Plus(i_vrf_coordinator).requestRandomWords(IVRFCoordinatorV2Plus.RandomWordsRequest(
        keyHash = i_key_hash,
        subId = i_subscription_id,
        requestConfirmations = 1,
        callbackGasLimit = CALLBACK_GAS_LIMIT,
        numWords = 2,
        extraArgs = b""
    ))

    return request_id

@external 
def fullfil_random_words(request_id: uint256, random_words: DynArray[uint256, 3]):
    self._only_when_calculating()
    self._only_vrf_coordinator()
    winner_index: uint256 = random_words[0] % len(self.s_players)
    self.s_player_prize[self.s_players[winner_index]] += self.s_accumulated_prize
    self.s_accumulated_prize = 0

    for i:uint256 in range(len(self.s_players), bound=MAXIMUM_PARTICIPANTS):
        self.s_player_has_entered[self.s_players[i]] = False

    log PickWinner(winner = self.s_players[winner_index], prize = self.s_player_prize[self.s_players[winner_index]], timestamp = block.timestamp)
    self.s_players = []
    self.s_start_time = block.timestamp
    self.s_raffle_state = RaffleState.OPEN

@external
@nonreentrant
def withdraw_fees():
    self._has_collected_fees()
    self._only_owner()
    fees_to_withdraw: uint256 = self.s_collected_fees
    self.s_collected_fees = 0
    success: bool = False
    return_data: Bytes[64] = b""
    raw_call(i_fee_collector, b"", value=fees_to_withdraw)


@external
def withdraw_prize():
    prize: uint256 = self.s_player_prize[msg.sender]
    assert prize > 0, "Raffle__NoPrizeToWithdraw"
    self.s_player_prize[msg.sender] = 0
    raw_call(msg.sender, b"", value=prize)

# Getter methods for constants
@view
@external
def get_MINIMUM_INTERVAL() -> uint256:
    return MINIMUM_INTERVAL

@view
@external
def get_RAFFLE_FEE_PERCENTAGE() -> uint256:
    return RAFFLE_FEE_PERCENTAGE

@view
@external
def get_RAFFLE_FEE_PERCENTAGE_PRECISION() -> uint256:
    return RAFFLE_FEE_PERCENTAGE_PRECISION

@view
@external
def get_MINIMUM_PARTICIPANTS() -> uint256:
    return MINIMUM_PARTICIPANTS

@view
@external
def get_MAXIMUM_PARTICIPANTS() -> uint256:
    return MAXIMUM_PARTICIPANTS

@view
@external
def get_CALLBACK_GAS_LIMIT() -> uint32:
    return CALLBACK_GAS_LIMIT

# Getter methods for immutables
@view
@external
def get_i_owner() -> address:
    return i_owner

@view
@external
def get_i_fee_collector() -> address:
    return i_fee_collector

@view
@external
def get_i_vrf_coordinator() -> address:
    return i_vrf_coordinator

@view
@external
def get_i_entrance_fee() -> uint256:
    return i_entrance_fee

@view
@external
def get_i_subscription_id() -> uint256:
    return i_subscription_id

@view
@external
def get_i_key_hash() -> bytes32:
    return i_key_hash

# Getter methods for storage variables
@view
@external
def get_s_raffle_state() -> RaffleState:
    return self.s_raffle_state

@view
@external
def get_s_interval() -> uint256:
    return self.s_interval

@view
@external
def get_s_start_time() -> uint256:
    return self.s_start_time

@view
@external
def get_s_collected_fees() -> uint256:
    return self.s_collected_fees

@view
@external
def get_s_accumulated_prize() -> uint256:
    return self.s_accumulated_prize

@view
@external
def get_s_player_has_entered(player: address) -> bool:
    return self.s_player_has_entered[player]

@view
@external
def get_s_player_prize(player: address) -> uint256:
    return self.s_player_prize[player]

@view
@external
def get_players() -> DynArray[address, MAXIMUM_PARTICIPANTS]:
    return self.s_players

@internal
def _check_upkeep() -> (bool, Bytes[64]):
    has_players: bool = len(self.s_players) >= MINIMUM_PARTICIPANTS
    is_opened: bool = self.s_raffle_state == RaffleState.OPEN
    has_time_passed: bool = block.timestamp > self.s_start_time + self.s_interval

    if has_players and is_opened and has_time_passed:
        return (True, b"")
    else:
        return (False, b"")

@view
@internal
def _only_owner():
    assert msg.sender == i_owner, "Raffle__NotOwner"

@internal
def _not_the_owner():
    assert msg.sender != i_owner, "Raffle__Owner_Cannot_Participate"
    
@internal
def _not_entered():
    assert not self.s_player_has_entered[msg.sender], "Raffle__Player_Already_Entered"

@internal
def _opened():
    assert self.s_raffle_state == RaffleState.OPEN, "Raffle__Not_Opened"

@internal
def _not_opened():
    assert self.s_raffle_state != RaffleState.OPEN, "Raffle_Opened"

@internal
def _has_players():
    assert len(self.s_players) > 0, "Raffle__No_Players"

@internal
def _has_collected_fees():
    assert self.s_collected_fees > 0, "Raffle_No_Fees_Collected"
    
@internal
def _only_vrf_coordinator():
    assert msg.sender == i_vrf_coordinator, "Raffle__Not_VRF_Coordinator"

@internal
def _only_when_calculating():
    assert self.s_raffle_state == RaffleState.CALCULATING, "Raffle__Not_Calculating"

@payable
@internal
def calculate_prize_and_fees():
    assert msg.value >= i_entrance_fee, "Raffle__NotEnoughETH"
    self.s_collected_fees += ((msg.value * RAFFLE_FEE_PERCENTAGE)) // RAFFLE_FEE_PERCENTAGE_PRECISION
    self.s_accumulated_prize += ((msg.value * (RAFFLE_FEE_PERCENTAGE_PRECISION - RAFFLE_FEE_PERCENTAGE))) // RAFFLE_FEE_PERCENTAGE_PRECISION 
