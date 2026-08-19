// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title InstitutionGovernance
 * @dev Multi-signature governance module for regulatory accreditation of issuing bodies.
 */
contract InstitutionGovernance {
    address public admin;
    mapping(address => bool) public guardians;

    event GuardianAdded(address indexed guardian);
    event GuardianRemoved(address indexed guardian);

    modifier onlyAdmin() {
        require(msg.sender == admin, "AVFA-Gov: Caller is not admin");
        _;
    }

    constructor() {
        admin = msg.sender;
        guardians[msg.sender] = true;
    }

    function addGuardian(address _guardian) external onlyAdmin {
        guardians[_guardian] = true;
        emit GuardianAdded(_guardian);
    }

    function removeGuardian(address _guardian) external onlyAdmin {
        guardians[_guardian] = false;
        emit GuardianRemoved(_guardian);
    }
}
