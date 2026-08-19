// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AcademicCertificateRegistry
 * @dev Immutable on-chain registry for authentic academic certificates and cryptographic Merkle roots.
 * Built for AVFA (Authenticity Validator for Academia) • SIH25029 • Team Astrix
 */
contract AcademicCertificateRegistry {

    struct CertificateRecord {
        bytes32 certHash;             // SHA-256 / Keccak-256 canonical hash digest
        string certNumber;            // Public certificate identifier (e.g. CERT-2026-DA3A5BFC)
        address issuer;               // Accredited issuing institution wallet
        uint256 issueTimestamp;       // Unix block timestamp of issuance
        bool isRevoked;               // Revocation state flag
        string revocationReason;      // Audit reason for invalidation
        uint256 revocationTimestamp;  // Unix timestamp of revocation (0 if active)
    }

    struct InstitutionProfile {
        string name;                  // Accredited institution name
        string accreditationCode;     // UGC / AICTE / State accreditation identifier
        bool isAuthorized;            // Authorization active flag
        uint256 authorizedAt;         // Timestamp of authorization
    }

    address public owner;
    uint256 public totalCertificatesIssued;
    uint256 public totalCertificatesRevoked;
    uint256 public totalMerkleBatchesAnchored;

    // Mapping from certificate identifier to CertificateRecord
    mapping(string => CertificateRecord) private certificatesByNumber;
    
    // Mapping from canonical certificate hash to certificate identifier
    mapping(bytes32 => string) private certNumberByHash;

    // Mapping from institution address to InstitutionProfile
    mapping(address => InstitutionProfile) public accreditedInstitutions;

    // Mapping from Merkle Root to batch size
    mapping(bytes32 => uint256) public merkleBatches;

    // Events
    event InstitutionAuthorized(address indexed institution, string name, string accreditationCode, uint256 timestamp);
    event InstitutionRevoked(address indexed institution, uint256 timestamp);
    event CertificateIssued(bytes32 indexed certHash, string indexed certNumber, address indexed issuer, uint256 timestamp);
    event BatchCertificatesIssued(uint256 count, address indexed issuer, uint256 timestamp);
    event CertificateRevoked(bytes32 indexed certHash, string indexed certNumber, address indexed revoker, string reason, uint256 timestamp);
    event MerkleRootAnchored(bytes32 indexed merkleRoot, uint256 batchSize, address indexed issuer, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "AVFA: Caller is not the governance authority");
        _;
    }

    modifier onlyAuthorizedIssuer() {
        require(
            accreditedInstitutions[msg.sender].isAuthorized || msg.sender == owner,
            "AVFA: Caller is not an accredited issuing institution"
        );
        _;
    }

    constructor() {
        owner = msg.sender;
        // Authorize contract deployer as root authority
        accreditedInstitutions[msg.sender] = InstitutionProfile({
            name: "AVFA Root Governance Authority",
            accreditationCode: "SIH25029-ROOT",
            isAuthorized: true,
            authorizedAt: block.timestamp
        });
    }

    /**
     * @notice Authorize an accredited academic institution to issue certificates.
     */
    function authorizeInstitution(
        address _institution,
        string memory _name,
        string memory _accreditationCode
    ) external onlyOwner {
        require(_institution != address(0), "AVFA: Invalid institution address");
        require(bytes(_name).length > 0, "AVFA: Institution name required");

        accreditedInstitutions[_institution] = InstitutionProfile({
            name: _name,
            accreditationCode: _accreditationCode,
            isAuthorized: true,
            authorizedAt: block.timestamp
        });

        emit InstitutionAuthorized(_institution, _name, _accreditationCode, block.timestamp);
    }

    /**
     * @notice Revoke authorization for an academic institution.
     */
    function revokeInstitution(address _institution) external onlyOwner {
        require(accreditedInstitutions[_institution].isAuthorized, "AVFA: Institution not authorized");
        accreditedInstitutions[_institution].isAuthorized = false;
        emit InstitutionRevoked(_institution, block.timestamp);
    }

    /**
     * @notice Issue a single academic certificate with cryptographic hash.
     */
    function issueCertificate(
        bytes32 _certHash,
        string memory _certNumber
    ) external onlyAuthorizedIssuer {
        require(_certHash != bytes32(0), "AVFA: Invalid certificate hash");
        require(bytes(_certNumber).length > 0, "AVFA: Certificate number required");
        require(certificatesByNumber[_certNumber].issueTimestamp == 0, "AVFA: Certificate number already registered");
        require(bytes(certNumberByHash[_certHash]).length == 0, "AVFA: Certificate hash already registered");

        certificatesByNumber[_certNumber] = CertificateRecord({
            certHash: _certHash,
            certNumber: _certNumber,
            issuer: msg.sender,
            issueTimestamp: block.timestamp,
            isRevoked: false,
            revocationReason: "",
            revocationTimestamp: 0
        });

        certNumberByHash[_certHash] = _certNumber;
        totalCertificatesIssued++;

        emit CertificateIssued(_certHash, _certNumber, msg.sender, block.timestamp);
    }

    /**
     * @notice Batch issue multiple academic certificates in a single atomic transaction.
     */
    function batchIssueCertificates(
        bytes32[] memory _certHashes,
        string[] memory _certNumbers
    ) external onlyAuthorizedIssuer {
        require(_certHashes.length == _certNumbers.length, "AVFA: Array lengths mismatch");
        require(_certHashes.length > 0, "AVFA: Empty batch");

        for (uint256 i = 0; i < _certHashes.length; i++) {
            bytes32 hash = _certHashes[i];
            string memory num = _certNumbers[i];

            require(certificatesByNumber[num].issueTimestamp == 0, "AVFA: Duplicate cert number in batch");
            require(bytes(certNumberByHash[hash]).length == 0, "AVFA: Duplicate cert hash in batch");

            certificatesByNumber[num] = CertificateRecord({
                certHash: hash,
                certNumber: num,
                issuer: msg.sender,
                issueTimestamp: block.timestamp,
                isRevoked: false,
                revocationReason: "",
                revocationTimestamp: 0
            });

            certNumberByHash[hash] = num;
            totalCertificatesIssued++;

            emit CertificateIssued(hash, num, msg.sender, block.timestamp);
        }

        emit BatchCertificatesIssued(_certHashes.length, msg.sender, block.timestamp);
    }

    /**
     * @notice Anchor a Merkle Root representing thousands of certificates into the blockchain.
     */
    function anchorMerkleRoot(bytes32 _merkleRoot, uint256 _batchSize) external onlyAuthorizedIssuer {
        require(_merkleRoot != bytes32(0), "AVFA: Invalid Merkle Root");
        require(_batchSize > 0, "AVFA: Batch size must be positive");
        require(merkleBatches[_merkleRoot] == 0, "AVFA: Merkle Root already anchored");

        merkleBatches[_merkleRoot] = _batchSize;
        totalMerkleBatchesAnchored++;

        emit MerkleRootAnchored(_merkleRoot, _batchSize, msg.sender, block.timestamp);
    }

    /**
     * @notice Revoke an issued academic certificate with an official audit reason.
     */
    function revokeCertificate(
        string memory _certNumber,
        string memory _reason
    ) external onlyAuthorizedIssuer {
        CertificateRecord storage record = certificatesByNumber[_certNumber];
        require(record.issueTimestamp > 0, "AVFA: Certificate not found");
        require(!record.isRevoked, "AVFA: Certificate already revoked");

        record.isRevoked = true;
        record.revocationReason = _reason;
        record.revocationTimestamp = block.timestamp;
        totalCertificatesRevoked++;

        emit CertificateRevoked(record.certHash, _certNumber, msg.sender, _reason, block.timestamp);
    }

    /**
     * @notice Public verification query by Certificate Number.
     */
    function verifyCertificate(string memory _certNumber) external view returns (
        bool exists,
        bool isValid,
        bool isRevoked,
        bytes32 certHash,
        address issuer,
        uint256 issueTimestamp,
        string memory revocationReason,
        uint256 revocationTimestamp
    ) {
        CertificateRecord memory record = certificatesByNumber[_certNumber];
        if (record.issueTimestamp == 0) {
            return (false, false, false, bytes32(0), address(0), 0, "", 0);
        }

        return (
            true,
            !record.isRevoked,
            record.isRevoked,
            record.certHash,
            record.issuer,
            record.issueTimestamp,
            record.revocationReason,
            record.revocationTimestamp
        );
    }

    /**
     * @notice Public verification query by Certificate Canonical SHA-256 Hash.
     */
    function verifyHash(bytes32 _certHash) external view returns (
        bool exists,
        bool isValid,
        string memory certNumber,
        address issuer,
        uint256 issueTimestamp
    ) {
        string memory certNum = certNumberByHash[_certHash];
        if (bytes(certNum).length == 0) {
            return (false, false, "", address(0), 0);
        }

        CertificateRecord memory record = certificatesByNumber[certNum];
        return (true, !record.isRevoked, certNum, record.issuer, record.issueTimestamp);
    }
}
