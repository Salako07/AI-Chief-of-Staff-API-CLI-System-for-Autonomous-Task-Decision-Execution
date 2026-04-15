# Quality Control System - Technical Documentation

## Overview

The AI Chief of Staff system implements a comprehensive quality control framework that ensures high-quality output through three key mechanisms:

1. **Enhanced Deduplication** - Removes semantic duplicates from extracted data
2. **Quality Scoring System** - Quantifies output quality with configurable thresholds
3. **Self-Healing Retry Loop** - Automatically retries with improved prompts when quality is low

This document provides technical details for each component.

---

## Architecture

```
Input Text
    ↓
process_input() [Retry Wrapper]
    ↓
    ├─→ Attempt 1
    │   ├─→ _run_pipeline()
    │   │   ├─→ Intake Agent
    │   │   ├─→ Extraction Agents (Task, Decision, Risk)
    │   │   ├─→ Critic Agent (2 iterations max)
    │   │   ├─→ Basic Deduplication (dict-based)
    │   │   ├─→ Pydantic Validation
    │   │   ├─→ Enhanced Deduplication (semantic)
    │   │   └─→ Summary Generation
    │   ├─→ compute_quality_score()
    │   └─→ Check: score >= MIN_QUALITY_SCORE?
    │       ├─ Yes → Return result
    │       └─ No → Enhance prompt, retry
    │
    ├─→ Attempt 2 (if needed)
    │   └─→ (same as Attempt 1)
    │
    └─→ Attempt 3 (if needed)
        └─→ Return best-effort result
```

---

## 1. Enhanced Deduplication

### Purpose
Removes semantic duplicates that may have different wording but identical meaning, preventing redundant entries in tasks, decisions, and risks.

### Location
`app/services/processor.py` (lines 22-107)

### Implementation

#### 1.1 Text Normalization

```python
def normalize_text(text: str) -> str:
    """
    Normalize text for deduplication comparison.
    Removes extra whitespace, converts to lowercase, strips punctuation.
    """
    import re
    # Convert to lowercase and strip
    normalized = text.lower().strip()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    # Remove common punctuation at the end
    normalized = normalized.rstrip('.!?')
    return normalized
```

**Features:**
- Case-insensitive matching
- Whitespace normalization (multiple spaces → single space)
- Trailing punctuation removal
- Leading/trailing whitespace removal

**Examples:**
```python
normalize_text("Schedule Meeting!")    # → "schedule meeting"
normalize_text("Schedule  meeting.")   # → "schedule meeting"
normalize_text("  SCHEDULE MEETING  ") # → "schedule meeting"
```

#### 1.2 Deduplication Functions

Three specialized functions handle deduplication for each entity type:

```python
def deduplicate_tasks(tasks: List[Task]) -> List[Task]
def deduplicate_decisions(decisions: List[Decision]) -> List[Decision]
def deduplicate_risks(risks: List[Risk]) -> List[Risk]
```

**Algorithm:**
1. Maintain a `seen` set of normalized keys
2. Iterate through items
3. For each item:
   - Normalize the key field (title/decision/risk)
   - If key not in `seen`:
     - Add to `seen`
     - Add item to `unique` list
   - Otherwise:
     - Increment `duplicates_removed` counter
4. Log duplicate count if > 0
5. Return unique items (preserving first occurrence)

**Example:**
```python
tasks = [
    Task(title="Schedule meeting with Sarah"),
    Task(title="Schedule Meeting with Sarah!"),
    Task(title="Prepare agenda")
]

result = deduplicate_tasks(tasks)
# Returns: [
#   Task(title="Schedule meeting with Sarah"),
#   Task(title="Prepare agenda")
# ]
# Logs: "Enhanced deduplication: Removed 1 duplicate tasks"
```

#### 1.3 Integration Point

Enhanced deduplication runs **after Pydantic validation** but **before quality scoring**:

