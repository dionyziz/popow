Towards a “Partially synchronous” blockchain.
=====

Synchronous protocols have (perhaps implicitly) a parameter that depends on an estimate of the network’s delivery latency. In Bitcoin, this manifests mainly in the hardcoded “10 minute” target block time, which is used to adjust the puzzle difficulty.
 This time cannot be set too low, or else the blockchain will fail to converge. Users should not accept a transaction that turns out to be reversed. The time cannot be set too long, or else it takes too long to wait for block confirmations.


In distributed systems, a “partially synchronous” protocol guarantees safety and liveness, regardless of how long messages take (as long as they are bounded). A partially synchronous protocol would not depend on such an estimate, and thus would not feature any hard coded timeout parameters.


Why not simply remove the puzzle difficulty limit, and let miners choose their own difficulty limits? This would lead to the “high variance” attack where the adversary creates a long chain with very difficult blocks (this is the Bahack-style attack).


Actually, it is easy to show an impossibility result, which is that in a partially synchronous network, where the bound on message delay is not known and the total hashpower of the network is not known, it is not possible to guarantee safety (no double spends) and liveness.


However, our idea is to provide “per user” guarantees. We describe one protocol, Pi_blockchain, which does not have any timing parameters. However, when users interact with this protocol, i.e. with the ‘sendMoney(src,dst,amount,\Delta’)’ command, they include a parameter including their “estimate” \Delta’ of the delay \Delta. The system guarantees there are no double spends among transactions that are chosen with sufficiently high \Delta’ > \Delta. More conservative users can therefore accept payments at a “higher level” which therefore will resist double-spending even under more turbulent network conditions, while more risk-tolerant users can accept fast payments at lower levels.


How to implement PartialSynchronyCoin using the NiPoPow proofs
====

The NiPoPow data structure involves building an unbounded number of “layers” of blockchains, each with 2x the difficulty of the previous layer. However, so far, prior work has only considered the case where the “bottom” layer is chosen according to the same difficulty adjustment mechanism as in Bitcoin.


Our idea is to let miners choose their own “base difficulty” according to their local view.


We need to update the fork choice rule. Like in the ordinary case, we still need to choose a fork that is longer, however now we must compare forks that have different “base levels.”


The naive strategy would be to choose the fork that is longer at whatever is the “highest level”. But this is vulnerable to high variance attacks, similar to the problem with SPV proofs why it’s necessary to always have “m” samples.


For example, suppose you (the honest party) are presented with a fork that begins 1023 blocks behind our main chain. However, this fork switches to a difficult of 2^10 beyond our chain, and it contains only a single block at this difficulty level. Do we switch to it?


The solution to this problem is to only choose a longer “fork” if the longer fork contains at least m blocks beyond the fork point on some level.


Still TODO: Explanation of how to choose the “base difficulty” and what factors drive that