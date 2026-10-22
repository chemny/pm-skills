---
name: summarize-interview
description: "Summarize a customer interview transcript into a structured template with JTBD, satisfaction signals, and action items. Use when processing interview recordings or transcripts, synthesizing discovery interviews, or creating interview summaries."
scenarios: ["帮我把这段访谈录音整理成结构", "提炼下这次用户访谈的关键信息", "把访谈转成JTBD和行动项"]
---

## Summarize Customer Interview

Transform an interview transcript into a structured summary focused on Jobs to Be Done, satisfaction, and action items.

### Context

You are summarizing a customer interview for the product discovery of **$ARGUMENTS**.

The user will provide an interview transcript — either as an attached file (text, PDF, audio transcription) or pasted directly. Read any attached files first.

### Instructions

1. **Read the full transcript** carefully before summarizing.

2. **Fill in the summary template** below. Use "-" if information is unavailable. Replace numeric values with qualitative descriptions if needed (e.g., "not satisfied").

3. **Use clear, simple language** — a primary school graduate should be able to understand the summary.

### Output Template

```
**Date**: [Date and time of the interview]
**Participants**: [Full names and roles]
**Background**: [Background information about the customer]

**Current Solution**: [What solution they currently use]

**What They Like About Current Solution**:
- [Job to be done, desired outcome, importance, and satisfaction level]

**Problems With Current Solution**:
- [Job to be done, desired outcome, importance, and satisfaction level]

**Key Insights**:
- [Unexpected findings or notable quotes]

**Action Items**:
- [Date, Owner, Action — e.g., "2025-01-15, 张三, Follow up with customer about pricing"]
```

Save the summary as a markdown document in the user's workspace.
