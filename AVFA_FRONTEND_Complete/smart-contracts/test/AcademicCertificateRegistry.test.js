const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AcademicCertificateRegistry", function () {
  let registry, owner, university, verifier;

  beforeEach(async function () {
    [owner, university, verifier] = await ethers.getSigners();
    const Registry = await ethers.getContractFactory("AcademicCertificateRegistry");
    registry = await Registry.deploy();
    await registry.waitForDeployment();

    // Authorize University
    await registry.authorizeInstitution(university.address, "National Institute of Technology", "NIT-2026");
  });

  it("Should allow authorized university to issue a certificate", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("VANSH_GUPTA_CERT_2026"));
    const certNum = "CERT-2026-DA3A5BFC";

    await registry.connect(university).issueCertificate(hash, certNum);

    const [exists, isValid, isRevoked] = await registry.verifyCertificate(certNum);
    expect(exists).to.equal(true);
    expect(isValid).to.equal(true);
    expect(isRevoked).to.equal(false);
  });

  it("Should prevent unauthorized wallets from issuing certificates", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("UNAUTHORIZED_CERT"));
    const certNum = "CERT-2026-FAKE0001";

    await expect(
      registry.connect(verifier).issueCertificate(hash, certNum)
    ).to.be.revertedWith("AVFA: Caller is not an accredited issuing institution");
  });

  it("Should allow authorized university to revoke a certificate", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("SAMPLE_REVOKE_CERT"));
    const certNum = "CERT-2026-REV0001";

    await registry.connect(university).issueCertificate(hash, certNum);
    await registry.connect(university).revokeCertificate(certNum, "Administrative prerequisite audit failed");

    const [exists, isValid, isRevoked, , , , reason] = await registry.verifyCertificate(certNum);
    expect(exists).to.equal(true);
    expect(isValid).to.equal(false);
    expect(isRevoked).to.equal(true);
    expect(reason).to.equal("Administrative prerequisite audit failed");
  });
});
