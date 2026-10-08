# Search Strategies

## Best-of-N
Generate N independent candidates and select using a verifier. Baseline for test-time compute.

## Self-refinement
Feed verifier feedback into a new candidate.

## Beam search
Maintain multiple partial candidates and expand them.

## MCTS
Only call the implementation MCTS after defining selection, expansion, simulation and backpropagation. The included lightweight `mcts_like` implementation is deliberately conservative; replace it with a formal implementation when you study the algorithm.
