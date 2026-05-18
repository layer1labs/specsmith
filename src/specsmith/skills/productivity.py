# SPDX-License-Identifier: MIT
"""Productivity skills — email, presentations, Office suites, tools."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="email-workflow",
        name="Email — professional writing, templates, inbox zero, automation",
        description=(
            "Effective email workflow: professional writing principles, "
            "template library, inbox-zero system, filters, and automation."
        ),
        domain=SkillDomain.PRODUCTIVITY,
        tags=[
            "email",
            "communication",
            "templates",
            "inbox-zero",
            "gmail",
            "outlook",
            "automation",
            "productivity",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# Email Workflow Skill

## Professional writing principles
1. **Subject line**: Specific + action-oriented.
   "Action required: approve Q3 budget by Fri 5pm" > "Budget"
2. **First sentence**: State what you need in ≤ 20 words.
3. **BLUF** (Bottom Line Up Front): conclusion → supporting details → call to action.
4. **Length**: < 150 words for requests; < 300 words for updates. Longer = send a doc instead.
5. **One ask per email**: multiple asks get partial responses.
6. **Deadline**: always include "by [DATE/TIME]" for action items.

## Email templates

### Meeting request
```
Subject: [30 min] Sync on [Topic] — can you do [DATE]?

Hi [Name],

I'd like to discuss [1-sentence topic]. Would [DAY] at [TIME] work?
If not, here are 3 alternatives: [link to Calendly or dates].

The goal: [outcome]. I'll send an agenda 24h before.

[Your name]
```

### Status update
```
Subject: [Project] update — week of [DATE]

✅ Done: [bullet list]
🔄 In progress: [bullet list]
⚠️  Blockers: [if any — what you need and from whom]
📅 Next: [what you'll do next week]

Full details: [link to doc/tracker]
```

### Escalation
```
Subject: ESCALATION: [Issue] — need decision by [DATE]

Background: [2 sentences max]
Impact: [quantified — "$X revenue at risk" / "Y users affected"]
Decision needed: [specific choice with options A/B/C]
Deadline: [DATE] — after this, I'll proceed with [default action].

I can jump on a call: [availability].
```

## Inbox zero system
1. **Process email 2× per day** (9 AM + 3 PM) — turn off notifications.
2. **4D rule**: Do (< 2 min), Delegate, Defer (add to task list), Delete/Archive.
3. **Labels/Folders**: `@Action`, `@Waiting`, `@Reference` — no project-per-folder.
4. **Filters**: auto-archive newsletters to `@Reference`; auto-label team emails.
5. **Snooze**: use for emails needing follow-up at specific time.

## Gmail automation (Google Apps Script)
```javascript
// Auto-label emails from key senders
function labelKeyEmails() {
  var label = GmailApp.createLabel("@Team");
  var threads = GmailApp.search('from:(@company.com) is:unread');
  threads.forEach(t => t.addLabel(label));
}
```

## Common pitfalls
- Reply-All to large groups: use BCC for distribution lists.
- Emotional emails: write it, save as draft, review in 1 hour before sending.
- CC inflation: CC = FYI only; TO = action required.
- Email is not a task manager: move action items to your task system immediately.
""",
    ),
    SkillEntry(
        slug="presentations",
        name="Presentations — slide structure, storytelling, Gamma.ai, PowerPoint",
        description=(
            "Presentation skills: story arc structure, slide design principles, "
            "Gamma.ai AI generation, PowerPoint/Keynote, and delivery tips."
        ),
        domain=SkillDomain.PRODUCTIVITY,
        tags=[
            "presentations",
            "slides",
            "powerpoint",
            "keynote",
            "gamma",
            "storytelling",
            "pitching",
            "design",
            "communication",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# Presentations Skill

## Story arc (the universal structure)
```
1. SITUATION   — What is the context? (1 slide)
2. COMPLICATION — What changed or is the problem? (1-3 slides)
3. RESOLUTION  — Your solution/recommendation (main body)
4. CALL TO ACTION — What do you need from the audience? (1 slide)

Minto Pyramid: Lead with your recommendation, then support it.
"We should do X. Here's why: A, B, C."
Not: "We found A, and B, and C, so we recommend X."
```

## Slide design principles
- **One idea per slide**: if you need "and" to describe a slide, split it.
- **6×6 rule**: max 6 bullets, max 6 words per bullet.
- **Contrast**: dark text on light background or vice versa (check accessibility).
- **Whitespace**: 30-40% of slide area should be empty.
- **Consistent typography**: 2 fonts max (title + body); 24px+ body text.
- **Data visualisation**: bar charts > pie charts; label directly on chart.
- **Images**: full-bleed photos are more impactful than clip art.

## Gamma.ai (AI-powered deck generation)
```
1. go to gamma.app → New → Generate
2. Paste outline or prompt: "Investor pitch for [company], [product], [market], [ask]"
3. Select theme + length
4. Review generated deck: edit text, swap images, rearrange cards
5. Present directly (browser-based) or export to PowerPoint/PDF

Best uses:
- First-draft outline from bullet points
- Quick status update decks
- Internal team updates

Always refine: fix brand colours, swap stock photos, personalise examples.
```

## PowerPoint keyboard shortcuts (Windows)
```
F5          Start presentation from beginning
Shift+F5    Start from current slide
B           Blank screen during presentation
W           White screen during presentation
Ctrl+D      Duplicate slide
Ctrl+G      Group shapes
Alt+F10     Selection pane (layer management)
```

## Keynote shortcuts (macOS)
```
⌘P          Play presentation
⌘⌥P         Play from current slide
⌘D          Duplicate slide
⌘⌥G         Group objects
```

## LibreOffice Impress
```bash
soffice --impress presentation.pptx   # open in Impress
soffice --headless --convert-to pdf presentation.pptx  # convert to PDF
soffice --headless --convert-to pptx presentation.odp  # convert to PPTX
```

## Delivery tips
- **Rehearse 3×**: once to yourself, once to a colleague, once as full run.
- **Rule of thirds**: spend 1/3 time on problem, 1/3 on solution, 1/3 on impact.
- **Pause**: 2-second pause after key points; silence = confidence.
- **Backup**: always have PDF version in case of font/animation issues.
- **Send deck before**: "Here's the deck for tomorrow — come with questions."

## Common pitfalls
- Death by PowerPoint: > 20 slides for 30 min = too many.
- Reading slides verbatim: slides are visual aid, not script.
- Small fonts: everyone in the room must read it without squinting.
- Animation overuse: entrance animations for every bullet = distraction.
""",
    ),
    SkillEntry(
        slug="office-productivity",
        name="MS Office/LibreOffice — Excel, Word, macros, cross-platform tips",
        description=(
            "Office suite productivity: Excel formulas and Power Query, "
            "Word document automation, macro scripting, and LibreOffice equivalents."
        ),
        domain=SkillDomain.PRODUCTIVITY,
        tags=[
            "excel",
            "word",
            "powerpoint",
            "libreoffice",
            "macros",
            "vba",
            "spreadsheet",
            "office",
            "automation",
            "pivot",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# Office Productivity Skill

## Excel essentials

### Power formulas
```excel
# VLOOKUP (use XLOOKUP instead in Excel 2019+)
=XLOOKUP(A2, Products!A:A, Products!C:C, "Not found")

# Dynamic array — spill to multiple cells
=FILTER(A2:C100, B2:B100="Active")   # filter rows
=SORT(A2:A100, 1, -1)                 # sort descending
=UNIQUE(D2:D100)                       # deduplicate

# Named range best practice (Formulas → Define Name)
=SUM(Revenue)    # easier to read than =SUM(B2:B1000)

# Table formula (structured references)
=SUM(Table1[Revenue])    # auto-expands with table

# Date formulas
=EOMONTH(A2, 0)           # last day of month
=NETWORKDAYS(A2, B2)      # business days between dates
=TEXT(A2, "YYYY-MM-DD")   # format as string
```

### Power Query (Get & Transform)
```
Data → Get Data → From File / From Database / From Web
1. Load data source
2. Transform: remove columns, filter rows, unpivot, merge queries
3. Load to sheet or data model
Key: Power Query steps are recorded and refreshable — no manual ETL!
```

### PivotTable workflow
```
1. Format source data as Table (Ctrl+T)
2. Insert → PivotTable → New worksheet
3. Drag: Rows (category), Columns (time), Values (numbers), Filters
4. Refresh: right-click → Refresh (or Data → Refresh All)
5. Calculated field: PivotTable Analyze → Fields, Items → Calculated Field
```

## Word automation
```
Styles: Heading 1/2/3 → auto-generates table of contents
Table of Contents: References → Table of Contents → Automatic
Track Changes: Review → Track Changes (Ctrl+Shift+E)
Comments: Insert → Comment (Ctrl+Alt+M) — for review workflows
Mail Merge: Mailings → Start Mail Merge → connect data source
Cross-reference: Insert → Cross-reference → Heading/Figure/Table number
```

## VBA macro (Excel example)
```vba
Sub FormatReport()
    Dim ws As Worksheet
    Set ws = ActiveSheet

    ' Bold header row
    ws.Rows(1).Font.Bold = True

    ' Auto-fit columns
    ws.Columns.AutoFit

    ' Add border to used range
    With ws.UsedRange.Borders
        .LineStyle = xlContinuous
        .Weight = xlThin
    End With

    ' Save
    ActiveWorkbook.Save
    MsgBox "Done!"
End Sub
```
```
Tools → Macros → Record Macro → stop → edit in VBA Editor (Alt+F11)
Assign macro to button: Developer → Insert → Button
```

## LibreOffice equivalents
```bash
# LibreOffice CLI
libreoffice --calc myspreadsheet.xlsx            # open Calc
libreoffice --writer report.docx                  # open Writer
libreoffice --headless --convert-to csv data.xlsx  # batch convert
libreoffice --headless --convert-to xlsx data.ods  # convert to XLSX

# Macros: Tools → Macros → Organize Basic Macros
# LibreOffice Basic is similar to VBA
Sub Hello()
    MsgBox "Hello LibreOffice"
End Sub
```

## Cross-platform tips
- Save as `.xlsx`, `.docx`, `.pptx` for maximum compatibility.
- LibreOffice on Linux/macOS: `sudo apt install libreoffice` or `brew install libreoffice`.
- Google Sheets: for collaboration; use `.gs` (Apps Script) for automation.
- macOS Numbers/Pages: import `.xlsx`/`.docx` well; export for cross-compatibility.

## Common pitfalls
- Excel dates on Mac vs Windows: 1900 vs 1904 date system (rare but causes 4-year offset).
- Merged cells: avoid — break sorting, filtering, and Power Query.
- `=` in CSV: prefix with `'` to prevent formula injection.
""",
    ),
]
