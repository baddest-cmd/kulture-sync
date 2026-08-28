# Technical architecture and decolonial ML audit

Mathematical framework, system design, and socio-technical audit for the KultureSync taskmaster agent.

## 1. Mathematical framework

### Algorithmic flattening and the inversion problem
Mainstream streaming algorithms often compress local music expressions into global umbrella genres, such as labeling Amapiano or Gqom as generic World Music or Afrobeats.

Formally, let $B$ represent a local South African subgenre, $M$ represent a song's musical features, and $C$ represent the global classification context. Because global recommenders optimize for international audiences:
$$P(B \mid M, C) \neq P(B \mid M)$$

The global context $C$ acts as a confounder that reduces the posterior probability of identifying local subgenres.

### Cultural context tax ($\tau_c$)
To measure the cost of algorithmic flattening, we define the Cultural Context Tax as:
$$\tau_c = \text{popularity} \times \delta$$

Here, $\delta$ is a localized friction coefficient (such as $\delta = 1.25$ for local subgenres on metered networks). KultureSync isolates this tax by routing classification through a Causal Alignment Framing Layer (CAFL) powered by Gemini 3.5 Flash, which reduces redundant transfers and improves classification accuracy.

## 2. Socio-technical audit
A pilot survey in South Africa identified a Gauteng urban selection bias ($N=152$).

To avoid reinforcing geographic inequities through unverified automation, KultureSync adds a human-in-the-loop checkpointing graph. When the background agent detects a metered cellular connection where data rates average R85 to R120 per GB, it raises an ADK `NodeInterruptedError` and pauses. This prevents background syncs from consuming mobile data allowances unexpectedly.

## 3. Scale boundaries and production roadmap

### Interactive sync vs. bulk processing
* Interactive tier (under 500 tracks): The agent runs in real time with Gemini 3.5 Flash structured outputs, sub-second responses, and Firestore state checkpoints.
* Bulk migration tier (over 5,000 tracks): The production roadmap decouples execution from HTTP requests using Google Cloud Tasks and the Gemini Batch API. This avoids rate limits, reduces token costs by 50%, and provides dedicated execution leases for large library migrations.
