const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BugBounty", function () {
    let bugBounty, owner, committee1, committee2, reporter1, otherAccount;
    let committeeMembers;
    const requiredApprovals = 2;

    beforeEach(async function () {
        [owner, committee1, committee2, reporter1, otherAccount] = await ethers.getSigners();
        committeeMembers = [committee1.address, committee2.address];
        const BugBountyFactory = await ethers.getContractFactory("BugBounty");
        bugBounty = await BugBountyFactory.deploy(committeeMembers, requiredApprovals);
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await bugBounty.owner()).to.equal(owner.address);
        });

        it("Should set up committee members correctly", async function () {
            expect(await bugBounty.isCommitteeMember(committee1.address)).to.be.true;
            expect(await bugBounty.isCommitteeMember(committee2.address)).to.be.true;
            expect(await bugBounty.committeeMemberCount()).to.equal(2);
            expect(await bugBounty.requiredApprovals()).to.equal(requiredApprovals);
        });
    });

    describe("Committee Management", function () {
        it("Should allow the owner to add and remove committee members", async function () {
            await bugBounty.connect(owner).addCommitteeMember(otherAccount.address);
            expect(await bugBounty.isCommitteeMember(otherAccount.address)).to.be.true;
            expect(await bugBounty.committeeMemberCount()).to.equal(3);

            await bugBounty.connect(owner).removeCommitteeMember(committee1.address);
            expect(await bugBounty.isCommitteeMember(committee1.address)).to.be.false;
            expect(await bugBounty.committeeMemberCount()).to.equal(2);
        });

        it("Should prevent removing a committee member if it drops below required approvals", async function () {
            await expect(bugBounty.connect(owner).removeCommitteeMember(committee1.address))
                .to.be.revertedWith("Cannot have fewer members than required approvals");
        });

        it("Should allow the owner to set required approvals", async function () {
            await bugBounty.connect(owner).setRequiredApprovals(1);
            expect(await bugBounty.requiredApprovals()).to.equal(1);
        });

        it("Should prevent setting required approvals to 0 or more than committee members", async function () {
            await expect(bugBounty.connect(owner).setRequiredApprovals(0)).to.be.revertedWith("Required approvals must be greater than zero");
            await expect(bugBounty.connect(owner).setRequiredApprovals(3)).to.be.revertedWith("Cannot require more approvals than committee members");
        });
    });

    describe("Pausable Functionality", function () {
        it("Should allow the owner to pause and unpause the contract", async function () {
            await bugBounty.connect(owner).pause();
            expect(await bugBounty.paused()).to.be.true;
            await bugBounty.connect(owner).unpause();
            expect(await bugBounty.paused()).to.be.false;
        });

        it("Should prevent actions when paused", async function () {
            await bugBounty.connect(owner).pause();
            await expect(bugBounty.connect(reporter1).submitBug("A bug", 5)).to.be.revertedWithCustomError(bugBounty, "EnforcedPause");
        });
    });

    describe("Dispute Resolution", function () {
        beforeEach(async function () {
            await bugBounty.connect(reporter1).submitBug("CSRF issue", 6);
        });

        it("Should allow a reporter to raise a dispute", async function () {
            await expect(bugBounty.connect(reporter1).raiseDispute(1, "Unfairly rejected"))
                .to.emit(bugBounty, "DisputeRaised");
        });

        it("Should allow the owner to resolve a dispute and approve the report", async function () {
            await bugBounty.connect(reporter1).raiseDispute(1, "Valid issue");
            await expect(bugBounty.connect(owner).resolveDispute(1, true)).to.emit(bugBounty, "DisputeResolved");
            const report = await bugBounty.reports(1);
            expect(report.approved).to.be.true;
        });
    });
});
