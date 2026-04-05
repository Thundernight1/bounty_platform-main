// scripts/deploy.js
const hre = require("hardhat");

async function main() {
  // We get the signers
  const [deployer, committee1, committee2] = await hre.ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);

  const committeeMembers = [committee1.address, committee2.address];
  const requiredApprovals = 2;

  // We get the contract to deploy
  const BugBounty = await hre.ethers.getContractFactory("BugBounty");
  const bugBounty = await BugBounty.deploy(committeeMembers, requiredApprovals);

  await bugBounty.waitForDeployment();


  console.log("BugBounty deployed to:", await bugBounty.getAddress());
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
