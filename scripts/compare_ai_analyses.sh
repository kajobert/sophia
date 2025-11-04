#!/bin/bash
# 📊 AI Analysis Results Collector
# Purpose: Compare analyses from different AI models

echo "🤖 AI Analysis Comparison Tool"
echo "================================"
echo ""

# Check if analysis files exist
ANALYSIS_FILES=(docs/analysis-*.md)

if [ ! -f "${ANALYSIS_FILES[0]}" ]; then
    echo "❌ No analysis files found in docs/"
    echo ""
    echo "📝 To create analyses:"
    echo "   1. Open new chat with AI model (GPT-4, Claude, Gemini, etc.)"
    echo "   2. Copy prompt from: docs/AI_ANALYSIS_PROMPT_QUICK.md"
    echo "   3. Let AI create analysis-{model-name}.md file"
    echo "   4. Repeat with different models"
    echo ""
    exit 1
fi

# Count analyses
NUM_ANALYSES=$(ls -1 docs/analysis-*.md 2>/dev/null | wc -l)
echo "📁 Found $NUM_ANALYSES analysis files:"
echo ""

for file in docs/analysis-*.md; do
    if [ -f "$file" ]; then
        model_name=$(basename "$file" .md | sed 's/analysis-//')
        echo "   - $model_name"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract ratings from each analysis
echo "⭐ RATINGS COMPARISON"
echo ""
printf "%-20s | %-12s | %-12s | %-12s | %-12s | %-12s\n" \
    "Model" "Architecture" "Code" "Tests" "Prod Ready" "OVERALL"
echo "-------------------|------------|------------|------------|------------|------------"

for file in docs/analysis-*.md; do
    if [ -f "$file" ]; then
        model_name=$(basename "$file" .md | sed 's/analysis-//')
        
        # Extract ratings (assuming format: "- Architecture Quality: X/10")
        arch=$(grep -i "Architecture.*Quality.*:" "$file" | grep -oP '\d+/10' | head -1 || echo "?/10")
        code=$(grep -i "Code.*Quality.*:" "$file" | grep -oP '\d+/10' | head -1 || echo "?/10")
        tests=$(grep -i "Test.*Coverage.*:" "$file" | grep -oP '\d+/10' | head -1 || echo "?/10")
        prod=$(grep -i "Production.*Readiness.*:" "$file" | grep -oP '\d+/10' | head -1 || echo "?/10")
        overall=$(grep -i "Overall.*Health.*:" "$file" | grep -oP '\d+/10' | head -1 || echo "?/10")
        
        printf "%-20s | %-12s | %-12s | %-12s | %-12s | %-12s\n" \
            "$model_name" "$arch" "$code" "$tests" "$prod" "$overall"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract top priority items
echo "🔴 TOP PRIORITY ITEMS (Tier 1 Blockers)"
echo ""

for file in docs/analysis-*.md; do
    if [ -f "$file" ]; then
        model_name=$(basename "$file" .md | sed 's/analysis-//')
        echo "[$model_name]"
        
        # Extract Tier 1 items (between "TIER 1" and "TIER 2")
        sed -n '/TIER 1.*BLOCKER/,/TIER 2/p' "$file" | grep -E '^\s*[0-9]+\.' | head -5
        echo ""
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract success probabilities
echo "🎯 SUCCESS PROBABILITY"
echo ""

for file in docs/analysis-*.md; do
    if [ -f "$file" ]; then
        model_name=$(basename "$file" .md | sed 's/analysis-//')
        prob=$(grep -i "Probability.*achieving.*autonomy.*:" "$file" | grep -oP '\d+%' | head -1 || echo "?%")
        
        printf "%-20s : %s\n" "$model_name" "$prob"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count consensus on critical issues
echo "🤝 CONSENSUS ANALYSIS"
echo ""
echo "Issues mentioned by multiple models:"
echo ""

# Extract all issue titles and count occurrences
temp_issues=$(mktemp)
for file in docs/analysis-*.md; do
    if [ -f "$file" ]; then
        grep -E "^###.*Issue.*:" "$file" | sed 's/^###.*Issue.*: //' >> "$temp_issues"
    fi
done

# Count and sort
sort "$temp_issues" | uniq -c | sort -rn | head -10 | while read count issue; do
    if [ "$count" -gt 1 ]; then
        echo "   [$count/$NUM_ANALYSES models] $issue"
    fi
done

rm "$temp_issues"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
echo "📝 NEXT STEPS"
echo ""
echo "1. Read each full analysis in docs/analysis-*.md"
echo "2. Look for consensus (what ALL models agree on)"
echo "3. Investigate conflicts (where models disagree)"
echo "4. Create final plan: docs/FINAL_STABILIZATION_PLAN.md"
echo "5. Start implementation with confidence!"
echo ""
echo "💡 Tip: Issues mentioned by 3+ models are likely REAL and IMPORTANT"
echo ""
