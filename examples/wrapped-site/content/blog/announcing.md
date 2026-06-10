# Announcing Acme Widget 2.0

We are glad to ship a major release.
Highlights:

1. **Faster:** up to 3x throughput on large batches.
2. **Smaller:** the install footprint dropped by half.
3. **Friendlier:** clearer errors and a new quickstart.

The math checks out: if each request used to take $t$ seconds, batches of $n$ now finish
in roughly $\frac{n \cdot t}{3}$.

Thanks to everyone who contributed.
See the [installation guide](/docs/installation/) to upgrade.