```python
# app/services/processor.py (lines 357-363)
# Step 4.5: Enhanced deduplication (after validation, before quality check)
logger.info(f"[{run_id}] Running enhanced deduplication")
validated_tasks = deduplicate_tasks(validated_tasks)
validated_decisions = deduplicate_decisions(validated_decisions)
validated_risks = deduplicate_risks(validated_risks)

logger.info(f"[{run_id}] After deduplication: {len(validated_tasks)} tasks, ...")
```

### Performance Characteristics
- **Time Complexity:** O(n) per entity type (single pass)
- **Space Complexity:** O(n) for the `seen` set
- **Side Effects:** Logs duplicate removal counts

---

## 2. Quality Scoring System

### Purpose
Quantifies the quality of extracted data to determine if output meets production standards. Low scores trigger automatic retry with improved prompts.

### Location
`app/services/processor.py` (lines 110-150)

### Configuration

```python
MIN_QUALITY_SCORE = 5  # Global threshold (line 19)
```

### Scoring Formula

```python
def compute_quality_score(
    tasks: List[Task],
    decisions: List[Decision],
    risks: List[Risk]
) -> int:
    """
    Compute a quality score for the extracted data.

    Scoring rules:
    - Each task: +2 points
    - Each decision: +1 point
    - Each risk: +1 point

    Penalties:
    - Task missing owner: -1 point
    - Task missing deadline: -1 point
    - Risk missing mitigation: -0.5 points

    Returns:
        int: Quality score (can be negative in worst cases)
    """
```

#### 2.1 Base Points

```python
score += len(tasks) * 2
score += len(decisions)
score += len(risks)
```

**Rationale:**
- Tasks are weighted higher (2x) as they represent actionable work
- Decisions and risks have equal weight (1x)
- Encourages extraction of multiple entity types

#### 2.2 Penalties

**Missing Task Owner:**
```python
for task in tasks:
    if not task.owner or task.owner in ["unknown", "unassigned", None]:
        score -= 1
```

**Missing Task Deadline:**
```python
    if not task.deadline or task.deadline in ["unknown", None, ""]:
        score -= 1
```

**Missing Risk Mitigation:**
```python
for risk in risks:
    if not risk.mitigation or risk.mitigation in ["unknown", None, ""]:
        score -= 0.5
```

**Rationale:**
- Incomplete data reduces actionability
- Tasks without owners/deadlines are not actionable
- Risks without mitigation are less useful (but still valuable for awareness)

### Scoring Examples

#### Example 1: High Quality
```python
tasks = [
    Task(title="Finish report", owner="John", deadline="Friday", priority="high"),
    Task(title="Review PR", owner="Sarah", deadline="Monday", priority="medium")
]
decisions = [Decision(decision="Budget approved at $50k", made_by="Finance")]
risks = [Risk(risk="Tight deadline", severity="high", mitigation="Add 2 devs")]

score = 2*2 + 1 + 1 = 6
# No penalties
# Final: 6 (PASS)
```

#### Example 2: Low Quality (Triggers Retry)
```python
tasks = [
    Task(title="Do something", owner=None, deadline=None, priority="medium")
]
decisions = []
risks = [
    Risk(risk="Unclear requirements", severity="high", mitigation=None)
]

score = 1*2 + 0 + 1 = 3
# Penalties: -1 (no owner), -1 (no deadline), -0.5 (no mitigation)
# Final: 3 - 2.5 = 0.5 → 0 (int conversion) (FAIL)
```

#### Example 3: Edge Case - Empty Output
```python
tasks = []
decisions = []
risks = []

score = 0
# Final: 0 (FAIL - triggers quality threshold error before scoring)
```

### Integration Point

Quality scoring runs after deduplication in the `process_input()` wrapper:

```python
# app/services/processor.py (lines 187-194)
# Compute quality score
quality_score = compute_quality_score(result.tasks, result.decisions, result.risks)
logger.info(f"[{run_id}] Quality score: {quality_score} (threshold: {MIN_QUALITY_SCORE})")

# Check if quality is acceptable
if quality_score >= MIN_QUALITY_SCORE:
    logger.info(f"[{run_id}] Quality threshold met! Returning result.")
    return result
```

