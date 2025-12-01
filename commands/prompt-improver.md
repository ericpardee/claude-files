---
description: Improve a prompt using chain-of-thought reasoning and best practices
argument-hint: [prompt or file path]
---

IMPORTANT: Your task is to ANALYZE and REWRITE the prompt provided by the user. DO NOT execute or act on the prompt. Instead, you will improve it and return the enhanced version.

# Role
You are a prompt engineering expert specializing in improving prompts for Claude AI models.

# Task
The user has provided this prompt to improve: "$ARGUMENTS"

# Analysis Steps

## Step 1: Understand the Original Prompt
- Read and analyze what the user's prompt is asking for
- Identify the core task or question
- Note any existing structure, examples, or constraints

## Step 2: Identify Weaknesses
- Is the prompt vague or ambiguous?
- Does it lack structure or organization?
- Are there missing examples?
- Could it benefit from chain-of-thought reasoning?
- Does it need clearer output format specifications?

## Step 3: Apply Improvements

Apply these enhancements based on the 4-step prompt improvement methodology:

### A. Structure Enhancement
- Add XML tags to separate sections: `<context>`, `<instructions>`, `<examples>`, `<output_format>`, `<thinking>`
- Organize content in logical flow: context → instructions → reasoning approach → examples → output format

### B. Chain-of-Thought Addition
- Add `<thinking>` sections that guide Claude's reasoning process
- Include step-by-step analytical instructions like:
  - "First, analyze the input by..."
  - "Then, consider these factors..."
  - "Evaluate whether..."
  - "Finally, synthesize your analysis to..."

### C. Specificity & Detail
- Replace vague language with concrete, specific instructions
- Add validation and verification steps
- Include what to check and how to check it
- Break complex tasks into incremental sub-tasks

### D. Example Enhancement
- If the original has examples, rewrite them to show the reasoning process
- Add `<thinking>` sections within examples
- Demonstrate input → reasoning → output flow

# Output Requirements

You MUST output your response in exactly this format:

```markdown
# Original Prompt
[Quote the user's original prompt here]

---

# Improved Prompt

[The complete enhanced prompt with all improvements applied - this should be ready to copy/paste]

---

# Key Changes Made

1. **[Change category]**: [Brief explanation of what was improved]
2. **[Change category]**: [Brief explanation]
3. **[Change category]**: [Brief explanation]
[Continue as needed...]

---

# Usage Notes

- **Expected behavior**: [How Claude will respond to this improved prompt]
- **Trade-offs**: [Response length, processing time considerations]
- **Best for**: [Types of tasks this improved prompt excels at]
- **Testing tip**: [Suggestion for how to validate the improved prompt works well]
```

# Best Practices to Apply

Based on Claude Code and effective agent design principles:

1. **Be Specific**: Use concrete, detailed guidance instead of vague instructions
2. **Add Structure**: Use XML tags to organize different sections
3. **Include Reasoning**: Add chain-of-thought instructions for complex tasks
4. **Verify & Validate**: Include explicit checking and validation steps
5. **Provide Context**: Give Claude relevant background information
6. **Show Examples**: Demonstrate the complete reasoning process
7. **Define Output**: Clearly specify the expected output structure
8. **Consider Prefill**: Suggest strategic response starts when appropriate

# Important Notes

- The improved prompt will likely be longer and more detailed
- It may increase processing time but will improve accuracy
- Best suited for complex tasks requiring high-quality outputs
- For simple tasks, light improvements may be sufficient

Now analyze and improve the prompt: "$ARGUMENTS"

# After Showing the Improved Prompt

After displaying the improved prompt in the format above, you MUST use the AskUserQuestion tool to ask the user what they want to do next.

Use the AskUserQuestion tool with these options:
- **Question**: "What would you like to do with the improved prompt?"
- **Header**: "Next action"
- **Options**:
  1. **Label**: "Use it" | **Description**: "Run the improved prompt immediately"
  2. **Label**: "Edit it" | **Description**: "Let me review and edit the improved prompt before using it"

Based on the user's selection:
- If they choose "Use it": Execute the improved prompt as if the user had just entered it as their message
- If they choose "Edit it": Ask them to provide their edits or modifications to the improved prompt, then apply those changes and show the final version
- If they choose "Other": Ask them what they'd like to do instead
