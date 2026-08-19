const hre = require("hardhat");

async function main() {
  console.log("=== Deploying AVFA Smart Contracts ===");

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);

  const Registry = await hre.ethers.getContractFactory("AcademicCertificateRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();

  const registryAddress = await registry.getAddress();
  console.log(`[SUCCESS] AcademicCertificateRegistry deployed to: ${registryAddress}`);

  const Governance = await hre.ethers.getContractFactory("InstitutionGovernance");
  const governance = await Governance.deploy();
  await governance.waitForDeployment();

  const govAddress = await governance.getAddress();
  console.log(`[SUCCESS] InstitutionGovernance deployed to: ${govAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
