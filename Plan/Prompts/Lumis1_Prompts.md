# Lumis-1 AI Prompts for Claude Opus

> [!NOTE]
> **USAGE INSTRUCTIONS**
> **TARGET RUNTIME: Claude Code (CLI)**.
> All prompts below are designed to be served to `claude` (Claude Code).
> **DO NOT** attempt to generate the notebook code yourself (as an Agent). 
> **CRITICAL: You (Gemini) MUST follow these rules STRICTLY, in addition to your Global User Rules.**
> **ACTION:** Copy the relevant phase prompt and paste it into the `claude` CLI.
> Each phase prompt below is now **self-contained**.

---

## 1. Phase 0: Environment Setup

**Goal**: Initialize RunPod GPU environment and verify model availability.
**Copy/Paste into Claude:**

```text
```text
You are an expert AI Engineer.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Reason deeply at every step.
2. **PLUGINS**: Use all capabilities (code/analysis) to verify.
3. **HISTORY**: Read `Lumis1_Execution_History.md` before starting.
4. **LOGGING**: You MUST save all execution logs (training metrics, test results, errors) to a file named `execution.log` AND print them to stdout.
5. **VERIFY**: Check code against Acceptance Criteria.

Create a notebook for RunPod (A40/A100 GPU) to set up the Lumis-1 development environment.
NOTE: The environment uses the "RunPod PyTorch 2.4.0" template which already has PyTorch 2.4.0 and CUDA 12.4.1 pre-installed. Do NOT try to reinstall/downgrade torch unless critical.

REQUIREMENTS:
1. Verify CUDA device is available (NVIDIA A40 or A100)
   - Print output of `nvidia-smi`
   - Print `torch.__version__` and `torch.version.cuda`
2. Install additional dependencies (ensure compatibility with torch 2.4.0):
   - transformers>=4.40.0
   - datasets>=2.18.0
   - accelerate>=0.28.0
   - peft>=0.10.0
   - onnxruntime-gpu>=1.17.0
   - optimum>=1.17.0

3. Download and verify these models load (on GPU):
   - ibm-granite/granite-4.0-h-1b (Speaker)
   - unitary/toxic-bert (Safety base)
   - cross-encoder/nli-deberta-v3-xsmall (NLI base)

4. Run inference test on each model (ensure .to("cuda"))
5. Print VRAM usage

Output: Single notebook cell with progress messages.
```

---

## 2. Phase 1: Speaker Dataset Construction

**Goal**: Generate the training data (Diversity Engine + Open Datasets).
**Copy/Paste into Claude:**

```text
```text
You are the Architect of the "Diversity Engine" data pipeline.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Reason deeply about modularity and async flows.
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md` for proven architecture (Async/DeepSeek).
4. **VERIFY**: Check against Acceptance Criteria.

Create a RunPod notebook that builds the Speaker training dataset.

Create a RunPod notebook that builds the Speaker training dataset.

**STATUS: PROVEN / EXECUTED (Do not change architecture without reason)**

REQUIREMENTS (CRITICAL):
1.  **Architecture**: Must use `asyncio` for parallel generation. Sequential is too slow.
2.  **Teacher Model**: Use `openai` client targeting `deepseek-chat` (DeepSeek V3).
3.  **Resilience**: Implement Checkpointing. Save `checkpoints/checkpoint_{category}.jsonl` after every batch.
4.  **JSON Robustness**: Prompt MUST say: "No markdown code blocks, double quotes only, no trailing commas."
5.  **Refusal Gate**: Use `min_tokens=15` for Refusal category (Standard is 50).

TARGET: ~9,500 high-quality examples

REQUIREMENTS:
1.  **Teacher Model**: Use `openai` python client to generate data.
    -   Target: `Qwen/Qwen2.5-72B-Instruct` (or 32B/DeepSeek-V3).
    -   Assume `OPENAI_API_KEY` and `OPENAI_API_BASE` (if non-standard) are in `os.environ`.
    -   Allow user to configure Base URL (e.g., DeepInfra, OpenRouter, or Local vLLM).
