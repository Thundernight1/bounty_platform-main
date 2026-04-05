const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BugBounty Core Workflow", function () {
    let bugBounty, owner, committee1, committee2, reporter1;
    let committeeMembers;
    const requiredApprovals = 2;

    beforeEach(async function () {
        [owner, committee1, committee2, reporter1] = await ethers.getSigners();
        committeeMembers = [committee1.address, committee2.address];
        const BugBountyFactory = await ethers.getContractFactory("BugBounty");
        bugBounty = await BugBountyFactory.deploy(committeeMembers, requiredApprovals);
        // Fund the contract for payouts
        await owner.sendTransaction({ to: bugBounty.target, value: ethers.parseEther("10.0") });
    });

    it("Should successfully process a bug report from submission to payout", async function () {
        // 1. Submit a Bug
        const description = "Critical vulnerability in authentication";
        const severity = 8;
        await expect(bugBounty.connect(reporter1).submitBug(description, severity))
            .to.emit(bugBounty, "BugReportSubmitted")
            .withArgs(1, reporter1.address, description, severity);

        // 2. Approve the Bug
        await expect(bugBounty.connect(owner).approveBug(1))
            .to.not.be.reverted;
        const report = await bugBounty.reports(1);
        expect(report.approved).to.be.true;

        // 3. Request a Payout
        await expect(bugBounty.connect(owner).requestPayout(1))
            .to.emit(bugBounty, "PayoutRequested");
        const payout = await bugBounty.payouts(1);
        expect(payout.recipient).to.equal(reporter1.address);

        // 4. Approve the Payout
        await expect(bugBounty.connect(committee1).approvePayout(1))
            .to.emit(bugBounty, "PayoutApproved");
        await expect(bugBounty.connect(committee2).approvePayout(1))
            .to.emit(bugBounty, "PayoutApproved");

        // 5. Execute the Payout
        const initialBalance = await ethers.provider.getBalance(reporter1.address);
        await expect(bugBounty.connect(owner).executePayout(1))
            .to.emit(bugBounty, "PayoutExecuted");
        const finalBalance = await ethers.provider.getBalance(reporter1.address);

        expect(finalBalance).to.be.gt(initialBalance);
        const finalReport = await bugBounty.reports(1);
        expect(finalReport.paid).to.be.true;
    });
});
