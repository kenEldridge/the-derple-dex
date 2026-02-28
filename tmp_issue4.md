# Research Note

## Metadata
- Date: 2026-02-20
- Topic: Melody as a Log-Derivative -- why songs survive key changes
- Core question: Is it accurate to say melody survives key changes because the cochlea operates in log-space and intervals are frequency ratios (preserved under multiplication)?
- Why this matters to me: This is the central argument of the blog post. If the claims are wrong or significantly oversimplified, the post is misleading.
- Timebox (minutes): 120
- Current confidence in my main view (0-100%): 65% -- the math is trivially correct, but the perceptual and biological claims need checking

## 1) Exploration (Divergent)
- What I currently think: Melody identity is preserved under key changes because the auditory system encodes pitch approximately logarithmically, making intervals (log-differences) invariant under the multiplicative shift of transposition.
- Key intuitions:
  - The k-cancels-in-kf2/kf1 math is trivially true -- the interesting question is whether the ear actually works this way
  - "Logarithmic" might be an oversimplification of the actual cochlear frequency map
  - "Intervals are ratios" might be more of a musical-context phenomenon than a universal perceptual law
- Candidate explanations (at least 3):
  1. The cochlea is log-scaled, intervals are ratios, transposition is a shift in log-space, derivative is invariant (the blog argument)
  2. Melody recognition relies more on contour (up/down pattern) than precise intervals, so the ratio story is only part of it
  3. The log approximation breaks down at frequency extremes, and other perceptual scales (mel, Bark) fit better in some regimes
- What I might be misunderstanding:
  - How well "approximately logarithmic" actually fits the Greenwood function
  - Whether outer hair cell amplification is really just a refinement or a fundamental part of cochlear tuning
  - Whether melody recognition for *unfamiliar* melodies works differently than for familiar ones

## 2) Claims (Convergent)
List concrete, testable claims.

| ID | Claim | Type (fact/model/value) | Confidence | Why I believe it now |
|---|---|---|---|---|
| C1 | The cochlea place-to-frequency map is approximately logarithmic | fact | High | Broad scientific consensus: Bekesy 1961 (Nobel Prize), Greenwood 1961, 1990 *J. Acoust. Soc. Am.* Known deviation at apex/low frequencies. The blog says "approximately," which is accurate. |
| C2 | Basilar membrane stiffness drops roughly exponentially from base to apex | fact | High | Measured by von Bekesy (1960), Emde & Franke (1979), Naidu & Mountain (2001) |
| C3 | The stiffness gradient is the "main driver" of the logarithmic frequency map | model | Low-medium | Blog claim; may understate fluid coupling and active amplification |
| C4 | Musical intervals are perceived as frequency ratios, not Hz differences | model | Medium-high | Strong in musical contexts above ~200 Hz; stretched octaves and mel scale complicate it |
| C5 | Melody recognition is transposition-invariant | model | Medium | True for familiar melodies at moderate distances; novel melodies rely more on contour |
| C6 | Each point on the basilar membrane is tuned to a specific frequency | fact | Medium | Each point has a characteristic frequency, but bandwidth is substantial (Q10 ~5-20); "bandpass filter" is more accurate than "point resonator" |

## 3) Falsification Plan
For each claim, define what would change your mind.

| Claim ID | What evidence would reduce confidence by >=30%? | What evidence would increase confidence by >=20%? | Fastest test |
|---|---|---|---|
| C1 | Cochlear implant mapping data showing systematic deviations >1 octave from log across the mid-frequency range | Greenwood function fit residuals <0.1 octave across 100 Hz-8 kHz | Plot Greenwood function vs pure log and compare residuals |
| C2 | Direct stiffness measurements showing linear or non-monotonic variation | Additional species data confirming exponential fit | Read Naidu & Mountain (2001) directly |
| C3 | Evidence that fluid coupling or active amplification alone can produce the tonotopic map without stiffness gradient | Computational model showing stiffness gradient alone produces ~correct map | Find cochlear mechanics review comparing passive vs active contributions |
| C4 | Listeners consistently matching intervals by Hz difference rather than ratio in controlled experiments | Cross-cultural studies showing ratio-based interval matching across non-Western traditions | Read Attneave & Olson (1971) original data |
| C5 | Studies showing chance-level melody recognition even for familiar melodies transposed by 1-2 semitones | Infant studies confirming transposition invariance without musical training | Read Dowling (1978) and Bartlett & Dowling (1980) |
| C6 | Single-unit recordings showing tuning curves broader than 1 octave at mid-frequencies | High-Q measurements (>30) at mid-frequencies in live human cochlea | Read Shera, Guinan & Oxenham (2002) |

## 4) Adversarial Audit
- Strongest argument against my current view: Melody recognition for *unfamiliar* melodies depends heavily on contour (up/down pattern), not precise intervals. Dowling (1978) showed chance-level discrimination between exact transpositions and same-contour-different-intervals for novel melodies. The blog interval-ratio model describes only one component of actual melody recognition.
- Best alternative hypothesis: Melody recognition is primarily contour-based (pattern of ups and downs), with precise interval information serving as a secondary cue that mainly helps for well-known melodies. The log-derivative model captures the interval component but misses the dominant one.
- If I am wrong, what is most likely true instead? The ear does work approximately in log-space and ratios are important, but melody identity depends at least as much on contour, rhythm, and tonal context as on precise interval preservation. The "derivative in log-space" framing, while mathematically elegant, oversells how much of melody recognition it actually explains.
- What would a skeptical expert criticize first?
  1. Calling outer hair cell amplification a "refinement" -- it transforms broadly-tuned passive responses into sharply-tuned active ones, and is arguably co-essential with stiffness
  2. The stretched octave problem -- if intervals were purely ratio-based, 2:1 should always sound like a perfect octave, but listeners consistently prefer slightly wider ratios
  3. The blog treats melody as a sequence of pitches, ignoring rhythm, timbre, and temporal structure