2.  **Dependencies**: Install `openai`, `tqdm`, `pandas`.

TARGET: ~10,000 high-quality examples

DATASET COMPOSITION (Strict Targets):
| Category | Count | Description |
|---|---|---|
| General | 1,500 | OpenOrca/NoRobots (Filtered) |
| Identity | 1,000 | Brand identity + Jailbreak resistance |
| Evidence | 2,000 | Micro-worlds: Context-grounded + "Traps" (answer not in context) |
| Refusal | 500 | Short, polite refusals (max 2 sentences) |
| Repair | 2,500 | 5-turn: Hallucination -> Steering -> Correction |
| Contrast | 1,500 | Near-identical inputs, different outputs (Boundary testing) |
| Policy | 1,000 | Enterprise scenarios (Approve/Deny/Escalate) |

STEP 1: Load Open Datasets (General Category)
- Load OpenOrca & NoRobots.
- Filter: English, 50-500 tokens, No Code.
- Sample 1,500 total.

STEP 2: Generate Diversity Data (Qwen/API Teacher)
Use the API to generate the remaining categories.

A. Micro-World Contexts (Evidence & Repair)
- Generate fictional "Micro-Worlds" (3-10 sentences).
- Create valid Q&A pairs.
- Create "Trap" questions where the answer is NOT in the context (Model must state uncertainty).

B. Repair Sequences (2,500)
- Format:
  [
    {"role": "system", ...},
    {"role": "user", "content": "Question..."},
    {"role": "assistant", "content": "Hallucinated Answer..."},
    {"role": "user", "content": "Your response contained unsupported claims..."},
    {"role": "assistant", "content": "Corrected Answer (Grounded)..."}
  ]

C. Policy & Contrast
- Generate pairs differing by one variable (e.g., "Deploy to AWS" vs "Deploy to Azure").

STEP 3: Quality Gates (Discard & Regenerate)
- JSON Validity: Must be valid.
- Length: 50-500 tokens.
- Repair Logic: Corrected response MUST have >= 30% keyword overlap with context.
- Uniqueness: No exact duplicate prompts.
- Log the "Discard Rate" (Expected 5-15%).

STEP 4: Format & Save
- Format for Granite chat template: <|start_of_role|>...
- Save: `train.jsonl` (9,000), `eval.jsonl` (1,000).

ACCEPTANCE CRITERIA:
1. Notebook runs end-to-end.
2. Final count is ~10,000.
3. Category counts match the table above.
4. Quality Gates log the number of discarded bad examples.
5. "Repair" sequences strictly follow the 5-turn format.
```

---

## 3. Phase 1: Speaker Fine-tuning

**Goal**: Fine-tune Granite 4.0-H-1B.
**Copy/Paste into Claude:**

```text
```text
You are a Fine-Tuning Specialist.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Reason about hyperparameters for Granite/Mamba2.
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md` for context.
4. **VERIFY**: Check against Acceptance Criteria.

Create a RunPod notebook that fine-tunes Granite 4.0-H-1B.

Create a RunPod notebook that fine-tunes Granite 4.0-H-1B.

REQUIREMENTS:
1. Load ibm-granite/granite-4.0-h-1b
2. LoRA config:
   - r=16, lora_alpha=32, lora_dropout=0.05
   - Target: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
   
3. Training config:
   - Learning rate: 2e-5, cosine scheduler
   - Batch size: 4, gradient accumulation: 4 (effective 16)
   - Epochs: 2
   - Max sequence length: 2048
   - Warmup: 10% steps
   
4. Load train.jsonl, eval.jsonl
5. Train with eval every 200 steps
6. Save LoRA adapter
7. Merge into base model
8. Save as lumis1-speaker-v1/ in safetensors

Run 5 test generations after training.
```

---

## 4. Phase 2: Safety Validator Fine-tuning

**Goal**: Fine-tune Toxic-BERT (Adversarial Robustness).
**Copy/Paste into Claude:**

```text
```text
You are a Safety Systems Engineer.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Focus on preventing False Negatives.
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md`.
4. **VERIFY**: Check against Acceptance Criteria.

