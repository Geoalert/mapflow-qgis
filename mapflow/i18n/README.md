# Internationalization (i18n) Guide for Mapflow QGIS Plugin

## Overview

This plugin uses Qt's internationalization system to support multiple languages. Currently supported:
- **English** (source language - `en_US`)
- **Russian** (`ru_RU`) - `mapflow_ru.ts`

## File Structure

```
i18n/
├── README.md              # This file
├── mapflow.pro            # Qt Linguist project file (lists all source files)
├── mapflow_ru.ts          # Russian translation source (XML format)
└── mapflow_ru.qm          # Russian compiled translation (binary)
```

## How Translation Works

1. **Source strings** - All translatable strings in Python code use `self.tr("Text")` or `QCoreApplication.translate(context, "Text")`
2. **Translation files (.ts)** - XML files containing source strings and their translations
3. **Compiled translations (.qm)** - Binary files loaded at runtime by the plugin
4. **Auto-detection** - Plugin automatically loads translations based on QGIS locale settings

## Adding a New Language

### Step 1: Update mapflow.pro

Add your new translation file to the `TRANSLATIONS` line in `mapflow.pro`:

```pro
TRANSLATIONS = mapflow_ru.ts mapflow_fr.ts mapflow_es.ts
```

Replace `fr` and `es` with your language codes (e.g., `de` for German, `ja` for Japanese).

### Step 2: Generate Translation Template

Run lupdate to extract all translatable strings from the source code:

```bash
cd i18n
pylupdate5 mapflow.pro
```

This creates/updates `.ts` files with all strings found in:
- Python source files (listed in `SOURCES`)
- UI files (listed in `FORMS`)

### Step 3: Translate Strings

Open the `.ts` file with Qt Linguist (recommended) or a text editor:

**Using Qt Linguist (GUI - Recommended):**
```bash
linguist mapflow_fr.ts
```

**Or edit manually (XML format):**
```xml
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="324"/>
        <source>Draw AOI at the map</source>
        <translation>Dessiner la zone d'intérêt sur la carte</translation>
    </message>
</context>
```

### Step 4: Compile Translations

After translating, compile the `.ts` file to `.qm` (binary format):

```bash
lrelease mapflow_fr.ts
```

This generates `mapflow_fr.qm` which the plugin will load at runtime.

### Step 5: Test Your Translation

1. Copy the `.qm` file to the `i18n/` directory
2. Restart QGIS
3. Change QGIS language: Settings → Options → General → User Interface Translation
4. Restart QGIS and open the plugin

## For Developers: Making Strings Translatable

### In Python Code

#### For QWidget/QDialog classes (dialogs):
```python
# These inherit tr() from Qt
self.setWindowTitle(self.tr("My Dialog"))
```

#### For QObject classes (services, controllers, views):
```python
class MyService(QObject):
    def tr(self, message: str) -> str:
        """Translate string for i18n support."""
        from PyQt5.QtCore import QCoreApplication
        return QCoreApplication.translate('MyService', message)
    
    def some_method(self):
        text = self.tr("Translatable text")
```

#### For standalone functions/classes without QObject:
```python
from PyQt5.QtCore import QCoreApplication

def my_function():
    text = QCoreApplication.translate('ModuleName', "Text to translate")
```

### In UI Files

UI files created with Qt Designer automatically support translation. All visible text properties (labels, button text, tooltips, etc.) are extracted by `lupdate`.

### Best Practices

1. **Use descriptive contexts** - The context name (class name) helps translators understand the usage
2. **Avoid string concatenation** - Use format strings:
   ```python
   # Good
   self.tr("Processing {name} completed").format(name=proc_name)
   
   # Bad (harder to translate)
   self.tr("Processing ") + proc_name + self.tr(" completed")
   ```

3. **Keep strings complete** - Don't split sentences:
   ```python
   # Good
   self.tr("Click OK to continue or Cancel to abort")
   
   # Bad
   self.tr("Click") + " OK " + self.tr("to continue")
   ```