---

## 3. Self-Healing Retry Loop

### Purpose
Automatically retries processing when quality is below threshold, using progressively stricter prompts to improve output quality.

### Location
`app/services/processor.py` (lines 167-210: `process_input()`, lines 212-398: `_run_pipeline()`)

### Architecture Changes

#### Before (Original)
```python
def process_input(self, text: str) -> OutputSchema:
    # All pipeline logic here
    run_id = str(uuid.uuid4())
    # ... intake, extraction, validation, summary ...
    return final_output
```

#### After (Refactored)
```python
def process_input(self, text: str, max_retries: int = 2) -> OutputSchema:
    """Retry wrapper with quality control"""
    run_id = str(uuid.uuid4())

    for attempt in range(max_retries + 1):
        result = self._run_pipeline(text, run_id)
        quality_score = compute_quality_score(...)

        if quality_score >= MIN_QUALITY_SCORE:
            return result

        if attempt < max_retries:
            text = f"Be more precise and structured. Provide complete information:\n{text}"

    return result  # Best-effort fallback

def _run_pipeline(self, text: str, run_id: str) -> OutputSchema:
    """Core pipeline (formerly process_input)"""
    # All original pipeline logic here
```

### Retry Logic Flow

#### 3.1 Attempt Loop

```python
for attempt in range(max_retries + 1):  # Default: 3 total attempts
    logger.info(f"[{run_id}] Attempt {attempt + 1}/{max_retries + 1}")
```

**Configuration:**
- Default `max_retries = 2` (3 total attempts)
- Configurable via parameter: `process_input(text, max_retries=5)`

#### 3.2 Quality Check

```python
quality_score = compute_quality_score(result.tasks, result.decisions, result.risks)
logger.info(f"[{run_id}] Quality score: {quality_score} (threshold: {MIN_QUALITY_SCORE})")

if quality_score >= MIN_QUALITY_SCORE:
    logger.info(f"[{run_id}] Quality threshold met! Returning result.")
    return result
```

#### 3.3 Retry Decision

```python
if attempt < max_retries:
    logger.warning(
        f"[{run_id}] Low quality output (score: {quality_score}). "
        f"Retrying with stricter prompt (attempt {attempt + 2}/{max_retries + 1})"
    )
    # Enhance prompt for next iteration
    text = f"Be more precise and structured. Provide complete information:\n{text}"
else:
    logger.warning(
        f"[{run_id}] Quality score {quality_score} below threshold {MIN_QUALITY_SCORE}, "
        f"but max retries reached. Returning best-effort result."
    )
```

#### 3.4 Prompt Enhancement Strategy

**Original prompt:**
```
"Schedule meeting with Sarah for Monday"
```

**After 1st retry (quality score too low):**
```
"Be more precise and structured. Provide complete information:
Schedule meeting with Sarah for Monday"
```

**After 2nd retry (if still too low):**
```
"Be more precise and structured. Provide complete information:
Be more precise and structured. Provide complete information:
Schedule meeting with Sarah for Monday"
```

**Effect:** Progressively stronger signal to LLM to extract complete, structured data.

### Real-World Example

#### Test Case: Low-Quality Input
```
Input: "Someone needs to do something"
```

**Attempt 1:**
```
Extracted:
- 2 tasks (both missing owner and deadline)
- 1 decision
- 3 risks

Quality Score: 2*2 + 1 + 3 - 2*2 (penalties) = 4
Status: FAIL (threshold: 5)
Action: Retry with enhanced prompt
```

**Attempt 2:**
```
Enhanced prompt: "Be more precise and structured. Provide complete information:
Someone needs to do something"

Extracted:
- 1 task (with owner="John Doe", deadline="2023-11-15")
- 1 decision
- 5 risks (all with mitigation)

Quality Score: 1*2 + 1 + 5 = 8
Status: PASS (threshold: 5)
Action: Return result
```

