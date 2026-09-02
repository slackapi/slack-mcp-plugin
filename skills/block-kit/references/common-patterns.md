# Common Block Kit Patterns

> Starting scaffolds for frequent use cases — copy one and customize rather than building from scratch.
> They were valid when written, but the live docs (the skill's **Source of Truth**) remain authoritative for field schemas, and Block Kit evolves. Confirm any field you change against the component's doc page, and re-run the customized payload through `blocks.validate` (Step 5) before shipping.

---

## Approval Message [M]

A notification with context and Approve/Reject buttons.

```json
{
  "channel": "C0123456789",
  "text": "New request from Jane awaiting approval",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "New Approval Request" }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*Requester:* <@U0123456789>\n*Type:* Access request\n*Details:* Production database read access" }
    },
    { "type": "divider" },
    {
      "type": "actions",
      "block_id": "approval_actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Approve" },
          "style": "primary",
          "action_id": "approve_btn",
          "value": "request_123"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Reject" },
          "style": "danger",
          "action_id": "reject_btn",
          "value": "request_123"
        }
      ]
    }
  ]
}
```

**Customization points:** Header text, section fields, button values, adding a confirmation dialog to the Reject button.

---

## Simple Form Modal [V]

A modal with text input, select menu, and optional checkbox.

```json
{
  "type": "modal",
  "callback_id": "feedback_form",
  "title": { "type": "plain_text", "text": "Submit Feedback" },
  "submit": { "type": "plain_text", "text": "Submit" },
  "close": { "type": "plain_text", "text": "Cancel" },
  "blocks": [
    {
      "type": "input",
      "block_id": "category_block",
      "label": { "type": "plain_text", "text": "Category" },
      "element": {
        "type": "static_select",
        "action_id": "category_select",
        "placeholder": { "type": "plain_text", "text": "Choose a category" },
        "options": [
          { "text": { "type": "plain_text", "text": "Bug Report" }, "value": "bug" },
          { "text": { "type": "plain_text", "text": "Feature Request" }, "value": "feature" },
          { "text": { "type": "plain_text", "text": "General Feedback" }, "value": "general" }
        ]
      }
    },
    {
      "type": "input",
      "block_id": "description_block",
      "label": { "type": "plain_text", "text": "Description" },
      "element": {
        "type": "plain_text_input",
        "action_id": "description_input",
        "multiline": true,
        "placeholder": { "type": "plain_text", "text": "Tell us more..." }
      }
    },
    {
      "type": "input",
      "block_id": "urgency_block",
      "label": { "type": "plain_text", "text": "Priority" },
      "element": {
        "type": "radio_buttons",
        "action_id": "urgency_select",
        "options": [
          { "text": { "type": "plain_text", "text": "Low" }, "value": "low" },
          { "text": { "type": "plain_text", "text": "Medium" }, "value": "medium" },
          { "text": { "type": "plain_text", "text": "High" }, "value": "high" }
        ]
      },
      "optional": true
    }
  ]
}
```

**Customization points:** Title, callback_id, input types, options list, adding/removing input blocks.

---

## Notification Alert [M]

An alert banner with description and timestamp context.

```json
{
  "channel": "C0123456789",
  "text": "Alert: Deployment failed for api-gateway",
  "blocks": [
    {
      "type": "alert",
      "text": { "type": "plain_text", "text": "Deployment failed for api-gateway" },
      "level": "error"
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "The deployment to *production* failed during the health check phase.\n\n*Error:* `Connection timeout after 30s`\n*Commit:* `a1b2c3d`" }
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Triggered by <@U0123456789> | <!date^1700000000^{date_short} at {time}|Nov 14, 2023>" }
      ]
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "View Logs" },
          "url": "https://logs.example.com/deploy/456",
          "action_id": "view_logs_btn"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Retry" },
          "style": "primary",
          "action_id": "retry_deploy_btn"
        }
      ]
    }
  ]
}
```

**Customization points:** Level (`info`, `warning`, `error`, `success`), description text, action buttons.

---

## Dashboard Home Tab [H]

A welcome dashboard with metrics fields and quick-action buttons.

```json
{
  "type": "home",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "Welcome to AppName" }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "Here's your overview for today:" }
    },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "*Open Tickets:*\n12" },
        { "type": "mrkdwn", "text": "*Resolved Today:*\n5" },
        { "type": "mrkdwn", "text": "*Avg Response:*\n2.4 hrs" },
        { "type": "mrkdwn", "text": "*SLA Status:*\n:white_check_mark: On Track" }
      ]
    },
    { "type": "divider" },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "New Ticket" },
          "style": "primary",
          "action_id": "new_ticket_btn"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "My Queue" },
          "action_id": "my_queue_btn"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Settings" },
          "action_id": "settings_btn"
        }
      ]
    }
  ]
}
```

**Customization points:** Metrics fields, action buttons, adding image blocks or additional sections.

---

## Confirmation with Dialog [M]

An action button with a confirmation dialog attached (prevents accidental clicks).

```json
{
  "channel": "C0123456789",
  "text": "Server shutdown requested",
  "blocks": [
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "Are you sure you want to shut down *prod-server-01*?" }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Shut Down" },
          "style": "danger",
          "action_id": "shutdown_btn",
          "value": "prod-server-01",
          "confirm": {
            "title": { "type": "plain_text", "text": "Confirm Shutdown" },
            "text": { "type": "plain_text", "text": "This will immediately terminate the server. Active connections will be dropped." },
            "confirm": { "type": "plain_text", "text": "Shut Down" },
            "deny": { "type": "plain_text", "text": "Cancel" },
            "style": "danger"
          }
        }
      ]
    }
  ]
}
```

**Customization points:** Confirmation title/text (title max 100 chars, text max 300 chars, confirm/deny max 30 chars), button style.

---

## Data Table [M]

A structured table for displaying tabular data. Only one table block per message.

```json
{
  "channel": "C0123456789",
  "text": "Team sprint summary",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "Sprint Summary" }
    },
    {
      "type": "table",
      "column_settings": [
        { "is_wrapped": true },
        { "align": "center" },
        { "align": "right" }
      ],
      "rows": [
        [
          { "type": "raw_text", "text": "Name" },
          { "type": "raw_text", "text": "Status" },
          { "type": "raw_text", "text": "Points" }
        ],
        [
          { "type": "raw_text", "text": "Auth refactor" },
          { "type": "raw_text", "text": "In Progress" },
          { "type": "raw_text", "text": "5" }
        ],
        [
          { "type": "raw_text", "text": "API docs update" },
          { "type": "raw_text", "text": "Done" },
          { "type": "raw_text", "text": "2" }
        ],
        [
          { "type": "raw_text", "text": "Bug #1234" },
          { "type": "raw_text", "text": "Blocked" },
          { "type": "raw_text", "text": "3" }
        ]
      ]
    }
  ]
}
```

**Customization points:** Column settings (alignment: `left`/`center`/`right`, wrapping: `is_wrapped`), row data, cell type (`raw_text` for plain content, `rich_text` for formatted content with links/emoji/mentions). Max 100 rows, max 20 cells per row. First row is the header. Only one table block per message.

---

## Settings Modal with Multiple Input Types [V]

A modal combining different input types for a settings/preferences form.

```json
{
  "type": "modal",
  "callback_id": "settings_modal",
  "title": { "type": "plain_text", "text": "Notification Settings" },
  "submit": { "type": "plain_text", "text": "Save" },
  "close": { "type": "plain_text", "text": "Cancel" },
  "blocks": [
    {
      "type": "input",
      "block_id": "channel_block",
      "label": { "type": "plain_text", "text": "Notification Channel" },
      "element": {
        "type": "conversations_select",
        "action_id": "channel_select",
        "default_to_current_conversation": true
      }
    },
    {
      "type": "input",
      "block_id": "frequency_block",
      "label": { "type": "plain_text", "text": "Digest Frequency" },
      "element": {
        "type": "static_select",
        "action_id": "frequency_select",
        "options": [
          { "text": { "type": "plain_text", "text": "Real-time" }, "value": "realtime" },
          { "text": { "type": "plain_text", "text": "Hourly" }, "value": "hourly" },
          { "text": { "type": "plain_text", "text": "Daily" }, "value": "daily" }
        ],
        "initial_option": { "text": { "type": "plain_text", "text": "Daily" }, "value": "daily" }
      }
    },
    {
      "type": "input",
      "block_id": "events_block",
      "label": { "type": "plain_text", "text": "Notify me about" },
      "element": {
        "type": "checkboxes",
        "action_id": "events_checkboxes",
        "options": [
          { "text": { "type": "plain_text", "text": "New deployments" }, "value": "deploys" },
          { "text": { "type": "plain_text", "text": "Failed builds" }, "value": "failures" },
          { "text": { "type": "plain_text", "text": "PR reviews needed" }, "value": "reviews" }
        ]
      }
    },
    {
      "type": "input",
      "block_id": "quiet_hours_block",
      "label": { "type": "plain_text", "text": "Quiet hours start" },
      "element": {
        "type": "timepicker",
        "action_id": "quiet_start",
        "initial_time": "22:00",
        "placeholder": { "type": "plain_text", "text": "Select time" }
      },
      "optional": true
    }
  ]
}
```

**Customization points:** Input types, options, initial values, adding `hint` text to inputs, marking fields as `optional`.

---

## Poll Message [M]

A poll where each option is a section with a Vote button accessory and a running tally. The app updates the message (`chat.update`) as votes arrive.

```json
{
  "channel": "C0123456789",
  "text": "Poll: Where should we hold the team offsite?",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "Where should we hold the team offsite?" }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "Vote by clicking an option. Poll closes *Friday at 5pm*." }
    },
    { "type": "divider" },
    {
      "type": "section",
      "block_id": "poll_option_tahoe",
      "text": { "type": "mrkdwn", "text": "*Lake Tahoe*\n`████████░░` 8 votes" },
      "accessory": {
        "type": "button",
        "text": { "type": "plain_text", "text": "Vote" },
        "action_id": "vote_tahoe",
        "value": "tahoe"
      }
    },
    {
      "type": "section",
      "block_id": "poll_option_portland",
      "text": { "type": "mrkdwn", "text": "*Portland*\n`████░░░░░░` 4 votes" },
      "accessory": {
        "type": "button",
        "text": { "type": "plain_text", "text": "Vote" },
        "action_id": "vote_portland",
        "value": "portland"
      }
    },
    {
      "type": "section",
      "block_id": "poll_option_remote",
      "text": { "type": "mrkdwn", "text": "*Fully remote*\n`█░░░░░░░░░` 1 vote" },
      "accessory": {
        "type": "button",
        "text": { "type": "plain_text", "text": "Vote" },
        "action_id": "vote_remote",
        "value": "remote"
      }
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "13 votes | Created by <@U0123456789> | One vote per person" }
      ]
    }
  ]
}
```

**Customization points:** Options (one section per option), tally rendering (the bar is just `mrkdwn` text — regenerate it and `chat.update` the message on each vote), close date, voting rules in the context footer. For anonymous polls, omit voter names from the tally text.

---

## Multi-Step Wizard Modal [V]

Step 1 of a multi-step modal flow. A context block shows progress, and `submit` reads "Next" instead of a final verb. On submission, the app swaps in the next step's view (`response_action: "update"` from the `view_submission` handler, or `views.update`), carrying collected values forward in `private_metadata`.

```json
{
  "type": "modal",
  "callback_id": "project_wizard_step_1",
  "private_metadata": "{\"step\": 1}",
  "title": { "type": "plain_text", "text": "New Project" },
  "submit": { "type": "plain_text", "text": "Next" },
  "close": { "type": "plain_text", "text": "Cancel" },
  "blocks": [
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "*Step 1 of 3* — Project basics" }
      ]
    },
    {
      "type": "input",
      "block_id": "name_block",
      "label": { "type": "plain_text", "text": "Project name" },
      "element": {
        "type": "plain_text_input",
        "action_id": "project_name",
        "placeholder": { "type": "plain_text", "text": "e.g. Q3 launch" }
      }
    },
    {
      "type": "input",
      "block_id": "type_block",
      "label": { "type": "plain_text", "text": "Project type" },
      "element": {
        "type": "static_select",
        "action_id": "project_type",
        "placeholder": { "type": "plain_text", "text": "Choose a type" },
        "options": [
          { "text": { "type": "plain_text", "text": "Feature launch" }, "value": "launch" },
          { "text": { "type": "plain_text", "text": "Internal tooling" }, "value": "tooling" },
          { "text": { "type": "plain_text", "text": "Research" }, "value": "research" }
        ]
      }
    }
  ]
}
```

**Customization points:** Step count and labels in the context block, inputs per step, a distinct `callback_id` per step so the handler knows which step was submitted. Accumulate earlier answers in `private_metadata` (a string, max 3,000 chars — serialize JSON into it). On the final step, change `submit` to the completing verb (e.g. "Create").

---

## Empty State Home Tab [H]

A first-run Home tab for a user with no data yet: explain what they'll see here, then point them at one primary action. Complements the Dashboard Home Tab, which is the populated version of the same surface.

```json
{
  "type": "home",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "Welcome to AppName" }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "This is your dashboard. Once you create a project, you'll see its status, open tasks, and recent activity here." }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Create your first project" },
          "style": "primary",
          "action_id": "create_first_project_btn"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "View tutorial" },
          "url": "https://example.com/tutorial",
          "action_id": "view_tutorial_btn"
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Questions? Ask in <#C0123456789> or see the <https://example.com/docs|docs>." }
      ]
    }
  ]
}
```

**Customization points:** The explanation text (say what the populated tab will show, not just "nothing here"), the primary action, help links in the context footer. The app decides at `views.publish` time whether to render this or the Dashboard Home Tab.
