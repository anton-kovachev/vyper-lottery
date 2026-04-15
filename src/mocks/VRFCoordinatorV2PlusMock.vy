# pragma version ^0.4.1
# @license MIT

from interfaces import IVRFCoordinatorV2Plus

struct RandomWordsRequest:
    request_id:  uint256
    request_sender: address

owner: public(address)
request_number: uint256
random_words_requests: HashMap[uint256, RandomWordsRequest]

@deploy
def __init__():
    self.owner = msg.sender

@external
def requestRandomWords(req: IVRFCoordinatorV2Plus.RandomWordsRequest) -> uint256:
    # Mock implementation - return a dummy request ID
    self.request_number += 1
    self.random_words_requests[self.request_number] = RandomWordsRequest(request_id=self.request_number, request_sender=msg.sender)
    return self.request_number

@external
@nonreentrant
def trigger_fullfil_random_words(request_id: uint256):
    self._only_owner()
    request: RandomWordsRequest = self.random_words_requests[request_id]
    assert request.request_id == request_id, "VRFCoordinatorV2PlusMock_Request_Not_Found"
    random_words: uint256[2] = [block.number, block.timestamp]
    
    # ABI encode: method_id + request_id + offset + array_length + array_elements
    # For DynArray, the ABI signature uses uint256[] not DynArray
    calldata: Bytes[164] = concat(
        method_id("fullfil_random_words(uint256,uint256[])"),  # 4 bytes
        convert(request_id, bytes32),                          # 32 bytes - first param
        convert(64, bytes32),                                  # 32 bytes - offset to array data (0x40)
        convert(2, bytes32),                                   # 32 bytes - array length
        convert(random_words[0], bytes32),                     # 32 bytes - element 0
        convert(random_words[1], bytes32)                      # 32 bytes - element 1
    )
    
    raw_call(request.request_sender, calldata)


@internal
def _only_owner():
    assert msg.sender == self.owner, "VRFCoordinatorV2PlusMock_NotOwner"
    
