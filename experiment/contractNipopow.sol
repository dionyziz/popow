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

    function submitProof(bytes32[4][] headers) public {
	for (var i = 0; i < headers.length; i++) {
	    bytes32[4] memory header = headers[i];
	 
	    // Compute the hash of 112-byte header
	    var s = new string(112);
	    uint sptr;
	    uint hptr;
	    assembly { sptr := add(s, 32) }
	    assembly { hptr := add(header, 0) }
	    memcpy(sptr, hptr, 112);
	    bytes32 b = sha256(s);

	    // Store the header indexed by hash
	    mapHeader[b].hashInterlink = header[0];
	    mapHeader[b].bitcoinHeader[0] = header[1];
	    mapHeader[b].bitcoinHeader[1] = header[2];
	    mapHeader[b].bitcoinHeader[2] = header[3];

	    LogBytes32("header[0] hash", b);
	}
	    //s.concat(headers[0][1].toSliceB32());
	//s.concat(headers[0][2].toSliceB32());
	//s.concat(headers[0][3].toSliceB32());
	//s.len = 12
	//bytes32 b = sha256(s.toString()); // sha256(sha256(s.toString()));
    }
}