4. **Add comments for context** when ambiguous:
   ```python
   # TRANSLATORS: This is a button label
   self.tr("Open")
   ```

5. **Update .pro file** - When adding new Python files or UI files with translatable strings, add them to `mapflow.pro`

## Maintenance Workflow

### Updating Existing Translations

When source code changes:

1. **Extract new strings:**
   ```bash
   cd i18n
   pylupdate5 mapflow.pro
   ```
   This updates `.ts` files with new/changed strings, marking missing translations as "unfinished"

2. **Translate new strings** using Qt Linguist or text editor

3. **Compile updated translations:**
   ```bash
   lrelease mapflow_ru.ts
   lrelease mapflow_fr.ts
   # ... for each language
   ```

4. **Test** - Restart QGIS and verify translations appear correctly

### Finding Untranslated Strings

Using Qt Linguist:
- Open the `.ts` file
- Filter by "Unfinished" translations
- Translate and mark as "Done"

## Language Codes

Common ISO 639-1 language codes:
- `ru` - Russian
- `fr` - French  
- `de` - German
- `es` - Spanish
- `pt` - Portuguese
- `it` - Italian
- `ja` - Japanese
- `zh` - Chinese
- `ar` - Arabic
- `hi` - Hindi

With locale variants:
- `en_US` - English (US)
- `en_GB` - English (UK)
- `pt_BR` - Portuguese (Brazil)
- `pt_PT` - Portuguese (Portugal)
- `zh_CN` - Chinese (Simplified)
- `zh_TW` - Chinese (Traditional)

## Tools Required

### Ubuntu/Debian:
```bash
sudo apt-get install pyqt5-dev-tools qttools5-dev-tools
```

### macOS (using Homebrew):
```bash
brew install pyqt5
brew install qt5
```

### Windows:
Install with pip:
```bash
pip install PyQt5
```

Qt Linguist is included in the Qt distribution.

## Translation Loading Logic

The plugin automatically detects and loads translations in `mapflow.py`:

```python
# Get QGIS locale (e.g., 'ru_RU' → 'ru')
locale = self.settings.value('locale/userLocale', 'en_US')[0:2]

# Build path to translation file
locale_path = os.path.join(self.plugin_dir, 'i18n', f'mapflow_{locale}.qm')

# Load if exists
if os.path.exists(locale_path):
    self.translator = QTranslator()
    self.translator.load(locale_path)
    QCoreApplication.installTranslator(self.translator)
```

No code changes needed to add new languages - just add the `.qm` file!

## Troubleshooting

### Translations not appearing
1. Verify `.qm` file exists in `i18n/` directory
2. Check QGIS locale: Settings → Options → General
3. Restart QGIS after changing locale
4. Check console for error messages

### New strings not extracted
1. Verify file is listed in `SOURCES` or `FORMS` in `mapflow.pro`
2. Verify `self.tr()` is used (not plain strings)
3. Run `pylupdate5 mapflow.pro` again

### Strings shown in wrong language
1. Check `.qm` file is compiled from latest `.ts`
2. Verify translation is marked as "finished" in Qt Linguist
3. Clear QGIS cache and restart

## Resources

- [Qt Linguist Manual](https://doc.qt.io/qt-5/qtlinguist-index.html)
- [PyQt5 i18n Tutorial](https://www.riverbankcomputing.com/static/Docs/PyQt5/i18n.html)
- [QGIS Plugin i18n Guide](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#translating-plugins)

## Contributing Translations

If you'd like to contribute a translation:
1. Follow steps 1-4 above to create your translation
2. Submit a pull request with:
   - Updated `mapflow.pro` (if needed)
   - Your `.ts` file (source translation)
   - Your `.qm` file (compiled translation)
3. Include information about your language proficiency and any localization considerations

Thank you for helping make Mapflow accessible to more users worldwide!