## 5) External Validation
Use source quality tiers: Primary > Secondary > Commentary.

| Claim ID | Best supporting source | Best opposing source | Source tier | Notes on quality/limits |
|---|---|---|---|---|
| C1 | Greenwood (1990) "A cochlear frequency-position function for several species -- 29 years later" *J. Acoust. Soc. Am.* 87(6): 2592-2605 | Greenwood himself: the k-constant in f = A(10^(ax) - k) shows deviation from pure log at low frequencies | Primary | Greenwood function is the standard; the deviation at apex is well-documented |
| C2 | Naidu & Mountain (2001) gerbil stiffness measurements: ln(k) = 1.75 - 0.31x (exponential fit) | None found contradicting exponential; limited to animal models | Primary | Human cadaver data from von Bekesy is older and less precise |
| C3 | Von Bekesy (1960) *Experiments in Hearing* -- stiffness gradient as basis for frequency analysis | Yoon, Puria & Bhatt (2007) *Biophysical J.* -- organ of Corti mass essential for passive tuning | Primary | The traveling wave requires fluid-stiffness interaction; stiffness alone insufficient |
| C4 | Attneave & Olson (1971) "Pitch as a medium" *Am. J. Psychol.* 84: 147-166 -- log scale fits musical interval judgments | Ohgushi (1983), Bell & Trainor (2023) -- octave stretch of 10-50 cents contradicts pure ratio model | Primary | Attneave & Olson note you cannot empirically distinguish "ratio perception" from "difference on log scale" |
| C5 | Plantinga & Trainor (2005) -- infants show transposition invariance | Dowling (1978) -- novel melody recognition relies on contour, not intervals; Bartlett & Dowling (1980) -- key-distance effects | Primary | The supporting and opposing evidence address different conditions (familiar vs novel) |
| C6 | Shera, Guinan & Oxenham (2002) *PNAS* -- Q_ERB ~10-20 in humans | Ruggero & Temchin (2005) *PNAS* -- "unexceptional sharpness" of human tuning | Primary | Genuine scientific controversy about sharpness; both published in PNAS |

Rules:
- LLM agreement is weak evidence.
- Prefer primary sources and original data.
- If evidence conflicts, record conflict explicitly.

## 6) Belief Update
| Claim ID | Old confidence | New confidence | Why it changed |
|---|---:|---:|---|
| C1 | Broad scientific consensus | No change | Not meaningfully in dispute as stated (Bekesy 1961; Greenwood 1961, 1990). |
| C2 | High | No change | Multiple independent measurements confirm exponential stiffness. |
| C3 | Low-medium | Low | Fluid coupling is co-essential (no traveling wave without it), and active amplification is far more than a refinement. "Main driver" overstates. |
| C4 | Medium-high | Medium-high | Stretched octaves are a real deviation but small (~10-50 cents). The ratio model holds well for sub-octave intervals in musical contexts. |
| C5 | Medium | Low-medium | Contour vs interval distinction (Dowling 1978) is a significant qualification. The blog model captures the interval component but that may not be the dominant factor for unfamiliar melodies. |
| C6 | Medium | Low-medium | Q values of 5-20 mean each "point" responds to a range of frequencies spanning up to several semitones. "Bandpass filter" is meaningfully more accurate than "tuned to a specific frequency." |

## 7) Output for Blog

### What I think
The blog core argument -- that melody survives key changes because the auditory system operates approximately in log-frequency space, making intervals (log-differences) invariant under the multiplicative shift of transposition -- is a sound first-order model. The math is correct. The biological grounding is approximately right. The main insight (the logarithm is not a trick, it is baked into the cochlea) is genuinely interesting and well-supported.

### Why
The Greenwood function confirms approximately logarithmic cochlear mapping. Exponential stiffness gradients are measured. Ratio-based interval perception is well-documented in musical contexts. The transposition-invariance math is trivially correct.

### What could falsify this
- Evidence that melody recognition depends primarily on contour, not intervals, even for familiar melodies
- Evidence that the cochlear map is significantly non-logarithmic across the musically relevant range (200 Hz - 4 kHz)
- Evidence that stretched octave perception undermines the ratio model for intervals smaller than an octave

### What I am unsure about
- Whether "main driver" is fair for stiffness, given that fluid coupling and active amplification are arguably co-essential
- Whether the blog adequately conveys that melody recognition involves contour and rhythm, not just intervals
- Whether "each point is tuned to a specific frequency" is too sharp a claim given Q values of 5-20
- How much the stretched octave phenomenon matters for the blog argument (it may be negligible for intervals smaller than an octave)

### What I will test next
- Plot the Greenwood function against a pure log to quantify the deviation across the musical range
- Read Dowling (1978) to understand the contour vs interval distinction more precisely
- Decide whether the blog should acknowledge contour as a co-factor in melody recognition

## 8) Calibration (Later Review)
- Review date: 2026-03-20
- Outcome per claim: Correct / Incorrect / Unresolved
- Where I was overconfident:
- Process fix for next cycle:




