# 🔗 AVFA Smart Contracts & Blockchain Ledger Registry
### **Smart India Hackathon (SIH25029)**
### **Team Astrix**

This module contains production-grade Solidity smart contracts implementing on-chain cryptographic certificate anchoring, institutional authorization, and decentralized revocation for the **AVFA (Authenticity Validator for Academia)** platform.

---

## 🏛️ Smart Contracts Overview

| Contract Name | Description | Key Functions |
|---|---|---|
| **`AcademicCertificateRegistry.sol`** | Core decentralized ledger mapping certificate IDs and SHA-256 hashes to accredited issuing institutions. | `issueCertificate`, `batchIssueCertificates`, `anchorMerkleRoot`, `revokeCertificate`, `verifyCertificate` |
| **`InstitutionGovernance.sol`** | Multi-authority governance module for AICTE/UGC/State accreditation and guardian management. | `addGuardian`, `removeGuardian`, `onlyAdmin` |

---

## 🚀 Quick Setup & Testing

### 1. Install Dependencies:
```bash
cd smart-contracts
npm install
```

### 2. Compile Smart Contracts:
```bash
npx hardhat compile
```

### 3. Run Automated Unit Tests:
```bash
npx hardhat test
```

### 4. Deploy to Testnet (Polygon Amoy / Ethereum Sepolia):
```bash
npx hardhat run scripts/deploy.js --network polygonAmoy
```

---

## 🔒 Security & Immutability Guarantees

1. **Role-Based Access Control (RBAC):** Only verified, accredited institution wallets (`onlyAuthorizedIssuer`) can write certificate records or anchor Merkle roots.
2. **Deterministic Uniqueness:** Reverts any duplicate certificate number or collision hash.
3. **Permanent Audit Trail:** Revocation preserves historical issuance timestamps and attaches an immutable audit reason.
