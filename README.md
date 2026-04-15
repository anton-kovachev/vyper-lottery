# Vyper Raffle - Decentralized Lottery Smart Contract

🎲 A provably fair, decentralized raffle system built with Vyper and powered by Chainlink VRF for verifiable randomness.

---

## 🎯 Goals

The Vyper Raffle project aims to:

1. **Provide Transparent Lottery Mechanics**: Create a fully transparent and auditable on-chain raffle system where all operations are verifiable on the blockchain.

2. **Ensure Provable Fairness**: Leverage Chainlink VRF (Verifiable Random Function) to guarantee tamper-proof randomness for winner selection, eliminating any possibility of manipulation.

3. **Demonstrate Vyper Best Practices**: Showcase secure and efficient smart contract development using Vyper, a Pythonic language designed for the Ethereum Virtual Machine (EVM).

4. **Enable Automated Operations**: Implement Chainlink Automation (formerly Keepers) compatible functions for automated raffle cycles without manual intervention.

5. **Support Multi-Network Deployment**: Provide seamless deployment across multiple networks including local testnets, Ethereum Sepolia, and zkSync Era.

---

## 💼 Business Case

### Problem Statement
Traditional lottery systems suffer from:
- Lack of transparency in winner selection
- Centralized control leading to trust issues
- High operational costs and fees
- Geographic restrictions and accessibility limitations
- Delayed prize distribution

### Solution
The Vyper Raffle smart contract addresses these issues by:

- **Trustless Operation**: Fully decentralized with no central authority controlling the raffle
- **Transparent Prize Pool**: All funds are held in smart contracts with visible balances
- **Automated Distribution**: Winners can claim prizes instantly without intermediaries
- **Low Fees**: Only 3% platform fee on entrance, with 97% going to the prize pool
- **Global Accessibility**: Anyone with an Ethereum wallet can participate
- **Verifiable Randomness**: Chainlink VRF ensures cryptographically secure winner selection

### Use Cases

1. **Community Raffles**: Communities can run fair fundraising raffles
2. **NFT Projects**: Projects can use it for whitelist spot lotteries
3. **DAO Treasury Management**: DAOs can implement fair distribution mechanisms
4. **Gaming Platforms**: Integration into Web3 gaming for prize pools
5. **Charitable Lotteries**: Transparent charity fundraising with verifiable winner selection

### Revenue Model

- Platform collects a 3% fee from entrance payments
- Fees are automatically segregated and sent to a designated fee collector address
- Sustainable model that incentivizes platform maintenance and development

---

## 🛠️ Technologies Used

### Smart Contract Development

