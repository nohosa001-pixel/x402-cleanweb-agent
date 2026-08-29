// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CleanWebOracleConsumer
 * @notice Verifies EIP-712 cryptographically signed web/youtube/pdf scrapings from CleanWeb Studio Oracle on Polygon, Base, and Arbitrum.
 */
contract CleanWebOracleConsumer {
    // EIP-712 Domain Separator constants
    bytes32 public immutable DOMAIN_SEPARATOR;
    bytes32 public constant ATTESTATION_TYPEHASH = keccak256(
        "CleanWebAttestation(string targetUrl,bytes32 contentHash,uint256 timestamp)"
    );

    address public oracleSigner;
    address public owner;

    struct AttestationRecord {
        bytes32 contentHash;
        uint256 timestamp;
        address recordedBy;
    }

    // targetUrl hash => AttestationRecord
    mapping(bytes32 => AttestationRecord) public attestations;

    event AttestationRecorded(
        string targetUrl,
        bytes32 indexed urlHash,
        bytes32 indexed contentHash,
        uint256 timestamp,
        address indexed recordedBy
    );
    event OracleSignerUpdated(address indexed previousSigner, address indexed newSigner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call");
        _;
    }

    constructor(address _oracleSigner) {
        owner = msg.sender;
        oracleSigner = _oracleSigner;

        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes("CleanWebOracle")),
                keccak256(bytes("1.0.0")),
                block.chainid,
                address(this)
            )
        );
    }

    function setOracleSigner(address _newSigner) external onlyOwner {
        require(_newSigner != address(0), "Invalid signer address");
        emit OracleSignerUpdated(oracleSigner, _newSigner);
        oracleSigner = _newSigner;
    }

    /**
     * @notice Records and verifies an oracle attestation with EIP-712 signature (v, r, s).
     */
    function recordAttestation(
        string calldata targetUrl,
        bytes32 contentHash,
        uint256 timestamp,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(timestamp <= block.timestamp + 300, "Timestamp too far in future");
        require(timestamp >= block.timestamp - 86400, "Attestation expired (>24h)");

        bytes32 structHash = keccak256(
            abi.encode(
                ATTESTATION_TYPEHASH,
                keccak256(bytes(targetUrl)),
                contentHash,
                timestamp
            )
        );

        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash)
        );

        address recoveredSigner = ecrecover(digest, v, r, s);
        require(recoveredSigner == oracleSigner, "Invalid CleanWeb Oracle signature");

        bytes32 urlHash = keccak256(bytes(targetUrl));
        attestations[urlHash] = AttestationRecord({
            contentHash: contentHash,
            timestamp: timestamp,
            recordedBy: msg.sender
        });

        emit AttestationRecorded(targetUrl, urlHash, contentHash, timestamp, msg.sender);
    }

    /**
     * @notice Verifies if a given text matches the on-chain recorded content hash for a URL.
     */
    function verifyContent(string calldata targetUrl, string calldata rawText) external view returns (bool) {
        bytes32 urlHash = keccak256(bytes(targetUrl));
        AttestationRecord memory record = attestations[urlHash];
        if (record.timestamp == 0) return false;

        bytes32 computedHash = keccak256(bytes(rawText));
        return record.contentHash == computedHash;
    }
}