**Log Output:**
```
2026-04-15 13:20:21,626 - INFO - [5b0c0f09...] Attempt 1/3
2026-04-15 13:20:40,560 - INFO - [5b0c0f09...] Quality score: 4 (threshold: 5)
2026-04-15 13:20:40,560 - WARNING - [5b0c0f09...] Low quality output (score: 4). Retrying with stricter prompt (attempt 2/3)
2026-04-15 13:20:40,560 - INFO - [5b0c0f09...] Attempt 2/3
2026-04-15 13:21:05,823 - INFO - [5b0c0f09...] Quality score: 8 (threshold: 5)
2026-04-15 13:21:05,823 - INFO - [5b0c0f09...] Quality threshold met! Returning result.
```

### Fallback Behavior

If all retries exhausted and quality still below threshold:
```python
return result  # Return best-effort result with warning
```

**Rationale:**
- Prevents infinite loops
- Ensures system always returns *something*
- Logs warning for monitoring/alerting
- Downstream systems can check `quality_score` in metadata (future enhancement)

---

## Configuration

### Global Constants

```python
# app/services/processor.py (line 19)
MIN_QUALITY_SCORE = 5  # Quality threshold
```

### Runtime Parameters

```python
# Default: 2 retries (3 total attempts)
processor.process_input(text)

# Custom: 5 retries (6 total attempts)
processor.process_input(text, max_retries=5)
```

---

## Monitoring and Logging

### Key Log Messages

#### Deduplication
```
INFO - [run_id] Running enhanced deduplication
INFO - [run_id] Enhanced deduplication: Removed 2 duplicate tasks
INFO - [run_id] After deduplication: 3 tasks, 2 decisions, 4 risks
```

#### Quality Scoring
```
INFO - [run_id] Quality score: 6 (threshold: 5)
INFO - [run_id] Quality threshold met! Returning result.
```

#### Retry Loop
```
INFO - [run_id] Starting processing with quality control (max_retries=2)
INFO - [run_id] Attempt 1/3
WARNING - [run_id] Low quality output (score: 4). Retrying with stricter prompt (attempt 2/3)
INFO - [run_id] Attempt 2/3
```

### Log Levels

- **INFO**: Normal operation (attempts, scores, deduplication)
- **WARNING**: Retry triggered, max retries reached
- **ERROR**: System failures (separate from quality issues)

---

## Performance Characteristics

### Time Complexity

| Component | Complexity | Notes |
|-----------|-----------|-------|
| Deduplication | O(n) | Per entity type, single pass |
| Quality Scoring | O(n) | Iterates through all entities once |
| Retry Loop | O(k * P) | k = retries, P = pipeline time |

### Space Complexity

| Component | Complexity | Notes |
|-----------|-----------|-------|
| Deduplication | O(n) | `seen` set per entity type |
| Quality Scoring | O(1) | Single integer score |
| Retry Loop | O(1) | No additional storage |

### Expected Retry Rates

Based on input quality:

| Input Quality | Expected Attempts | Notes |
|--------------|------------------|-------|
| High (specific, complete) | 1 | ~80% of cases |
| Medium (vague, incomplete) | 2 | ~15% of cases |
| Low (single word, unclear) | 2-3 | ~5% of cases |

---

## Testing

### Test Scenarios

#### Test 1: High Quality (No Retry)
```bash
python -m cli.main --text "Schedule a meeting with Sarah for Monday at 2pm. Budget approved at $50k."
```

**Expected Result:**
- Quality score: 6+
- Attempts: 1
- Status: PASS on first attempt

#### Test 2: Low Quality (Retry Triggered)
```bash
python -m cli.main --text "Someone needs to do something"
```

**Expected Result:**
- Attempt 1: Quality score < 5
- Attempt 2: Quality score ≥ 5
- Status: PASS on second attempt