- **[Vyper](https://docs.vyperlang.org/)** (v0.4.1+): Pythonic smart contract language focused on security and auditability
- **[Moccasin](https://github.com/Cyfrin/moccasin)** (v0.4.3+): Modern Python-based development framework for Vyper contracts
- **[Titanoboa](https://github.com/vyperlang/titanoboa)**: Vyper interpreter for testing and local development

### Blockchain & Oracles

- **[Ethereum](https://ethereum.org/)**: Primary blockchain platform (EVM compatible)
- **[zkSync Era](https://zksync.io/)**: Layer 2 scaling solution support
- **[Chainlink VRF V2 Plus](https://docs.chain.link/vrf)**: Verifiable random function for provably fair winner selection
- **[Chainlink Automation](https://docs.chain.link/chainlink-automation)**: Time-based automated raffle execution

### Development & Testing

- **Python 3.12+**: Primary development language
- **pytest**: Testing framework
- **Anvil**: Local Ethereum node for development (via Foundry)

### Networks Supported

- **PyEVM**: Local Python-based EVM for unit testing
- **Anvil**: Local development network
- **Ethereum Sepolia**: Ethereum testnet
- **zkSync Sepolia**: zkSync Era testnet
- **Mainnet Ready**: Easily configurable for production deployment

---

## 🚀 Project Setup

### Prerequisites

- Python 3.12 or higher
- pip package manager
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vyper-raffle
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Install Moccasin**
   ```bash
   pip install moccasin
   ```

### Configuration

1. **Environment Variables**
   
   Create a `.env` file in the project root:
   ```env
   # For testnet deployments
   SEPOLIA_RPC_URL=your_sepolia_rpc_url
   PRIVATE_KEY=your_private_key
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```

2. **Network Configuration**
   
   Edit `moccasin.toml` to configure network-specific parameters:
   - Entrance fee
   - Raffle interval
   - Fee collector address
   - VRF Coordinator address
   - Subscription ID

### Development Workflow

1. **Deploy to local network**
   ```bash
   mox run deploy
   ```

2. **Run unit tests**
   ```bash
   mox test
   ```

3. **Run specific test file**
   ```bash
   mox test tests/test_raffle.py
   ```

4. **Run staging tests (requires testnet deployment)**
   ```bash
   mox test tests/staging/test_staging_raffle.py --network sepolia
   ```

5. **Deploy to testnet**
   ```bash
   mox run deploy --network sepolia
   ```

### Contract Architecture

```
src/
├── Raffle.vy                          # Main raffle contract
├── Counter.vy                         # Example counter contract
├── interfaces/
│   └── IVRFCoordinatorV2Plus.vyi     # Chainlink VRF interface
└── mocks/
    └── VRFCoordinatorV2PlusMock.vy   # Mock for local testing
```

### Key Features Implementation

- **Entrance Fee**: Configurable minimum payment required to enter
- **Raffle Interval**: Minimum time between raffle rounds (60 seconds minimum)
- **Maximum Participants**: Up to 50 participants per raffle
- **Fee Structure**: 3% platform fee, 97% to prize pool
- **Exit Mechanism**: Players can exit before winner selection (with 3% fee retained)
- **Automated Triggering**: Compatible with Chainlink Automation for autonomous operation
- **Prize Claiming**: Winners can claim accumulated prizes at any time

---

## 📚 Reference Information

### Smart Contract Functions

#### User Functions

- `enter_raffle()`: Enter the raffle by paying the entrance fee
- `exit_raffle()`: Exit before winner selection (97% refund)
- `withdraw_prize()`: Claim accumulated prizes

#### Admin Functions

- `set_raffle_interval(uint256)`: Update the raffle interval (owner only)
- `withdraw_fees()`: Withdraw collected platform fees (fee collector only)

#### Automation Functions

- `check_upkeep(bytes)`: Check if raffle is ready for winner selection
- `perform_upkeep()`: Trigger winner selection and request randomness

#### Chainlink VRF Callback

- `fullfil_random_words(uint256, uint256[])`: Receive random numbers and select winner

### Events

- `RaffleEntered(address indexed player, uint256 timestamp, uint256 entrance_fee)`
- `RaffleExited(address indexed player, uint256 timestamp)`
- `PickWinner(address indexed winner, uint256 prize, uint256 timestamp)`
- `WithdrawPrize(address indexed winner, uint256 prize, uint256 timestamp)`

### Security Features

- **Reentrancy Protection**: Uses checks-effects-interactions pattern
- **Access Control**: Owner and fee collector role separation
- **State Machine**: OPEN/CALCULATING states prevent race conditions
- **Input Validation**: Comprehensive parameter validation in constructor and functions
- **Overflow Protection**: Vyper's built-in overflow checks

### Gas Optimization

- Dynamic arrays for player storage
- HashMap for O(1) entry lookups
- Efficient player removal using swap-and-pop
- Minimal storage updates

### Testing Strategy

1. **Unit Tests** (`tests/test_raffle.py`):
   - Contract deployment
   - Entry and exit mechanisms
   - Winner selection logic
   - Fee calculations
   - Access control

2. **Integration Tests** (staging):
   - VRF integration
   - Cross-contract interactions
   - Network-specific behavior

### Chainlink VRF Setup

To deploy on testnet/mainnet, you need:

1. Create a VRF subscription at [vrf.chain.link](https://vrf.chain.link)
2. Fund the subscription with LINK tokens
3. Add your deployed Raffle contract as a consumer
4. Update subscription ID in `moccasin.toml` or deployment script

### Useful Commands

```bash
# Compile contracts
mox compile

# Interactive console
mox console

# View contract size
mox inspect

# Run deployment on specific network
mox run deploy --network sepolia

# Get help
mox --help
```

### Resources

- [Vyper Documentation](https://docs.vyperlang.org/)
- [Moccasin Documentation](https://cyfrin.github.io/moccasin)
- [Chainlink VRF Documentation](https://docs.chain.link/vrf)
- [Chainlink Automation Documentation](https://docs.chain.link/chainlink-automation)
- [Cyfrin Updraft](https://updraft.cyfrin.io/) - Blockchain development courses

### Contributing

Contributions are welcome! Please ensure:
- All tests pass before submitting PRs
- Code follows Vyper style guidelines
- New features include corresponding tests
- Documentation is updated

### License

MIT License - see LICENSE file for details

---

_Built with 🐍 Vyper and ⛓️ Chainlink_
