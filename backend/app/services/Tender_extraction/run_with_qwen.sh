#!/bin/zsh
# Usage: ./run_with_qwen.sh <input_json> <output_json>

export QWEN_BASE_URL="http://localhost:1234/v1"
export QWEN_API_KEY="lm-studio"
export QWEN_MODEL="qwen2.5-7b-instruct"

INPUT_JSON=${1:-tender_extracted.json}
OUTPUT_JSON=${2:-eligibility_rules1.json}

python3 extract_eligibility_rules.py "$INPUT_JSON" "$OUTPUT_JSON"
