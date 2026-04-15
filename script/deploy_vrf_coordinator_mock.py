from src.mocks import VRFCoordinatorV2PlusMock
from moccasin.boa_tools import VyperContract


def deploy_vrf_coordinator_mock() -> VyperContract:
    vrf_coordinator_mock_contract = VRFCoordinatorV2PlusMock.deploy()
    return vrf_coordinator_mock_contract


def moccasin_main() -> VyperContract:
    return deploy_vrf_coordinator_mock()
