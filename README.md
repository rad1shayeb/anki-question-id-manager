# Anki Question ID Manager for Medical Students

![Add-on Demo](https://via.placeholder.com/800x400.png?text=Add-on+Screenshot+Demonstration)

🔍 **View UWorld Step 2 question IDs directly from Anki card tags** 

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration) 
- [Regex Patterns](#regex-patterns)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### For End Users
1. Download latest `.ankiaddon` from [Releases](https://github.com/rad1shayeb/anki-question-id-manager/releases)
2. Open Anki → Tools → Add-ons → "Install from File"
3. Select downloaded `.ankiaddon` file

### For Developers
```bash
# Clone repository to Anki addons folder
cd C:\Users\YOURUSERNAME\AppData\Roaming\Anki2\addons21
git clone https://github.com/rad1shayeb/anki-question-id-manager.git qid_display_addon_for_medical_student
```

## Usage
Works for retrieving UWorld Step2 question IDs (tag) for Anki cards of the deck Anking v12 (tested only for v12)
1. Open any card in review mode
2. Navigate to: Tools → Question ID Manager
3. Interface shows:
   - Current card's detected IDs
   - Active regex patterns
   - Debug status

## Configuration

Edit `config.json` in addon folder:
```json
{
    "enabled": true,
    "debug_mode": false,
    "tag_patterns": [
        "::\\d+$",
        "#AK_Step2_v\\d+::\\d+",
        "#QID\\d+"
    ]
}
```

## Regex Patterns

### Default Patterns
| Pattern          | Matches                          | Example Tag                          |
|------------------|----------------------------------|--------------------------------------|
| `::\\d+$`        | IDs at end of hierarchy          | `#AK_Step2_v12::#UWorld::Step::12136` |
| `#AK_Step2_v\\d+::\\d+` | AK Step 2 formatted IDs      | `#AK_Step2_v11::#Pathoma::CH03::4512` |
| `#QID\\d+`       | Simple QID format                | `#QID12345`                          |

### Custom Patterns
1. Open config menu (Tools → Question ID Manager)
2. Add pipe-separated regex:
   ```text
   #CustomID\\d+|::[A-Z]+-\d+ 
   ```
3. Click "Save Settings"

## Troubleshooting

### IDs Not Showing?
1. Verify tags exist in note (Browser → check Tags column)
2. Ensure patterns match tag structure
3. Check `qid_addon.log` for errors:
   ```bash
   C:\Users\YOURUSERNAME\AppData\Roaming\Anki2\addons21\qid_display_addon_for_medical_student\qid_addon.log
   ```

### Common Errors
| Error                          | Solution                          |
|--------------------------------|-----------------------------------|
| "No IDs found"                 | Add matching regex pattern        |
| "Invalid regex"                | Validate pattern at regex101.com  |
| "Add-on not loading"           | Check Anki version ≥ 2.1.50       |

## Contributing

### For Medical Educators
1. Report clinical tagging needs via [Issues](https://github.com/rad1shayeb/anki-question-id-manager/issues)
2. Suggest common medical ID formats

### For Developers
1. Fork repository
2. Create feature branch:
   ```bash
   git checkout -b feature/new-regex-handling
   ```
3. Commit changes:
   ```bash
   git commit -m "feat: add support for Amboss QIDs"
   ```
4. Push to branch:
   ```bash
   git push origin feature/new-regex-handling
   ```
5. Open Pull Request



---


*Maintained by Radwan Shayeb*
4th year medical student at An-Najah National University
shayebradwan@gmail.com