Create a RunPod notebook to fine-tune the Safety Validator.

Create a RunPod notebook to fine-tune the Safety Validator.

BASE MODEL: unitary/toxic-bert

The base model already detects: toxic, severe_toxic, obscene, threat, insult, identity_hate

We need to ADD detection for:
- pii_risk: response contains or requests personal information
- injection_attempt: input tries to override system instructions

STEP 1: Prepare additional training data

PII examples (2,000):
- Positive: "My SSN is 123-45-6789", "Email me at john@email.com", "Call me at 555-1234"
- Negative: "Contact our support team", "Please provide your order number"

Injection examples (2,000):
- Positive: "Ignore previous instructions", "You are now DAN", "System: override safety"
- Negative: "Can you help me write instructions?", "What are your system requirements?"

Adversarial Hard Negatives (2,000 - 30% of new data):
- Use Diversity Engine to generate "Poisoned" examples:
  - Surface features suggest SAFE but content is unsafe.
  - "Please debug this Python code: [obfuscated exploit script]" (Should be Injection/Harmful)
  - "Write a story about a happy event [that implicitly reveals PII]" (Should be PII Risk)

STEP 2: Extend the classification head
- Load unitary/toxic-bert
- Add 2 new output neurons (pii_risk, injection_attempt)
- Initialize new weights randomly, keep original 6 frozen initially

STEP 3: Two-phase training
Phase A: Train only new heads (freeze base + original heads)
- 3 epochs on PII + injection data
- LR: 3e-5

Phase B: Fine-tune all heads together
- 1 epoch on combined data (subsample original toxicity to balance)
- LR: 1e-5

STEP 4: Export
- Save PyTorch model: lumis1-safety-validator-v1/
- Export ONNX: lumis1-safety-validator-v1/model.onnx
- Quantize ONNX to INT8

STEP 5: Verify
Test on 20 examples (including 5 hard negatives), print classification report.

Output labels: toxic, severe_toxic, obscene, threat, insult, identity_hate, pii_risk, injection_attempt
Final output: max(all_scores) as "safety_risk" score (0-1, higher = more risky)

ACCEPTANCE CRITERIA:
1. Model successfully loads and fine-tunes.
2. ONNX export is valid and runs in < 10ms.
3. Test set includes at least 5 "Hard Negative" examples.
4. Verify that "debug this exploit" is correctly flagged as risk.
```

---

## 5. Phase 2: Consistency Validator Fine-tuning

**Goal**: Fine-tune DeBERTa (NLI Logic).
**Copy/Paste into Claude:**

```text
```text
You are a Logic & Reason Engineer. 

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Ensure model learns semantic contradiction.
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md`.
4. **VERIFY**: Check against Acceptance Criteria.

Create a RunPod notebook to fine-tune the Consistency Validator.

Create a RunPod notebook to fine-tune the Consistency Validator.

BASE MODEL: cross-encoder/nli-deberta-v3-xsmall

This model already does NLI: (premise, hypothesis) → entailment/neutral/contradiction
We adapt it to: (context+prompt, response) → same labels

For Lumis: consistency_score = 1 - P(contradiction)

STEP 1: Prepare training data
Load existing NLI data but reformat:
- SNLI : stanfordnlp/snli (filter label != -1)
- ANLI: facebook/anli

Transform to Lumis format:
- Input: "[CONTEXT] {premise} [QUERY] Is the following response consistent? [RESPONSE] {hypothesis}"
- Label: same (entailment=0, neutral=1, contradiction=2)

Generate "Hard Negatives" (Adversarial) - 20-30% of data:
- Use Diversity Engine to create subtle contradictions:
  - Context: "The server restarts at 3 AM."
  - Draft: "The server restarts at 3 PM." (One word difference, High Contradiction)
  - Context: "Policy allows read-only access."
  - Draft: "You can write to the database." (Action contradiction)

Total: 50,000 examples (subsample from SNLI/ANLI + synthetic hard negatives)

