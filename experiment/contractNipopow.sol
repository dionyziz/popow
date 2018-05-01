pragma solidity ^0.4.18;

//import "strings.sol";

contract Nipopow {
  //using strings for *;

  // TODO: Set the genesis_block. Is it going to be constant?
  bytes32 genesis_block;
  // Collateral to pay.
  uint constant z = 100000000000000000; // 0.1 eth

  // Nipopow proof.
  struct Nipopow {
    mapping (bytes32 => bool) curProofMap;
    mapping (uint => uint) levelCounter;
    mapping (bytes32 => bool) visitedBlock;
    // Stores the block precedence in the proofs.
    // For example: Given proof [1, 2, 3] we have 3 -> 2, 2 -> 1.
    // Used for preventing filling the blockDAG with duplicates.
    mapping (bytes32 => mapping(bytes32 => bool)) blockPrecedence;
    // Stores DAG of blocks.
    mapping (bytes32 => bytes32[]) blockDAG;
    // Stores the hashes of the block headers of the best proof.
    bytes32[] best_proof;
    // Ancestors of the best proof. Used for the calculation of the predicate.
    bytes32[] ancestors;
  }

  struct Event {
    address author;
    uint expire;
    Nipopow proof;
  }

  // The key is the key value used for the predicate. In our case
  // the block header hash.
  mapping (bytes32 => Event) events;
  mapping (bytes32 => bool) finalized_events;

  // Security parameters.
  uint constant m = 15;
  uint constant k = 6;

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

  function add_proof_to_dag(Nipopow storage nipopow, bytes32[] proof) internal {
    for (uint i = 1; i < proof.length; i++) {
      if (!nipopow.blockPrecedence[proof[i - 1]][proof[i]]) {
        nipopow.blockPrecedence[proof[i - 1]][proof[i]] = true;
        nipopow.blockDAG[proof[i - 1]].push(proof[i]);
      }
    }
  }

  function ancestors_traversal(Nipopow storage nipopow, bytes32 current_block) internal {
    nipopow.ancestors.push(current_block);
    nipopow.visitedBlock[current_block] = true;

    for (uint i = 0; i < nipopow.blockDAG[current_block].length; i++) {
      if (!nipopow.visitedBlock[nipopow.blockDAG[current_block][i]]) {
        ancestors_traversal(nipopow, nipopow.blockDAG[current_block][i]);
      }
    }
  }

  function update_ancestors(Nipopow storage nipopow, bytes32 current_block) internal {
    ancestors_traversal(nipopow, current_block);

    // Clear visitedBlock map.
    for (uint i = 0; i < nipopow.ancestors.length; i++) {
      nipopow.visitedBlock[nipopow.ancestors[i]] = false;
    }
  }

  function get_lca(Nipopow storage nipopow, bytes32[] c_proof)
    internal returns(uint, uint) {

    for (uint i = 0; i < c_proof.length; i++) {
      nipopow.curProofMap[c_proof[i]] = true;
    }

    bytes32 lca_hash;

    uint b_lca = 0;
    uint c_lca = 0;
    for (i = 0; i < nipopow.best_proof.length; i++) {
      if (nipopow.curProofMap[nipopow.best_proof[i]]) {
        b_lca = i;
        lca_hash = nipopow.best_proof[i];
        break;
      }
    }

    // Get the index of lca in the current_proof.
    for (i = 0; i < c_proof.length; i++) {
      if (lca_hash == c_proof[i]) {
        c_lca = i;
        break;
      }
    }

    // Clear the map. We don't need it anymore.
    for (i = 0; i < c_proof.length; i++) {
      nipopow.curProofMap[c_proof[i]] = false;
    }

    return (b_lca, c_lca);
  }

  // TODO: Implement the O(log(max_level)) algorithm.
  function get_level(bytes32 hashed_header) internal returns(uint256) {
    uint256 hash = uint256(hashed_header);

    for (uint i = 0; i <= 255; i++) {
      // Change endianess.
      uint pow = (i/8) * 8 + 8 - (i % 8) - 1;
      uint256 mask = 2 ** pow;
      if ((hash & mask) != 0) {
        return uint8(i);
      }
    }
    return 0;
  }

  // TODO: Check if anchored.
  function best_arg(Nipopow storage nipopow, bytes32[] proof, uint al_index)
    internal returns(uint256) {
    uint max_level = 0;
    uint256 max_score = 0;
    uint cur_level = 0;

    // Count the frequency of the levels.
    for (uint i = 0; i < al_index; i++) {
      cur_level = get_level(proof[i]);
      nipopow.levelCounter[cur_level]++;

      if (max_level < cur_level) {
        max_level = cur_level;
      }
    }

    for (i = 0; i <= max_level; i++) {
      uint256 cur_score = uint256(nipopow.levelCounter[i] * 2 ** i);
      if (nipopow.levelCounter[i] >= m && cur_score > max_score) {
        max_score = nipopow.levelCounter[i] * 2 ** i;
      }
      // clear the map.
      nipopow.levelCounter[i] = 0;
    }
    return max_score;
  }

  function compare_proofs(Nipopow storage nipopow,
    bytes32[] contesting_proof) internal returns(bool) {
    uint proof_lca_index;
    uint contesting_lca_index;
    (proof_lca_index, contesting_lca_index) = get_lca(nipopow, contesting_proof);
    return best_arg(nipopow, contesting_proof, contesting_lca_index) >
           best_arg(nipopow, nipopow.best_proof, proof_lca_index);
  }

  function verify_merkle(bytes32 roothash, bytes32 leaf, uint8 mu,
    bytes32[] siblings) constant internal {
    bytes32 h = leaf;
    for (uint i = 0; i < siblings.length; i++) {
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

  function validate_interlink(bytes32[] proof, bytes32[] hash_interlinks,
    bytes32[] siblings, uint8[] merkle_branch_length, uint8[] merkle_indices) internal {
    uint ptr = 0; // Index of the current sibling
    for (uint i = 1; i < proof.length; i++) {

      require(merkle_branch_length[i] <= 5);
      require(merkle_indices[i] <= 32);

      // Copy siblings.
      bytes32[] memory _siblings = new bytes32[](merkle_branch_length[i]);
      for (uint8 j = 0; j < merkle_branch_length[i]; j++) _siblings[j] = siblings[ptr+j];
      ptr += merkle_branch_length[i];

      // Verify the merkle tree proof
      verify_merkle(hash_interlinks[i - 1], proof[i], merkle_indices[i], _siblings);
    }
  }

  // Simple proofs that checks for the inclusion of the block of
  // interest in the proof.
  function predicate(bytes32[] ancestors, bytes32 block_of_interest)
    internal returns (bool) {
      for (uint i = 0; i < ancestors.length; i++) {
        if (ancestors[i] == block_of_interest) {
          return true;
        }
      }
    return false;
  }

  // Verify the first proof.
  function verify(bytes32[] proof, bytes32[] hash_interlinks,
    bytes32[] siblings, uint8[] merkle_branch_length, uint8[] merkle_indices,
    bytes32 block_of_interest) public returns(bool) {

     //Throws if invalid.
    validate_interlink(proof, hash_interlinks, siblings, merkle_branch_length,
      merkle_indices);

    return predicate(proof, block_of_interest);
  }

  function verify(Nipopow storage proof, bytes32[] contesting_proof,
    bytes32[] hash_interlinks, bytes32[] siblings,
    uint8[] merkle_branch_length, uint8[] merkle_indices,
    bytes32 block_of_interest) internal returns(bool) {

      // Throws if invalid.
    validate_interlink(contesting_proof, hash_interlinks, siblings,
      merkle_branch_length, merkle_indices);

    add_proof_to_dag(proof, contesting_proof);

    if (compare_proofs(proof, contesting_proof)) {
      proof.best_proof = contesting_proof;
    }

    update_ancestors(proof, proof.best_proof[0]);

    // Use ancestors.
    return predicate(proof.ancestors, block_of_interest);
  }

  // TODO: Deleting a mapping is impossible without knowing
  // beforehand all the keys of the mapping. That costs gas
  // and it may be in our favor to never delete this stored memory.
  function submit_event_proof(bytes32[] proof, bytes32[] hash_interlinks,
    bytes32[] siblings, uint8[] merkle_branch_length, uint8[] merkle_indices,
    bytes32 block_of_interest) public payable returns(bool) {

    if (msg.value < z) {
      return false;
    }

    verify(proof, hash_interlinks, siblings, merkle_branch_length,
        merkle_indices, block_of_interest);

    /*if (events[block_of_interest].expire == 0 &&  
      verify(proof, hash_interlinks, siblings, merkle_branch_length,
        merkle_indices, block_of_interest)) {
      events[block_of_interest].expire = block.number + k;
      events[block_of_interest].author = msg.sender;
      events[block_of_interest].proof.best_proof = proof;
      add_proof_to_dag(events[block_of_interest].proof, proof);
      return true;
    }*/
    return false;
  }

  function finalize_event(bytes32 block_of_interest) public returns(bool) {
    if (events[block_of_interest].expire == 0 ||
      block.number < events[block_of_interest].expire) {
      return false;
    }
    finalized_events[block_of_interest] = true;
    address author = events[block_of_interest].author;
    events[block_of_interest].expire = 0;
    author.transfer(z);

    return true;
  }

  function submit_contesting_proof(bytes32[] proof, bytes32[] hash_interlinks,
    bytes32[] siblings, uint8[] merkle_branch_length, uint8[] merkle_indices,
    bytes32 block_of_interest) public returns(bool) {
    if (events[block_of_interest].expire < block.number) {
      return false;
    }

    if (!verify(events[block_of_interest].proof, proof,
      hash_interlinks, siblings, merkle_branch_length, merkle_indices, block_of_interest)) {
      events[block_of_interest].expire = 0;
      msg.sender.transfer(z);
    }

    return true;
  }

  function event_exists(bytes32 block_header) public returns(bool) {
    return finalized_events[block_header];
  }
}
