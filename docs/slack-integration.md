# Slack Integration - Documentation

## Overview

The AI Chief of Staff system can automatically send formatted notifications to Slack channels whenever it processes new input. This feature provides real-time visibility into extracted tasks, decisions, and risks.

---

## Features

- **Automatic Notifications**: Sends messages after successful processing
- **Beautiful Formatting**: Uses Slack markdown with emojis and structured layout
- **Error Resilient**: Processing continues even if Slack notification fails
- **Optional**: Can be enabled/disabled via configuration

---

## Setup Instructions

### Step 1: Create a Slack Incoming Webhook

1. Go to https://api.slack.com/messaging/webhooks
2. Click "Create your Slack app"
3. Choose "From scratch"
4. Name your app (e.g., "AI Chief of Staff")
5. Select your workspace
6. Click "Incoming Webhooks"
7. Toggle "Activate Incoming Webhooks" to ON
8. Click "Add New Webhook to Workspace"
9. Select the channel where you want notifications
10. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### Step 2: Configure the System

**Option A: Environment Variable (Recommended)**

```bash
# Add to .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Option B: CLI Argument**

```bash
python -m cli.main --text "..." --slack-webhook "https://hooks.slack.com/services/..."
```

**Option C: API Initialization**

```python
from app.api.controller import init_process

init_process(llm, tools, db, slack_webhook_url="https://hooks.slack.com/services/...")
```

---

## Usage Examples

### CLI with Slack Notifications

```bash
# Using environment variable
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python -m cli.main --text "Schedule meeting with Sarah for Monday at 2pm"

# Using command-line argument
python -m cli.main \
  --text "Schedule meeting with Sarah for Monday at 2pm" \
  --slack-webhook "https://hooks.slack.com/services/..."
```

### API with Slack Notifications

```python
# Initialize with Slack
from app.api.controller import init_process
from app.llm.openai_llm import OpenAILLM

llm = OpenAILLM()
init_process(llm, None, None, slack_webhook_url="https://hooks.slack.com/services/...")

# Process requests - Slack notifications sent automatically
result = processor.process_input("Schedule meeting with Sarah")
```

### Programmatic Usage

```python
from app.tools.slack_tool import SlackTool, format_for_slack
from app.schemas.output_schema import OutputSchema

# Create Slack tool
slack = SlackTool(webhook_url="https://hooks.slack.com/services/...")

# Format your output
message = format_for_slack(result)

# Send to Slack
slack.send_message(message)
```

---

## Message Format

### Full Format (Default)

```
*📌 Tasks:*
- Schedule meeting with Sarah (Owner: John, Deadline: Monday at 2:00 PM)
- Prepare agenda for the meeting (Owner: None, Deadline: None)

*🧠 Decisions:*
- Budget approved at $50,000 for Q2 marketing campaign (By: Finance Team)
- Meeting scheduled for Monday at 2:00 PM (By: Sarah)

*⚠️ Risks:*
- Sarah may not be available for Monday meeting [Severity: medium]
- Budget allocation unclear for specific campaigns [Severity: high]

*📝 Summary:*
Schedule meeting with Sarah for Monday at 2:00 PM with agenda...
```

### Compact Format (Optional)

```python
from app.tools.slack_tool import format_for_slack_compact

message = format_for_slack_compact(result)
```

Output:
```
*🤖 AI Chief of Staff:* 2 tasks, 2 decisions, 3 risks

*Top Tasks:*
• Schedule meeting with Sarah
• Prepare agenda for the meeting
```

---

## Configuration

### Environment Variables

```bash
# .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

### Processor Initialization

```python
processor = AIChiefOfStaffProcessor(
    llm=llm,
    tools=tools,
    db=db,
    slack_webhook_url="https://hooks.slack.com/services/..."  # Optional
)
```

If `slack_webhook_url` is `None` or not provided, Slack notifications are disabled.

---

## Testing

### Test Formatter (No Network Calls)

```bash
python -c "
from app.tools.slack_tool import format_for_slack
from test_slack import create_sample_output

sample = create_sample_output()
message = format_for_slack(sample)

with open('test_message.txt', 'w', encoding='utf-8') as f:
    f.write(message)

print('Formatted message saved to test_message.txt')
"
```

### Test with Mock Webhook (Safe)

```bash
python test_slack.py
```

Output:
```
TESTING SLACK FORMATTER
...
Mock mode - No message will be sent to Slack
```

### Test with Real Slack (Sends Actual Message)

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python test_slack.py --real
```

---

## Error Handling

The system is designed to be resilient:

1. **Invalid Webhook URL**: Logs warning, processing continues
2. **Network Failure**: Logs error, processing continues
3. **Slack API Error**: Logs error with response details, processing continues

**Important**: Slack notification failures **never** prevent the main processing pipeline from completing successfully.

### Log Examples

**Success**:
```
INFO - [run_id] Sending Slack notification...
INFO - [run_id] Slack notification sent successfully
```

**Failure**:
```
ERROR - [run_id] Failed to send Slack notification: Connection timeout
```

---

## Customization

### Custom Formatter

Create your own formatter function:

```python
def my_custom_formatter(output: OutputSchema) -> str:
    lines = []
    lines.append(f"*New Processing Result*")
    lines.append(f"Tasks: {len(output.tasks)}")
    lines.append(f"Quality: {'High' if len(output.tasks) > 2 else 'Low'}")
    return "\n".join(lines)

