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

  // Stores the indices of the LCA in the best and current proof. 
  struct LcaIndex {
    uint b_lca;
    uint c_lca;
  }

  // TODO: Use the proof struct.
  struct Proof {
    Header[] pi; 
    Header[] chi;
  }

  // Access header data, by hash.
  mapping (bytes32 => Header) mapHeader;

  // Headers of the best proof.
  bytes32[4][] best_proof;

  // Security parameters.
  // TODO: Double-check the parameter values.
  uint m = 15;
  uint k = 6;

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

      // Copy remaining bytes.
      uint mask = 256 ** (32 - len) - 1;
      assembly {
        let srcpart := and(mload(src), not(mask))
          let destpart := and(mload(dest), mask)
          mstore(dest, or(destpart, srcpart))
      }
    }
  }

  function clean_hashmap(bytes32[4][] headers) {
    for (uint i = 0; i < headers.length; i++) {
      bytes32 b = hashHeader(headers[i]);
      // TODO: Is 0 the default value of the byte?
      mapHeader[b].hashInterlink = 0;
      mapHeader[b].bitcoinHeader[0] = 0;
      mapHeader[b].bitcoinHeader[1] = 0;
      mapHeader[b].bitcoinHeader[2] = 0;
    }
  }

  // Hash the header using double SHA256 
  function hashHeader(bytes32[4] header) internal returns(bytes32) {
    // Compute the hash of 112-byte header
    var s = new string(112);
    uint sptr;
    uint hptr;
    assembly { sptr := add(s, 32) }
    assembly { hptr := add(header, 0) }
    memcpy(sptr, hptr, 112);
    return sha256(sha256(s));
  }

  function get_lca(bytes32[4][] cur_proof) public view returns(LcaIndex) {
    LcaIndex memory index;

    bytes32 lca_hash;
    bytes32 cur_hash;
    for (uint i = 0; i < best_proof.length; i++) {
      // Is the hashing unnecessary(expensive)?
      cur_hash = hashHeader(best_proof[i]);
      // Different than the default value.
      if (mapHeader[cur_hash].hashInterlink != 0) {
        index.b_lca = i;
        lca_hash = cur_hash;
        break;
      }
    }

    // Get the index of lca in the current_proof.
    for (i = 0; i < cur_proof.length; i++) {
      cur_hash = hashHeader(cur_proof[i]);
      if (cur_hash == lca_hash) {
        index.c_lca = i;
        break;
      }
    }
    return index;
  }

  // TODO: Implement.
  function get_level(bytes32[4] header) internal returns(uint8) {
    return 0;
  }

  function best_argument(bytes32[4][] proof, uint al_index) internal returns(uint256) {
    uint8 max_level = 255;
    uint256 max_score = 0;

    for (uint256 i = 0; i <= max_level; i++) {
      uint256 cur_score = 0;

      for (uint j = al_index - 1; j >= 0; j--) {
        if (get_level(proof[j]) >= i) {
          cur_score += uint256(1 << i);
        }

        if (cur_score == 0) {
          break; // Maximum level achieved.
        }
      }
      if (cur_score > max_score) {
        max_score = cur_score;
      }
    }
    return max_score;
  }

  function Nipopow() public {
    // Convert nBits to constant?
  }

  function compare_proofs(bytes32[4][] cur_proof) internal returns(bool) {
    LcaIndex memory lca_index = get_lca(cur_proof);
    return best_argument(cur_proof, lca_index.c_lca) >
      best_argument(best_proof, lca_index.b_lca);
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

    for (uint i = 1; i < headers.length; i++) {
      header = headers[i];
      bytes32 b = hashHeader(header);

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

    /*if (compare_proofs(headers)) {
      best_proof = headers;
      }*/

    // We don't need to store the map.
    clean_hashmap(headers);
  }
}