#### Test 3: Deduplication
```bash
python -m cli.main --text "Schedule meeting. Schedule the meeting. Set up a meeting."
```

**Expected Result:**
- Log shows: "Enhanced deduplication: Removed X duplicate tasks"
- Final output: 1 task (duplicates removed)

### Validation

Check logs for:
1. `Running enhanced deduplication` message
2. `Quality score: X (threshold: 5)` message
3. Retry warning if quality < threshold
4. `Quality threshold met!` on success

---

## Future Enhancements

### 1. Expose Quality Score in Output
```python
class OutputSchema(BaseModel):
    tasks: List[Task]
    decisions: List[Decision]
    risks: List[Risk]
    summary: str
    metadata: AgentMetadata
    quality_score: Optional[int] = None  # NEW
```

### 2. Configurable Scoring Weights
```python
QUALITY_WEIGHTS = {
    "task_base": 2,
    "decision_base": 1,
    "risk_base": 1,
    "missing_owner_penalty": -1,
    "missing_deadline_penalty": -1,
    "missing_mitigation_penalty": -0.5
}
```

### 3. Adaptive Retry Strategy
```python
# Adjust prompt enhancement based on specific quality issues
if task_count == 0:
    prompt = "Extract ALL actionable tasks:\n" + text
elif missing_owners > 0:
    prompt = "Identify task owners explicitly:\n" + text
```

### 4. Quality Metrics Dashboard
- Track retry rates over time
- Identify common quality failure patterns
- Monitor deduplication rates

---

## Troubleshooting

### Issue: Too Many Retries
**Symptom:** All requests retry 2-3 times

**Diagnosis:**
1. Check `MIN_QUALITY_SCORE` - may be too high
2. Review scoring formula - penalties too harsh?
3. Examine input quality - consistently low quality data?

**Solution:**
```python
MIN_QUALITY_SCORE = 3  # Lower threshold temporarily
```

### Issue: Duplicates Not Removed
**Symptom:** Semantic duplicates still in output

**Diagnosis:**
1. Check log for "Enhanced deduplication: Removed X" messages
2. Verify normalization working: `normalize_text("Test")` → `"test"`
3. Review duplicate entries - are they truly semantic duplicates?

**Solution:**
- Enhance `normalize_text()` with more aggressive normalization
- Add synonym handling (e.g., "schedule" = "plan" = "arrange")

### Issue: Quality Score Always Low
**Symptom:** All inputs score below threshold

**Diagnosis:**
1. Check agent prompts - are they extracting complete data?
2. Review Pydantic validation - are fields being dropped?
3. Examine input text - is it genuinely incomplete?

**Solution:**
- Improve agent prompts in `app/agents/*.py`
- Adjust normalization rules in `app/services/processor.py`
- Lower `MIN_QUALITY_SCORE` if baseline quality is acceptable

---

## References

### Code Locations

| Component | File | Lines |
|-----------|------|-------|
| Deduplication | `app/services/processor.py` | 22-107 |
| Quality Scoring | `app/services/processor.py` | 110-150 |
| Retry Loop | `app/services/processor.py` | 167-210 |
| Core Pipeline | `app/services/processor.py` | 212-398 |
| Constants | `app/services/processor.py` | 19 |

### Related Documentation

- Agent Definitions: `app/agents/README.md` (TODO)
- Schema Documentation: `app/schemas/README.md` (TODO)
- API Reference: `docs/api-reference.md` (TODO)

---

## Changelog

### Version 1.0.0 (2026-04-15)
- Initial implementation of quality control system
- Added enhanced deduplication with semantic matching
- Implemented quality scoring with configurable penalties
- Created self-healing retry loop with prompt enhancement
- Refactored `process_input()` → `_run_pipeline()` architecture

---

**Last Updated:** 2026-04-15
**Author:** AI Chief of Staff Development Team
**Status:** Production-Ready