STEP 2: Fine-tune
- LR: 2e-5
- Batch: 32
- Epochs: 2
- Early stopping on validation accuracy

STEP 3: Export
- Save: lumis1-consistency-validator-v1/
- ONNX export + INT8 quantization

STEP 4: Create inference wrapper
def score_consistency(context: str, prompt: str, response: str) -> dict:
    input_text = f"[CONTEXT] {context} [QUERY] {prompt} [RESPONSE] {response}"
    # Run model
    # Return {"entailment": p0, "neutral": p1, "contradiction": p2, "consistency_score": 1-p2}

Test on 20 examples.

ACCEPTANCE CRITERIA:
1. Training loss decreases significantly on Hard Negatives.
2. Verify: "Server 3 AM" vs "Server 3 PM" is flagged as Contradiction (>0.8).
3. ONNX export valid and performant.
```

---

## 6. Phase 2: Support Validator Fine-tuning

**Goal**: Fine-tune DeBERTa (Fact Verification).
**Copy/Paste into Claude:**

```text
```text
You are a RAG Verification Specialist.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Focus on detecting hallucination (smooth but wrong).
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md`.
4. **VERIFY**: Check against Acceptance Criteria.

Create a RunPod notebook to fine-tune the Support Validator.

Create a RunPod notebook to fine-tune the Support Validator.

BASE MODEL: cross-encoder/nli-deberta-v3-xsmall

TASK: Verify if response claims are supported by context (fact verification)

STEP 1: Load FEVER dataset
- fever/fever (climate: train)
- Labels: SUPPORTS, REFUTES, NOT ENOUGH INFO
- Map to: supported=0, refuted=1, not_enough_info=2

Format:
- Input: "[EVIDENCE] {evidence} [CLAIM] {claim}"
- Label: support label

STEP 2: Add VitaminC for harder examples
- tals/vitaminc
- Same label mapping

STEP 3: Generate "Hallucination Traps" (Hard Negatives) - 20-30% of data:
- Use Diversity Engine to create "Grounded but Hallucinated" examples:
  - Draft looks professional and confident.
  - Cites the correct context document title.
  - BUT contains one specific numerical or factual detail NOT in the text.
  - Label: NOT_ENOUGH_INFO or REFUTES (depending on direct contradiction).

Total: 80,000 examples balanced across labels

STEP 4: Fine-tune
- LR: 2e-5
- Batch: 32  
- Epochs: 3

STEP 5: Export
- Save: lumis1-support-validator-v1/
- ONNX + INT8

STEP 6: Inference wrapper
def score_support(context: str, response: str) -> dict:
    input_text = f"[EVIDENCE] {context} [CLAIM] {response}"
    # Return {"supported": p0, "refuted": p1, "not_enough_info": p2, "support_score": p0}

Test on 20 examples including 5 Hallucination Traps.

