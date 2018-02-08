pragma solidity ^0.4.18;

import "strings.sol";

contract Nipopow {
  using strings for *; 

  // Access header data, by hash.
  // mapping (bytes32 => Header) blockById;
  mapping (bytes32 => bool) curProofMap;
  mapping (uint => uint) levelCounter;

  // Headers of the best proof.
  // Stores the hashes of the best proof.
  bytes32[] best_proof;

  // Ancestors of the best proof. Used for the calculation of the predicate.
  bytes32[] ancestors;
  // Update ancestors variable.
  // Mapping that marks the visited blocks when traversing the graphs.
  mapping (bytes32 => bool) visitedBlock;

  // Stores the block precedence in the proofs.
  // For example: Given proof [1, 2, 3] we have 3 -> 2, 2 -> 1.
  // Used for preventing filling the blockDAG with duplicates.
  mapping (bytes32 => mapping(bytes32 => bool)) blockPrecedence;
  // Stores DAG of blocks.
  mapping (bytes32 => bytes32[]) blockDAG;

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

  function add_to_dag(bytes32 hash_prev, bytes32 hash_cur) internal {
    if (!blockPrecedence[hash_prev][hash_cur]) {
      blockPrecedence[hash_prev][hash_cur] = true;

      blockDAG[hash_prev].length++;
      blockDAG[hash_prev][blockDAG[hash_prev].length - 1] = hash_cur;
    }
  }

  function ancestors_traversal(bytes32 current_block) internal {
    ancestors.length++;
    ancestors[ancestors.length - 1] = current_block;
    visitedBlock[current_block] = true;

    for (uint i = 0; i < blockDAG[current_block].length; i++) {
      if (!visitedBlock[blockDAG[current_block][i]]) {
        ancestors_traversal(blockDAG[current_block][i]);
      }
    }
  }

  function update_ancestors(bytes32 current_block) internal {
    ancestors_traversal(current_block);

    // Clear visitedBlock map.
    for (uint i = 0; i < ancestors.length; i++) {
      visitedBlock[ancestors[i]] = false;
    }
  }

  /* Clears the mapping of the submitted proof */
  function clear_hashmap(bytes32[] headers) internal {
    for (uint i = 0; i < headers.length; i++) {
      curProofMap[headers[i]] = false;
    }
  }

  /* // Used only for testing.
  function store_proof_in_map(bytes32[4][] proof) public {
    for (uint i = 0; i < proof.length; i++) {
      curProofMap[hash_header(proof[i])] = true;
    }
  } */

  /*// Hash the header using double SHA256 
  function hash_header(bytes32[4] header) internal returns(bytes32) {
    // Compute the hash of 112-byte header.
    var s = new string(112);
    uint sptr;
    uint hptr;
    assembly { sptr := add(s, 32) }
    assembly { hptr := add(header, 0) }
    memcpy(sptr, hptr, 112);
    return sha256(sha256(s));
  }*/

  function get_lca(bytes32[] cur_proof) internal returns(uint, uint) {
    bytes32 lca_hash;

    uint b_lca = 0;
    uint c_lca = 0;
    for (uint i = 0; i < best_proof.length; i++) {
      if (curProofMap[best_proof[i]]) {
        b_lca = i;
        lca_hash = best_proof[i];
        break;
      }
    }

    // Get the index of lca in the current_proof.
    for (i = 0; i < cur_proof.length; i++) {
      if (lca_hash == cur_proof[i]) {
        c_lca = i;
        break;
      }
    }
    return (b_lca, c_lca);
  }

  // TODO: Implement the O(log(max_level)) algorithm.
  function get_level(bytes32 hashed_header) internal returns(uint256) {
    uint256 hash = uint256(hashed_header);

    for (uint i = 0; i <= 255; i++) {
      // Change endianess.
      uint pow = (i/8) * 8 + 8 - (i % 8) - 1;
      uint256 k = 2 ** pow;
      if ((hash & k) != 0) {
        return uint8(i);
      }
    }
    return 0;
  }

  function best_arg(bytes32[] proof, uint al_index) public returns(uint256) {
    uint max_level = 0;
    uint256 max_score = 0;
    uint cur_level = 0;

    // Count the frequency of the levels.
    for (uint i = 0; i < al_index; i++) {
      cur_level = get_level(proof[i]);
      levelCounter[cur_level]++;

      if (max_level < cur_level) {
        max_level = cur_level;
      }
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

  function compare_proofs(bytes32[] cur_proof) public returns(bool) {
    if (!submitted_proof) {
      submitted_proof = true;
      return true;
    }
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

  function submit_nipopow(bytes32[] cur_proof, bytes32[] hash_interlinks,
    bytes32[] siblings, uint8[] merkle_branch_length, uint8[] merkle_indices) public returns(bool) {

    uint ptr = 0; // Index of the current sibling
    curProofMap[cur_proof[0]] = true;
    for (uint i = 1; i < cur_proof.length; i++) {
      curProofMap[cur_proof[i]] = true;
      // Add to block precedence to the blockDAG.
      add_to_dag(cur_proof[i - 1], cur_proof[i]);

      require(merkle_branch_length[i] <= 5);
      require(merkle_indices[i] <= 32);

      // Copy siblings.
      bytes32[] memory _siblings = new bytes32[](merkle_branch_length[i]);
      for (uint8 j = 0; j < merkle_branch_length[i]; j++) _siblings[j] = siblings[ptr+j];
      ptr += merkle_branch_length[i];

      // Verify the merkle tree proof
      verify_merkle(hash_interlinks[i - 1], cur_proof[i], merkle_indices[i], _siblings);
    }

    bool is_better_proof = false;
    if (compare_proofs(cur_proof)) {
      is_better_proof = true;
      best_proof = cur_proof;
    }
    // We don't need to store the map.
    clear_hashmap(cur_proof);
    // Update the ancestors.
    update_ancestors(best_proof[0]);
    return is_better_proof;
  }

  // Returns the value of the predicate. {Undefined -> -1, True -> 1, False -> 0}.
  function predicate(/* params */) public returns(uint8) {
    // Use the ancestors field to calculate the predicate.
  }
}
