architecture_flow = """# AVFA System Architecture Flow

This document details the operational workflow of the **Authenticity Validator for Academia (AVFA)** platform (SIH25029).

It visualizes the complete lifecycle of an academic credential, divided into two distinct logical stages: **Issuance (Blue)** by authenticated institutions and **Verification (Orange)** by public users (e.g., employers).

---

## Technical Workflow Diagram

We leverage the **Mermaid.js** diagramming tool. If your repository markdown renderer (like GitHub) supports Mermaid, you will see a dynamic flowchart below. If not, the raw diagram code is provided in the **Raw Mermaid.js Source** section.

### Operational Flowchart

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#007bff', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#fff'}}}%%
graph TD
    %% Define Styles
    classDef institution fill:#d1ecf1,stroke:#0c5460,stroke-width:2px,rx:10,ry:10;
    classDef process fill:#f8f9fa,stroke:#343a40,stroke-width:1px,rx:5,ry:5;
    classDef storage fill:#ffc107,stroke:#856404,stroke-width:2px,stroke-dasharray: 5 5,rx:5,ry:5;
    classDef public fill:#ffeeba,stroke:#856404,stroke-width:2px,rx:10,ry:10;
    classDef final_valid fill:#d4edda,stroke:#155724,stroke-width:2px,rx:15,ry:15;
    classDef final_flag fill:#f8d7da,stroke:#721c24,stroke-width:2px,rx:15,ry:15;

    %% STAGE 1: ISSUANCE (Managed by Institution)
    subgraph IssuanceStage [STAGE 1: ISSUANCE]
        Inst[Institution Officer]:::institution -->|Logs In| Login[Auth & RBAC Check]:::process
        Login -->|Authorized| Details[Enter Certificate Details]:::process
        Details -->|Submit| GenPDF[Generate Certificate PDF + QR]:::process
        GenPDF -->|Raw File| CalcHash[Calculate SHA-256 Hash]:::process
        CalcHash -->|Hash| Sign[Digital Signature with Inst. Key]:::process
        Sign --> StoreRec[Store Certificate Record]:::process
    end

    %% STORAGE BLOCK
    subgraph StorageBlock [IMMUTABLE STORAGE LAYER]
        Database[Relational Database<br/>(Student Metadata, Hash)]:::storage
        IPFS[Decentralized Ledger / IPFS<br/>(Encrypted PDF, Transaction Hash)]:::storage
    end
    StoreRec -->|Link Records| StorageBlock

    %% STAGE 2: VERIFICATION (Public User)
    subgraph VerificationStage [STAGE 2: VERIFICATION]
        Public[Public User / Employer]:::public -->|Method A| Upload[Upload Certificate PDF]:::process
        Public -->|Method B| ScanQR[Scan Certificate QR Code]:::process
        
        Upload --> backend[Backend Receives Certificate]:::process
        ScanQR --> backend
        
        backend --> Extract[Extract Information <br/>(via OCR / Metadata)]:::process
        Extract --> Compare[Compare with Stored Record]:::process
        Compare --> Check[Check SHA-256 Hash / Digital Signature]:::process
        Check --> Tamper[Tamper Analysis <br/>(Matching Hash = Integrous)]:::process
    end

    %% Verification Connections
    StorageBlock -.->|Retrieve Hash| Compare
    StorageBlock -.->|Verify Signature| Check

    %% Final Outcome
    Tamper --> Verified{"Is Valid?"}
    Verified -- "YES" --> ResultValid[✅ VERIFIED]:::final_valid
    Verified -- "NO" --> ResultFlagged[❌ FLAGGED]:::final_flag
