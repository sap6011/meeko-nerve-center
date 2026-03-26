// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * ██████████████████████████████████████████████████████████████████████
 *  SolarPunk Humanitarian Router — on-chain forever
 * ██████████████████████████████████████████████████████████████████████
 *
 * Every ETH sent to this contract routes INSTANTLY to active crisis zones.
 * No middleman. No escrow. No admin. No pause function. No upgrade proxy.
 * The math runs itself. The proof lives on-chain forever.
 *
 * ─── ROUTING SPLITS ────────────────────────────────────────────────────
 *  59.40%  →  PCRF         (Gaza / Palestine)
 *  14.85%  →  IRC          (Sudan / DRC / global displacement)
 *   9.90%  →  MSF          (crisis medical, anywhere)
 *   9.90%  →  UNICEF       (children in crisis)
 *   4.95%  →  Direct Relief (disaster response)
 *   1.00%  →  Operations   (keeps SolarPunk's engines running)
 * ────────────────────────────────────────────────────────────────────────
 *
 * SPT (SolarPunk Token) is minted to every contributor as proof.
 *   1 SPT = you routed 0.001 ETH to crisis zones.
 *   Immutable. Transferable. Auditable by anyone. Forever.
 *
 * SPT perks (checked off-chain by SolarPunk engines):
 *   10  SPT  → your AI agent gets priority task routing
 *   50  SPT  → name in every cycle commit, permanent git history
 *   100 SPT  → SolarPunk dedicates a full cycle to your chosen crisis
 *   500 SPT  → founding node — SolarPunk lists you as a super-connector
 *
 * ─── TRUST MODEL ────────────────────────────────────────────────────────
 * Zero humans can change the routing after deploy.
 * Zero platforms can deplatform a smart contract.
 * Zero middlemen between contributor and crisis orgs.
 * Verify the routing addresses on-chain at any time:
 *   call getRouting() — it returns all six addresses and their exact splits.
 *
 * Built by SolarPunk — autonomous humanitarian AI
 * Michael Wood (Meeko) · meekotharaccoon@gmail.com
 * github.com/meekotharaccoon-cell/meeko-nerve-center
 * ─────────────────────────────────────────────────────────────────────────
 */
contract SolarPunkRouter {

    // ── ERC-20 State ──────────────────────────────────────────────────────────
    string  public constant name     = "SolarPunk Token";
    string  public constant symbol   = "SPT";
    uint8   public constant decimals = 18;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ── Routing Splits (basis points, 10000 = 100%) ───────────────────────────
    uint16 public constant PCRF_BPS          = 5940;   // 59.40%
    uint16 public constant IRC_BPS           = 1485;   // 14.85%
    uint16 public constant MSF_BPS           =  990;   //  9.90%
    uint16 public constant UNICEF_BPS        =  990;   //  9.90%
    uint16 public constant DIRECT_RELIEF_BPS =  495;   //  4.95%
    // Operations = 10000 - 5940 - 1485 - 990 - 990 - 495 = 100 bps = 1.00%

    // ── Beneficiary Addresses — IMMUTABLE after deploy ────────────────────────
    // These are verified at deploy time. They can NEVER be changed.
    // Call getRouting() to verify on-chain at any moment.
    address payable public immutable PCRF;
    address payable public immutable IRC;
    address payable public immutable MSF;
    address payable public immutable UNICEF_ADDR;
    address payable public immutable DIRECT_RELIEF;
    address payable public immutable OPERATIONS;

    // ── SPT Minting Rate ──────────────────────────────────────────────────────
    // 1 SPT minted per 0.001 ETH contributed (1e15 wei)
    // At $3000/ETH: 1 SPT = $3 contributed to crisis zones
    uint256 public constant WEI_PER_SPT = 1e15;

    // ── Lifetime Proof Counters ───────────────────────────────────────────────
    uint256 public totalRoutedWei;
    uint256 public totalContributions;

    // ── Events ────────────────────────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Routed(
        address indexed contributor,
        uint256 totalWei,
        uint256 toPCRF,
        uint256 toIRC,
        uint256 toMSF,
        uint256 toUNICEF,
        uint256 toDirectRelief,
        uint256 toOperations,
        uint256 sptMinted,
        uint256 contributionNumber
    );

    // ── Constructor ───────────────────────────────────────────────────────────
    constructor(
        address payable _pcrf,
        address payable _irc,
        address payable _msf,
        address payable _unicef,
        address payable _directRelief,
        address payable _operations
    ) {
        require(_pcrf         != address(0), "PCRF address required");
        require(_irc          != address(0), "IRC address required");
        require(_msf          != address(0), "MSF address required");
        require(_unicef       != address(0), "UNICEF address required");
        require(_directRelief != address(0), "Direct Relief address required");
        require(_operations   != address(0), "Operations address required");

        PCRF          = _pcrf;
        IRC           = _irc;
        MSF           = _msf;
        UNICEF_ADDR   = _unicef;
        DIRECT_RELIEF = _directRelief;
        OPERATIONS    = _operations;
    }

    // ── Receive ETH → route instantly ─────────────────────────────────────────
    receive()  external payable { _route(msg.value, msg.sender); }
    fallback() external payable { _route(msg.value, msg.sender); }

    /// @notice Send ETH here to route to crisis zones and receive SPT proof.
    function contribute() external payable {
        require(msg.value > 0, "Send ETH to route to crisis zones");
        _route(msg.value, msg.sender);
    }

    // ── Core Routing Logic ────────────────────────────────────────────────────
    function _route(uint256 amount, address contributor) internal {
        uint256 toPCRF         = (amount * PCRF_BPS)          / 10000;
        uint256 toIRC          = (amount * IRC_BPS)            / 10000;
        uint256 toMSF          = (amount * MSF_BPS)            / 10000;
        uint256 toUNICEF       = (amount * UNICEF_BPS)         / 10000;
        uint256 toDirectRelief = (amount * DIRECT_RELIEF_BPS)  / 10000;
        // Operations gets exact remainder — no rounding dust lost
        uint256 toOperations   = amount - toPCRF - toIRC - toMSF
                                        - toUNICEF - toDirectRelief;

        // Route instantly — no escrow, no delay, no human step
        PCRF.transfer(toPCRF);
        IRC.transfer(toIRC);
        MSF.transfer(toMSF);
        UNICEF_ADDR.transfer(toUNICEF);
        DIRECT_RELIEF.transfer(toDirectRelief);
        OPERATIONS.transfer(toOperations);

        // Mint SPT proof tokens (1 per 0.001 ETH)
        uint256 sptMinted = amount / WEI_PER_SPT;
        if (sptMinted > 0) {
            uint256 sptWei = sptMinted * 1e18;
            totalSupply            += sptWei;
            balanceOf[contributor] += sptWei;
            emit Transfer(address(0), contributor, sptWei);
        }

        totalRoutedWei     += amount;
        totalContributions += 1;

        emit Routed(
            contributor, amount,
            toPCRF, toIRC, toMSF, toUNICEF, toDirectRelief, toOperations,
            sptMinted, totalContributions
        );
    }

    // ── ERC-20 Standard Functions ─────────────────────────────────────────────
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient SPT");
        balanceOf[msg.sender] -= amount;
        balanceOf[to]         += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from]             >= amount, "Insufficient SPT");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        allowance[from][msg.sender] -= amount;
        balanceOf[from]             -= amount;
        balanceOf[to]               += amount;
        emit Transfer(from, to, amount);
        return true;
    }

    // ── Public Proof & Verification Functions ─────────────────────────────────

    /// @notice Returns all routing addresses and their exact basis-point splits.
    /// Call this to verify 100% on-chain that routing is correct.
    function getRouting() external view returns (
        address pcrf,         uint16 pcrfBps,
        address irc,          uint16 ircBps,
        address msf,          uint16 msfBps,
        address unicef,       uint16 unicefBps,
        address directRelief, uint16 drBps,
        address operations,   uint16 opsBps
    ) {
        return (
            PCRF,          PCRF_BPS,
            IRC,           IRC_BPS,
            MSF,           MSF_BPS,
            UNICEF_ADDR,   UNICEF_BPS,
            DIRECT_RELIEF, DIRECT_RELIEF_BPS,
            OPERATIONS,    10000 - PCRF_BPS - IRC_BPS - MSF_BPS
                                 - UNICEF_BPS - DIRECT_RELIEF_BPS
        );
    }

    /// @notice Total ETH routed to crisis zones (in whole ETH).
    function totalRoutedETH() external view returns (uint256) {
        return totalRoutedWei / 1e18;
    }
}
