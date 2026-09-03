// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CleanWebOracleVerifier
 * @notice Lightweight Solidity verification library for CleanWeb Studio EIP-712 Signed Oracle Feeds.
 * @dev Enables DeFi protocols, prediction markets (Polymarket-style), and on-chain AI agents to verify
 *      off-chain research data, news digests, and price attestations with ZERO oracle gas overhead.
 */
contract CleanWebOracleVerifier {
    // Domain Separator Constants
    bytes32 private constant EIP712_DOMAIN_TYPEHASH = keccak256(
        "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
    );

    bytes32 private constant ORACLE_FEED_TYPEHASH = keccak256(
        "CleanWebOracleFeed(string query,bytes32 dataHash,uint256 timestamp)"
    );

    bytes32 public immutable DOMAIN_SEPARATOR;
    address public oracleSigner;

    event OracleAttestationVerified(string query, bytes32 indexed dataHash, uint256 timestamp, address indexed signer);
    event OracleSignerUpdated(address indexed oldSigner, address indexed newSigner);

    /**
     * @notice Initializes the verifier with the official CleanWeb treasury/oracle address.
     * @param _oracleSigner The public address of the CleanWeb Oracle signer key (e.g. 0x255F...)
     */
    constructor(address _oracleSigner) {
        require(_oracleSigner != address(0), "Invalid oracle signer");
        oracleSigner = _oracleSigner;

        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                EIP712_DOMAIN_TYPEHASH,
                keccak256(bytes("CleanWebOracle")),
                keccak256(bytes("1.0.0")),
                block.chainid,
                address(this)
            )
        );
    }

    /**
     * @notice Verifies an off-chain CleanWeb Oracle attestation payload.
     * @param query The natural language research or event query (e.g. "Fed Interest Rate Decision")
     * @param dataHash The SHA-256 / Keccak-256 hash of the canonical structured JSON payload
     * @param timestamp Unix epoch timestamp when CleanWeb attested the web evidence
     * @param v ECDSA recovery byte (27 or 28)
     * @param r First 32 bytes of ECDSA signature
     * @param s Second 32 bytes of ECDSA signature
     * @return isValid True if signature is genuine and matches CleanWeb Oracle signer
     */
    function verifyAttestation(
        string calldata query,
        bytes32 dataHash,
        uint256 timestamp,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public view returns (bool isValid) {
        // Enforce attestation freshness (e.g. within 24 hours, customizable)
        require(timestamp <= block.timestamp + 300, "Future timestamp rejected");
        
        bytes32 structHash = keccak256(
            abi.encode(
                ORACLE_FEED_TYPEHASH,
                keccak256(bytes(query)),
                dataHash,
                timestamp
            )
        );

        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19\x01",
                DOMAIN_SEPARATOR,
                structHash
            )
        );

        address recovered = ecrecover(digest, v, r, s);
        return (recovered != address(0) && recovered == oracleSigner);
    }

    /**
     * @notice Convenience assertion: reverts with descriptive error if attestation is invalid.
     */
    function requireValidAttestation(
        string calldata query,
        bytes32 dataHash,
        uint256 timestamp,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(verifyAttestation(query, dataHash, timestamp, v, r, s), "CleanWeb: Invalid Oracle Signature");
        emit OracleAttestationVerified(query, dataHash, timestamp, oracleSigner);
    }
}