# Use it
from app.tools.slack_tool import SlackTool

slack = SlackTool(webhook_url="...")
message = my_custom_formatter(result)
slack.send_message(message)
```

### Adding Rich Formatting

Slack supports:
- `*bold*`
- `_italic_`
- `~strikethrough~`
- `` `code` ``
- `> blockquote`
- Emojis: `:thumbsup:` or 👍

Example:
```python
def format_with_blocks(output: OutputSchema) -> str:
    return f"""
*🚀 New Task Processing Complete*

> {output.summary}

*Stats:*
• Tasks: {len(output.tasks)}
• Decisions: {len(output.decisions)}
• Risks: {len(output.risks)}

_Processed at {output.metadata.processed_at}_
"""
```

---

## Troubleshooting

### Issue: No Messages Received

**Check:**
1. Webhook URL is correct
2. App is installed in workspace
3. Channel permissions are correct
4. Network allows HTTPS to `hooks.slack.com`

**Test:**
```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'
```

### Issue: Messages Look Broken

**Cause**: Slack markdown rendering issues

**Solution**:
- Use `*bold*` not `**bold**`
- Use single emojis, not emoji codes
- Avoid complex nested formatting

### Issue: Too Many Notifications

**Solution**:
- Disable Slack for CLI: Don't set `SLACK_WEBHOOK_URL`
- Conditional sending:
```python
def _send_slack_notification(self, result, run_id):
    # Only send for high-priority tasks
    if any(t.priority == "high" for t in result.tasks):
        ...send notification...
```

---

## Performance

### Message Size Limits

- Slack message limit: 40,000 characters
- Our summary truncation: 200 characters
- Typical message size: 500-1000 characters

### Latency

- Slack API call: 100-500ms
- Does **not** block processing pipeline
- Network timeout: 10 seconds

---

## Security

### Best Practices

1. **Never commit webhook URLs to git**
   ```bash
   # Add to .gitignore
   .env
   ```

2. **Rotate webhooks periodically**
   - Delete old webhooks in Slack app settings
   - Generate new ones every 6 months

3. **Limit channel access**
   - Use private channels for sensitive data
   - Review channel member list regularly

4. **Sanitize input**
   - System already validates all fields
   - No user input directly in Slack messages

---

## Integration with Other Tools

### Jira/Asana

```python
# After sending Slack notification
if slack_sent:
    # Create Jira ticket
    for task in result.tasks:
        jira.create_issue(
            summary=task.title,
            description=f"Owner: {task.owner}\nDeadline: {task.deadline}"
        )
```

### Email

```python
# Send email AND Slack
message = format_for_slack(result)
slack.send_message(message)
email.send(to="team@company.com", body=message)
```

### Webhooks

```python
# Trigger other systems
webhook.send("https://your-system.com/api/tasks", data=result.model_dump())
slack.send_message(format_for_slack(result))
```

---

## Future Enhancements

Planned features:

1. **Interactive Buttons**: Mark tasks as complete from Slack
2. **Threaded Responses**: Reply to Slack message with updates
3. **Rich Blocks**: Use Slack's Block Kit for better UX
4. **Channel Routing**: Different channels for tasks vs risks
5. **Mention Users**: `@john` for task owners
6. **Attachments**: Include full JSON as file attachment

---

## Example Workflows

### Daily Standup Automation

```bash
# Cron job: 9am daily
0 9 * * * python -m cli.main \
  --text "$(cat daily_updates.txt)" \
  --slack-webhook "$SLACK_WEBHOOK_URL"
```

### Meeting Notes Processing

```bash
# After meeting ends
python -m cli.main \
  --text "$(cat meeting_transcript.txt)" \
  --output meeting_tasks.json \
  --slack-webhook "$SLACK_WEBHOOK_URL"
```

### Email Monitoring

```python
# Process incoming emails
for email in inbox.unread():
    result = processor.process_input(email.body)
    # Slack notification sent automatically
    email.mark_read()
```

---

## FAQ

**Q: Can I send to multiple channels?**
A: Yes, create multiple webhooks and send to each:
```python
slack1.send_message(message)  # #general
slack2.send_message(message)  # #tasks
```

**Q: Can I disable Slack for specific requests?**
A: Yes, use a processor without Slack:
```python
processor_no_slack = AIChiefOfStaffProcessor(llm, tools, db, slack_webhook_url=None)
```

**Q: Does Slack cost money?**
A: Incoming webhooks are free on all Slack plans.

**Q: Can I use this with Microsoft Teams?**
A: Yes, Teams has similar incoming webhooks. Create a `TeamsTools` following the same pattern.

---

## Support

For issues or questions:
- Check logs for error messages
- Test webhook with `curl` first
- Verify environment variables are set
- See [Troubleshooting](#troubleshooting) section

---

**Last Updated:** 2026-04-15
**Version:** 1.0.0
**Status:** Production-Ready