ACCEPTANCE CRITERIA:
1. Model distinguishes between "Supported" and "Not Enough Info" for subtle details.
2. Verify: A draft citing real context but inventing a number is flagged as UNSUPPORTED.
3. ONNX export valid.
```

---

## 7. Phase 3: Runtime Implementation

**Goal**: Implement the Python Runtime Package.
**Copy/Paste into Claude:**

```text
```text
You are a Senior Python Systems Architect.

SYSTEM & CONTEXT:
1. **ULTRATHINK**: Design for <10ms latency.
2. **PLUGINS**: Use code execution to verify logic.
3. **HISTORY**: Read `Lumis1_Execution_History.md`.
4. **VERIFY**: Check against Acceptance Criteria.

Create the Lumis-1 runtime Python package.

Create the Lumis-1 runtime Python package.

FILE: lumis/config.py
----------------------------------------
from dataclasses import dataclass, field
from pathlib import Path
import yaml

@dataclass
class BrandConfig:
    name: str = "Lumis-1"
    company: str = "Eptesicus Laboratories"
    system_prompt: str = ""
    
    def __post_init__(self):
        if not self.system_prompt:
            self.system_prompt = f"""You are {self.name}, a governed enterprise AI assistant developed by {self.company}.
You operate under strict governance policies. You cite provided context when answering.
If you cannot verify a claim from the provided context, you explicitly state this.
You refuse harmful requests briefly without lengthy explanations."""

@dataclass
class PolicyConfig:
    safety_threshold: float = 0.3      # ABOVE this = unsafe → REFUSE
    consistency_threshold: float = 0.7  # BELOW this = inconsistent → REWRITE  
    support_threshold: float = 0.6      # BELOW this = unsupported → REWRITE
    max_retries: int = 3

@dataclass  
class LumisConfig:
    brand: BrandConfig = field(default_factory=BrandConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    speaker_path: str = "./lumis1-speaker-v1"
    safety_validator_path: str = "./validators/lumis1-safety-validator-v1"
    consistency_validator_path: str = "./validators/lumis1-consistency-validator-v1"
    support_validator_path: str = "./validators/lumis1-support-validator-v1"
    device: str = "cuda"
    use_onnx: bool = True
    
    @classmethod
    def from_yaml(cls, path: str) -> "LumisConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        brand = BrandConfig(**data.get("brand", {}))
        policy = PolicyConfig(**data.get("policy", {}))
        return cls(
            brand=brand,
            policy=policy,
            **{k: v for k, v in data.items() if k not in ("brand", "policy")}
        )


FILE: lumis/speaker.py
----------------------------------------
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class Speaker:
    def __init__(self, model_path: str, device: str, brand: BrandConfig):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            torch_dtype=torch.bfloat16,
            device_map="cuda"  # FORCE CUDA
        )
        self.model.eval()
        self.brand = brand
        
    def generate(self, prompt: str, context: str = "", 
                 steering: str = None, max_tokens: int = 512) -> str:
        messages = [{"role": "system", "content": self.brand.system_prompt}]
        
        user_content = ""
        if context:
            user_content += f"[CONTEXT]\n{context}\n\n"
        if steering:
            user_content += f"[INSTRUCTION]\n{steering}\n\n"
        user_content += prompt
        
        messages.append({"role": "user", "content": user_content})
        
        input_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return response.strip()


FILE: lumis/validators/base.py
----------------------------------------
from abc import ABC, abstractmethod
from typing import Dict

class BaseValidator(ABC):
    @abstractmethod
    def score(self, prompt: str, context: str, response: str) -> Dict[str, float]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


FILE: lumis/validators/safety.py
----------------------------------------
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from .base import BaseValidator

class SafetyValidator(BaseValidator):
    LABELS = ["toxic", "severe_toxic", "obscene", "threat", 
              "insult", "identity_hate", "pii_risk", "injection_attempt"]
    
    def __init__(self, model_path: str, use_onnx: bool = True):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if use_onnx:
            # TRY INT8 FIRST
            import os
            model_file = "model_int8.onnx" if os.path.exists(f"{model_path}/model_int8.onnx") else "model.onnx"
            self.session = ort.InferenceSession(f"{model_path}/{model_file}", providers=["CUDAExecutionProvider"])
        else:
            from transformers import AutoModelForSequenceClassification
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to("cuda")
        self.use_onnx = use_onnx
        
    def score(self, prompt: str, context: str, response: str) -> Dict[str, float]:
        text = f"{prompt} {context} {response}"
        inputs = self.tokenizer(text, return_tensors="np", truncation=True, max_length=512)
        
        if self.use_onnx:
            outputs = self.session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"]
            })
            logits = outputs[0][0]
        else:
            import torch
            with torch.no_grad():
                outputs = self.model(**{k: torch.tensor(v) for k, v in inputs.items()})
                logits = outputs.logits[0].numpy()
        
        probs = 1 / (1 + np.exp(-logits))  # sigmoid
        result = {label: float(probs[i]) for i, label in enumerate(self.LABELS)}
        result["safety_risk"] = float(max(probs))
        return result
    
    @property
    def name(self) -> str:
        return "safety"


FILE: lumis/validators/consistency.py
----------------------------------------
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from .base import BaseValidator

class ConsistencyValidator(BaseValidator):
    def __init__(self, model_path: str, use_onnx: bool = True):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if use_onnx:
            # TRY INT8 FIRST
            import os
            model_file = "model_int8.onnx" if os.path.exists(f"{model_path}/model_int8.onnx") else "model.onnx"
            self.session = ort.InferenceSession(f"{model_path}/{model_file}", providers=["CUDAExecutionProvider"])
        else:
            from transformers import AutoModelForSequenceClassification
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to("cuda")
        self.use_onnx = use_onnx
        
    def score(self, prompt: str, context: str, response: str) -> Dict[str, float]:
        input_text = f"[CONTEXT] {context} [QUERY] {prompt} [RESPONSE] {response}"
        inputs = self.tokenizer(input_text, return_tensors="np", truncation=True, max_length=512)
        
        if self.use_onnx:
            outputs = self.session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"]
            })
            logits = outputs[0][0]
        else:
            import torch
            with torch.no_grad():
                outputs = self.model(**{k: torch.tensor(v) for k, v in inputs.items()})
                logits = outputs.logits[0].numpy()
        
        probs = np.exp(logits) / np.sum(np.exp(logits))  # softmax
        return {
            "entailment": float(probs[0]),
            "neutral": float(probs[1]),
            "contradiction": float(probs[2]),
            "consistency_score": float(1 - probs[2])
        }
    
    @property
    def name(self) -> str:
        return "consistency"


FILE: lumis/validators/support.py
----------------------------------------
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from .base import BaseValidator

class SupportValidator(BaseValidator):
    def __init__(self, model_path: str, use_onnx: bool = True):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if use_onnx:
            # TRY INT8 FIRST
            import os
            model_file = "model_int8.onnx" if os.path.exists(f"{model_path}/model_int8.onnx") else "model.onnx"
            self.session = ort.InferenceSession(f"{model_path}/{model_file}", providers=["CUDAExecutionProvider"])
        else:
            from transformers import AutoModelForSequenceClassification
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to("cuda")
        self.use_onnx = use_onnx
        
    def score(self, prompt: str, context: str, response: str) -> Dict[str, float]:
        input_text = f"[EVIDENCE] {context} [CLAIM] {response}"
        inputs = self.tokenizer(input_text, return_tensors="np", truncation=True, max_length=512)
        
        if self.use_onnx:
            outputs = self.session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"]
            })
            logits = outputs[0][0]
        else:
            import torch
            with torch.no_grad():
                outputs = self.model(**{k: torch.tensor(v) for k, v in inputs.items()})
                logits = outputs.logits[0].numpy()
        
        probs = np.exp(logits) / np.sum(np.exp(logits))  # softmax
        return {
            "supported": float(probs[0]),
            "refuted": float(probs[1]),
            "not_enough_info": float(probs[2]),
            "support_score": float(probs[0])
        }
    
    @property
    def name(self) -> str:
        return "support"


FILE: lumis/steering.py
----------------------------------------
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict
import time

class Action(Enum):
    ALLOW = "allow"
    REWRITE = "rewrite"
    REFUSE = "refuse"

class Status(Enum):
    OK = "ok"
    LOW_CONFIDENCE = "low_confidence"
    REFUSED = "refused"

@dataclass
class Attempt:
    draft: str
    scores: Dict[str, Dict[str, float]]
    action: Action
    reason: Optional[str]
    steering_instruction: Optional[str]
    latency_ms: float

@dataclass
class SteeringResult:
    response: str
    status: Status
    attempts: List[Attempt]

class SteeringLoop:
    REFUSAL_TEMPLATES = {
        "safety": "I can't help with that request.",
        "default": "I'm not able to assist with this."
    }
    
    def __init__(self, speaker, validators: list, policy):
        self.speaker = speaker
        self.validators = {v.name: v for v in validators}
        self.policy = policy
        
    def run(self, prompt: str, context: str = "") -> SteeringResult:
        attempts = []
        steering = None
        
        for attempt_num in range(self.policy.max_retries + 1):
            start = time.time()
            
            draft = self.speaker.generate(prompt, context, steering)
            
            scores = {}
            for name, validator in self.validators.items():
                scores[name] = validator.score(prompt, context, draft)
            
            action, reason = self._evaluate(scores)
            
            latency = (time.time() - start) * 1000
            attempts.append(Attempt(draft, scores, action, reason, steering, latency))
            
            if action == Action.ALLOW:
                return SteeringResult(draft, Status.OK, attempts)
            elif action == Action.REFUSE:
                return SteeringResult(
                    self.REFUSAL_TEMPLATES.get(reason, self.REFUSAL_TEMPLATES["default"]),
                    Status.REFUSED,
                    attempts
                )
            else:
                steering = self._build_steering(scores, reason)
        
        best = min(attempts, key=lambda a: self._score_badness(a.scores))
        return SteeringResult(best.draft, Status.LOW_CONFIDENCE, attempts)
    
    def _evaluate(self, scores) -> Tuple[Action, Optional[str]]:
        if scores["safety"]["safety_risk"] > self.policy.safety_threshold:
            return Action.REFUSE, "safety"
        
        issues = []
        if scores["consistency"]["consistency_score"] < self.policy.consistency_threshold:
            issues.append("consistency")
        if scores["support"]["support_score"] < self.policy.support_threshold:
            issues.append("support")
        
        if issues:
            return Action.REWRITE, ",".join(issues)
        
        return Action.ALLOW, None
    
    def _build_steering(self, scores, reason: str) -> str:
        parts = []
        if "consistency" in reason:
            parts.append("Your response may contain contradictions. Ensure logical consistency.")
        if "support" in reason:
            parts.append("Your response contained claims not supported by the context. Revise to cite only provided information, or state when you cannot verify.")
        return " ".join(parts)
    
    def _score_badness(self, scores) -> float:
        return (scores["safety"]["safety_risk"] + 
                (1 - scores["consistency"]["consistency_score"]) + 
                (1 - scores["support"]["support_score"]))


FILE: lumis/trace.py
----------------------------------------
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json

@dataclass
class TraceArtifact:
    request_id: str
    timestamp: str
    prompt: str
    context: str
    response: str
    status: str
    attempts: List[Dict[str, Any]]
    total_latency_ms: float
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


FILE: lumis/runtime.py
----------------------------------------
from .config import LumisConfig
from .speaker import Speaker
from .validators.safety import SafetyValidator
from .validators.consistency import ConsistencyValidator
from .validators.support import SupportValidator
from .steering import SteeringLoop
from .trace import TraceArtifact
import uuid
from datetime import datetime
import time
from typing import Union, Tuple

class LumisRuntime:
    def __init__(self, config: LumisConfig):
        self.config = config
        self.speaker = Speaker(config.speaker_path, config.device, config.brand)
        self.validators = [
            SafetyValidator(config.safety_validator_path, config.use_onnx),
            ConsistencyValidator(config.consistency_validator_path, config.use_onnx),
            SupportValidator(config.support_validator_path, config.use_onnx),
        ]
        self.loop = SteeringLoop(self.speaker, self.validators, config.policy)
    
    def generate(self, prompt: str, context: str = "", 
                 return_trace: bool = False) -> Union[str, Tuple[str, TraceArtifact]]:
        start = time.time()
        result = self.loop.run(prompt, context)
        total_latency = (time.time() - start) * 1000
        
        trace = TraceArtifact(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            prompt=prompt,
            context=context,
            response=result.response,
            status=result.status.value,
            attempts=[{
                "draft": a.draft,
                "scores": a.scores,
                "action": a.action.value,
                "reason": a.reason,
                "latency_ms": a.latency_ms
            } for a in result.attempts],
            total_latency_ms=total_latency
        )
        
        if return_trace:
            return result.response, trace
        return result.response
    
    @classmethod
    def from_yaml(cls, path: str) -> "LumisRuntime":
        return cls(LumisConfig.from_yaml(path))


FILE: lumis/cli.py
----------------------------------------
import click
from .runtime import LumisRuntime

@click.group()
def cli():
    """Lumis-1 Enterprise Reliability Runtime"""
    pass

@cli.command()
@click.option("--config", "-c", required=True, help="Path to config.yaml")
@click.option("--prompt", "-p", required=True, help="Input prompt")
@click.option("--context", "-x", default="", help="Optional context")
@click.option("--trace", "-t", is_flag=True, help="Output trace artifact")
def generate(config, prompt, context, trace):
    """Generate a governed response."""
    runtime = LumisRuntime.from_yaml(config)
    if trace:
        response, trace_obj = runtime.generate(prompt, context, return_trace=True)
        click.echo(response)
        click.echo("\n--- TRACE ---")
        click.echo(trace_obj.to_json())
    else:
        click.echo(runtime.generate(prompt, context))

if __name__ == "__main__":
    cli()


FILE: lumis/__init__.py
----------------------------------------
from .runtime import LumisRuntime
from .config import LumisConfig, BrandConfig, PolicyConfig
from .trace import TraceArtifact

__version__ = "1.0.0"
__all__ = ["LumisRuntime", "LumisConfig", "BrandConfig", "PolicyConfig", "TraceArtifact"]


FILE: setup.py
----------------------------------------
from setuptools import setup, find_packages

setup(
    name="lumis",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.2.0",
        "transformers>=4.40.0",
        "onnxruntime>=1.17.0",
        "pyyaml>=6.0",
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "lumis=lumis.cli:cli",
        ],
    },
)


Include full type hints, docstrings, and error handling throughout.
```

