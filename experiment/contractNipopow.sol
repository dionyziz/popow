pragma solidity ^0.4.18;

import "strings.sol";

contract Nipopow {
  using strings for *;
  // Header is stored as 3*bytes32, so 112 bytes
  // 
  // The first 80 bytes are the ordinary bitcoin header
  // The next 32 bytes are the 

  struct Header { bytes32 hashInterlink;
    bytes32[3] bitcoinHeader; }

  // TODO: Use the proof struct.
  struct Proof {
    Header[] pi;
    Header[] chi;
  }

  // Access header data, by hash.
  mapping (bytes32 => Header) mapHeader;
  mapping (uint => uint) levelCounter;

  // Headers of the best proof.
  bytes32[4][] best_proof;

  // Security parameters.
  // TODO: Double-check the parameter values.
  uint m = 15;
  uint k = 6;

  // Boolean for the first submitted proof.
  bool submitted_proof;

  event LogInit();
  event LogBytes32(string name, bytes32 b);
  event LogUint8(string name, uint8 b);

  function memcpy(uint dest, uint src, uint len) private {
    // Copy word-length chunks while possible
    for(; len >= 32; len -= 32) {
      assembly {
        mstore(dest, mload(src))
      }
      dest += 32;
      src += 32;
    }

    // Copy remaining bytes.
    uint mask = 256 ** (32 - len) - 1;
    assembly {
      let srcpart := and(mload(src), not(mask))
      let destpart := and(mload(dest), mask)
      mstore(dest, or(destpart, srcpart))
    }
  }

  function clear_hashmap(bytes32[4][] headers) internal {
    for (uint i = 0; i < headers.length; i++) {
      bytes32 b = hash_header(headers[i]);
      // TODO: Is 0 the default value of the byte?
      mapHeader[b].hashInterlink = 0;
      mapHeader[b].bitcoinHeader[0] = 0;
      mapHeader[b].bitcoinHeader[1] = 0;
      mapHeader[b].bitcoinHeader[2] = 0;
    }
  }

  /* Used only for testing.
  function store_proof_in_map(bytes32[4][] proof) internal {
    for (uint i = 0; i < proof.length; i++) {
      store_header(proof[i], hash_header(proof[i]));
    }
  }*/

  function store_header(bytes32[4] header, bytes32 hash) internal {
    mapHeader[hash].hashInterlink = header[0];
    mapHeader[hash].bitcoinHeader[0] = header[1];
    mapHeader[hash].bitcoinHeader[1] = header[2];
    mapHeader[hash].bitcoinHeader[2] = header[3];
  }

  // Hash the header using double SHA256 
  function hash_header(bytes32[4] header) internal returns(bytes32) {
    // Compute the hash of 112-byte header.
    var s = new string(112);
    uint sptr;
    uint hptr;
    assembly { sptr := add(s, 32) }
    assembly { hptr := add(header, 0) }
    memcpy(sptr, hptr, 112);
    return sha256(sha256(s));
  }

  function get_lca(bytes32[4][] cur_proof) internal returns(uint, uint) {
    bytes32 lca_hash;
    bytes32 cur_hash;

    uint b_lca = 0;
    uint c_lca = 0;
    for (uint i = 0; i < best_proof.length; i++) {
      cur_hash = hash_header(best_proof[i]);
      // Different than the default value.
      if (mapHeader[cur_hash].hashInterlink != 0) {
        b_lca = i;
        lca_hash = cur_hash;
        break;
      }
    }

    // Get the index of lca in the current_proof.
    for (i = 0; i < cur_proof.length; i++) {
      cur_hash = hash_header(cur_proof[i]);
      if (cur_hash == lca_hash) {
        c_lca = i;
        break;
      }
    }
    return (b_lca, c_lca);
  }

  function get_level(bytes32[4] header) internal returns(uint8) {
    uint256 hash = uint256(hash_header(header));

    for (uint i = 0; i <= 255; i++) {
      uint256 k = 2 ** i;
      if ((hash & k) != 0) {
        return uint8(i);
      }
    }
    return 0;
  }

  function best_arg(bytes32[4][] proof, uint al_index) internal returns(uint256) {
    uint max_level = 255;
    uint256 max_score = 0;

    // Count the frequency of the levels.
    for (uint i = 0; i < al_index; i++) {
      levelCounter[get_level(proof[i])]++;
    }

    for (i = 0; i <= max_level; i++) {
      uint256 cur_score = uint256(levelCounter[i] * 2 ** i);
      if (levelCounter[i] >= m && cur_score > max_score) {
        max_score = levelCounter[i] * 2 ** i;
      }
      // clear the map.
      levelCounter[i] = 0;
    }
    return max_score;
  }

  // Initialise security parameters?
  function Nipopow() public {
    // Convert nBits to constant?
  }

  function compare_proofs(bytes32[4][] cur_proof) internal returns(bool) {
    var (b_lca, c_lca) = get_lca(cur_proof);
    return best_arg(cur_proof, c_lca) > best_arg(best_proof, b_lca);
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

  function submit_nipopow(bytes32[4][] headers, bytes32[] siblings) public returns(bool) {
    uint ptr = 0; // Index of the current sibling
    bytes32[4] memory header = headers[0];
    bytes32 hashInterlink = header[0];

    store_header(header, hash_header(header));

    for (uint i = 1; i < headers.length; i++) {
      header = headers[i];
      bytes32 b = hash_header(header);

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
      store_header(header, b);

      // Update hash interlink
      hashInterlink = header[0];

      // Log output
      //LogBytes32("header[0] hash", b);
    }

    // TODO: Last step of the verifier.

    bool better_proof;
    if (!submitted_proof) {
      better_proof = true;
      submitted_proof = true;
      best_proof = headers;
    } else if (compare_proofs(headers)) {
      better_proof = true;
      best_proof = headers;
    }

    // We don't need to store the map.
    clear_hashmap(headers);

    return better_proof;
  }
}
