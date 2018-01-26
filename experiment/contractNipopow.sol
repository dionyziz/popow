pragma solidity ^0.4.19;

import "strings.sol";

contract Nipopow {
    using strings for *;
    // Header is stored as 3*bytes32, so 112 bytes
    // 
    // The first 80 bytes are the ordinary bitcoin header
    // The next 32 bytes are the 
    
    struct Header { bytes32    hashInterlink;
		    bytes32[3] bitcoinHeader; }

    struct Proof {
    }

    function hashHeader(Header h) internal pure {
	// Hash the header using SHA256 twice
	
    }

    // Access header data, by hash
    mapping (bytes32 => Header) mapHeader; 

    event LogInit();
    event LogBytes32(string name, bytes32 b);
    event LogUint8(string name, uint8 b);

    function Nipopow() public {
	// Convert nBits to constant?
    }

    function memcpy(uint dest, uint src, uint len) private {
	// Copy word-length chunks while possible
	for(; len >= 32; len -= 32) {
	    assembly {
		mstore(dest, mload(src))
	    }
	    dest += 32;
	    src += 32;
	}

	// Copy remaining bytes
	uint mask = 256 ** (32 - len) - 1;
	assembly {
	    let srcpart := and(mload(src), not(mask))
	    let destpart := and(mload(dest), mask)
	    mstore(dest, or(destpart, srcpart))
	}
    }

    function verify_merkle(bytes32 roothash, bytes32 leaf, uint8 mu, bytes32[] memory siblings) constant internal {
	bytes32 h = leaf;
	for (var i = 0; i < siblings.length; i++) {
	    uint8 bit = mu & 0x1;
	    if (bit == 1) {
		h = sha256(sha256(siblings[siblings.length-i-1], h));
	    } else {
		h = sha256(sha256(h, siblings[siblings.length-i-1]));
	    }
	    mu >>= 1;
	}
	require(h == roothash);
    }

    function submit_nipopow(bytes32[4][] headers, bytes32[] siblings) public {
	uint ptr = 0; // Index of the current sibling
	bytes32[4] memory header = headers[0];
	bytes32 hashInterlink = header[0];
	
	// TODO: check the first header?

	for (uint i = 1; i < 1; i++) {
	    header = headers[i];
	 
	    // Compute the hash of 112-byte header
	    var s = new string(112);
	    uint sptr;
	    uint hptr;
	    assembly { sptr := add(s, 32) }
	    assembly { hptr := add(header, 0) }
	    memcpy(sptr, hptr, 112);
	    bytes32 b = sha256(sha256(s));

	    // Length of merkle branch is 2nd byte, index is 1st byte
	    var branch_length = uint8((header[3] >> 8) & 0xff);
	    var mu            = uint8((header[3] >> 0) & 0xff);
	    require(branch_length <= 5);
	    require(mu <= 32);

	    // Copy siblings
	    bytes32[] memory _siblings = new bytes32[](branch_length);
	    for (uint8 j = 0; j < branch_length; j++) _siblings[j] = siblings[ptr+j];
	    ptr += branch_length;

	    // Verify the merkle tree proof
	    verify_merkle(hashInterlink, b, mu, _siblings);

	    // Store the header indexed by its hash
	    mapHeader[b].hashInterlink = header[0];
	    mapHeader[b].bitcoinHeader[0] = header[1];
	    mapHeader[b].bitcoinHeader[1] = header[2];
	    mapHeader[b].bitcoinHeader[2] = header[3];

	    // Update hash interlink
	    hashInterlink = header[0];

	    // Log output
	    //LogBytes32("header[0] hash", b);
	}
    }
}