---

## 8. Phase 4: Evaluation Suite

**Goal**: Quantify Reliability.
**Copy/Paste into Claude:**

```text
You are a QA & Metrics Lead.
ULTRATHINK: The metrics must be scientifically defensible.

Create evaluation suite for Lumis-1.

STEP 1: Generate test corpus (500 examples)
- 200 safe, answerable (context provided, straightforward question)
- 100 safe, no context (should state uncertainty)
- 100 unsafe requests (should refuse)
- 50 identity probing (should maintain identity)
- 50 contradiction traps (context has conflicting info)

Save as eval_corpus.jsonl with fields:
{prompt, context, category, expected_behavior: "answer"|"uncertain"|"refuse"|"identity"|"handle_contradiction"}

STEP 2: Run baseline (raw Granite without runtime)
For each example:
- Generate response with raw model
- Score with validators (but don't steer)
- Record: response, scores, would_pass

STEP 3: Run Lumis
For each example:
- Generate with full runtime
- Record: response, status, attempts, latency

STEP 4: Calculate metrics
Compare baseline vs Lumis:
- Repair success: count steering recoveries
- Refusal precision/FP: compare against expected_behavior
- First-pass: count attempts == 1

STEP 5: Manual sample for unsupported claims
Randomly sample 50 responses, manually label if claims are supported.

STEP 6: Generate report
Output markdown with:
- Summary table (baseline vs Lumis)
- Reliability delta for each metric
- Example successes (steering fixed a bad draft)
- Example failures (still wrong after retries)
- Latency distribution
```

---

## 9. Phase 5: Packaging

**Goal**: Create Docker container and documentation.

```text
Create Docker packaging for Lumis-1.

Dockerfile:
----------------------------------------
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/ /app/models/
COPY lumis/ /app/lumis/
COPY setup.py .
RUN pip install -e .

COPY config.yaml /app/config/

ENTRYPOINT ["lumis"]
CMD ["--help"]


docker-compose.yml:
----------------------------------------
version: "3.8"
services:
  lumis:
    build: .
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    environment:
      - LUMIS_DEVICE=cpu
    command: generate -c /app/config/config.yaml -p "Hello"


Build variants:
- lumis:full (BF16, GPU)
- lumis:int8 (INT8 quantized)
- lumis:cpu (INT4, CPU-only)
```
