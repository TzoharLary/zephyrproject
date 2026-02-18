# TS (Test Suite) - מדריך חילוץ מידע גנרי

**מסמך זה מתאר את המבנה הכללי של קבצי Test Suite (TS.pdf) של Bluetooth SIG, וכל סוגי המידע שאפשר לחלץ מהם בצורה אוטומטית וגנרית.**

---

## 1. סקירה כללית

כל TS PDF מכיל תיעוד מלא על סט הבדיקות (test cases) שנדרש לבדוק profile מסוים של Bluetooth. המסמכים מסודרים בצורה סטנדרטית על ידי Bluetooth SIG, מה שמאפשר חילוץ מובנה של המידע.

### גודל וקנה מידה
- **עמודים**: 13-100+ עמודים (בהתאם לסיבוכיות הפרופיל)
- **טקסט**: 600-7000+ שורות טקסט בעת המרה ל-PDF text
- **אורך**: מ-5KB ל-50KB בפורמט טקסט

---

## 2. מטא-נתונים בעמוד הכיסוי (Cover Page / Header)

### מיקום
עמודים 1-3 של ה-PDF

### מידע שאפשר להוציא

#### 2.1 Revision Metadata
```
Pattern: "Revision: <specification>"
Example: "Revision: DIS.TS.p6"
         "Revision: BAS.TS.p7"
         "Revision: HOGP.TS.p12"

Extraction: חפש ב-regex: Revision:\s*([A-Z]+\.TS\.p\d+)
Output: String - מזהה גרסה רשמי
```

#### 2.2 Revision Date
```
Pattern: "Revision Date: <YYYY-MM-DD>"
Example: "Revision Date: 2023-06-23"
         "Revision Date: 2025-02-18"

Extraction: חפש ב-regex: Revision\s+Date:\s*(\d{4}-\d{2}-\d{2})
Output: Date string ISO 8601
```

#### 2.3 Prepared By
```
Pattern: "Prepared By: <organization>"
Example: "Prepared By: BTI"
         "Prepared By: Medical Devices Working Group"

Extraction: חפש ב-regex: Prepared\s+By:\s*(.+?)$
Output: String - שם ארגון
```

#### 2.4 Published During TCRL
```
Pattern: "Published during TCRL: <TCRL version>"
Example: "Published during TCRL: TCRL.2022-2-addition"
         "Published during TCRL: TCRL.2025-1"
         "Published during TCRL: TCRL.pkg100-addition"

Extraction: חפש ב-regex: Published\s+during\s+TCRL:\s*(.+?)$
Output: String - גרסת TCRL
```

---

## 3. מבנה תוכן (Table of Contents)

### מיקום
עמודים 2-4 בדרך כלל

### מידע שאפשר להוציא

#### 3.1 סעיפים ראשיים
```
Sections להוציא:
- Scope
- References, definitions, abbreviations
- Test Suite Structure (TSS)
- Test cases (TC)
- Test case mapping
- Revision history

Extraction: חפש "^[0-9]\s+" ו-"^[0-9]\.[0-9]\s+"
Output: List של subsections עם page numbers
Format: {section_number, section_title, page_number}
```

---

## 4. Test Suite Structure (TSS) - Section 3

### מיקום
דוד כ-עמודים 6-8 מתחילת המסמך

### מידע שאפשר להוציא

#### 4.1 Overview Diagram / Architecture
```
Content Type: וויזואל/טקסט המתאר את הארכיטקטורה
Contains:
- Layers (GAP, GATT, L2CAP, LE Controller, etc.)
- Required protocols
- Service relationships

Extraction:
1. חפש blocks של שמות פרוטוקולים (GAP, GATT, ATT, SM, etc.)
2. קבץ אותם כרשימה של protocol dependencies
3. צור DAG (Directed Acyclic Graph) של קשרים

Output Format:
{
  "layers": ["GAP", "GATT", "ATT", "L2CAP", "LE Controller"],
  "dependencies": {
    "GAP": ["L2CAP"],
    "GATT": ["ATT", "GAP"],
    "ATT": ["L2CAP"]
  }
}
```

#### 4.2 Test Strategy
```
Content Type: טקסט תיאורי
Contains:
- Test objectives
- Approach (mandatory, optional, conditional)
- ICS/IXIT reference
- Test applicability rules
- IUT (Implementation Under Test) role definitions
- Tester roles (Lower Tester, Upper Tester)

Extraction:
1. חפש פסקות המתחילות ב-"Test objectives", "The test approach", "Any defined test"
2. חלץ משפטים המכילים:
   - "mandatory"
   - "optional"
   - "conditional"
   - "ICS" (Implementation Conformance Statement)
   - "IXIT" (Implementation Extra Information for Test)
3. הוציא הגדרות תפקידים (roles)

Pattern Examples:
- "The testing approach covers mandatory and optional requirements"
- "Any defined test herein is applicable to the IUT if the ICS logical expression defined in the Test Case Mapping Table (TCMT) evaluates to true"
- "Lower Tester acts as the IUT's peer device"

Output Format:
{
  "test_objectives": "String - תיאור מטרות הבדיקה",
  "approach": "String - הגישה כללית",
  "mandatory_optional_conditional": Boolean,
  "ics_reference": Boolean,
  "ixit_reference": Boolean,
  "roles": ["IUT", "Lower Tester", "Upper Tester"],
  "key_phrases": [list of important statements]
}
```

#### 4.3 Test Groups
```
Content Type: רשימה מובנית
Contains:
- Named categories of tests
- Logical groupings (e.g., "Read", "Write", "Notify", "Indicate", "Broadcast")

Location: Section 3.3 "Test groups"
Pattern:
- "The following test groups have been defined:"
- "•" OR "-" bullet points
- Capitalized group names

Extraction:
1. חפש "^3\.3\s+" OR "^Test groups" 
2. חלץ כל בולט בין הכותרת הזו לבין הסעיף הבא
3. נקה whitespace וקמת נוספות

Example Pattern:
```
The following test groups have been defined:
• Generic GATT Integrated Tests
• Characteristic Read
• Characteristic Write
• Configure Notification
• Characteristic Notification
```

Output Format:
{
  "test_groups": [
    "Generic GATT Integrated Tests",
    "Characteristic Read",
    "Characteristic Write",
    "Configure Notification",
    "Characteristic Notification"
  ],
  "count": 5
}
```

---

## 5. Test Cases (TC) - Section 4

### מיקום
דוד זה הוא הציבור הגדול ביותר של ה-TS, דוד כ-עמודים 8-90+

### מידע שאפשר להוציא

#### 5.1 Test Case Identification Convention
```
Content Type: הגדרת קונוונציה של TCID format
Location: "4.1.1 Test case identification conventions"

Pattern Structure:
<spec_abbreviation>/<IUT_role>/<class>/<feat>/<func>/<subfunc>/<cap>/<xx>-<nn>-<y>

Examples:
- DIS/SR/SGGIT/SER/BV-01-C
- BAS/SR/IND/BV-31-C
- HRS/SEN/CN/BV-05-C
- HOGP/RH/HGWF/BV-07-I

Extraction:
1. חפש "Test case identification convention" OR "Test cases are assigned unique identifiers"
2. חלץ את FORMAT המתואר (עם <> סימנים)
3. הוציא את הסימבולים ומשמעויותיהם

Output Format:
{
  "tcid_format": "<spec_abbreviation>/<IUT_role>/<class>/<feat>/<func>/<subfunc>/<cap>/<xx>-<nn>-<y>",
  "components": {
    "spec_abbreviation": "Profile name (DIS, BAS, HRS, HOGP)",
    "IUT_role": "Server/Client/Reporter/etc",
    "class": "Class category",
    "feat": "Feature type",
    "func": "Function",
    "subfunc": "Sub-function",
    "cap": "Capability",
    "xx_nn_y": "Test case number and variant"
  },
  "special_convention": "Optional - GGIT (Generic GATT Integrated Tests) format if mentioned"
}
```

#### 5.2 Test Case Details
```
Content Type: טקסט מובנה עבור כל בדיקה

Contains (per test case):
- TCID (Test Case ID)
- Title/Description
- Features tested
- Roles (Server, Client, etc.)
- Category
- Active Date
- Procedure steps
- Initial conditions (precon/preconditions)
- Test execution steps
- Pass verdict criteria
- Fail verdict criteria
- Comments/Notes

Extraction Strategy:
1. חפש Regex: ^([A-Z]+/[A-Z]+/.*/BV-\d+-.)
   זה יתן TCID header
   
2. חלץ הכל ממש אחרי TCID עד ל-TCID הבא:
   - Title (שורה ממש אחרי TCID)
   - פסקאות של Procedure
   - Initial Conditions
   - Pass/Fail verdicts
   
3. חלץ מטא-ערכים:
   - Category (בדרך כלל בתוך הטקסט או בחלק "Test Purpose")
   - Roles (חפש "Tester", "Role")
   - Features (מהתיאור)

Output Format Per Test Case:
{
  "tcid": "BAS/SR/IND/BV-31-C",
  "title": "Characteristic Indication – Battery Energy Status, Multiple Instances...",
  "category": "Indication",
  "roles": ["Server"],
  "test_type": "BV" (or "BI" for Invalid Behavior),
  "features": ["Indication", "Battery Energy Status"],
  "procedures": {
    "initial_conditions": [list of preconditions],
    "test_steps": [ordered list of steps],
    "pass_verdict": "Description of pass condition",
    "fail_verdict": "Description of fail condition"
  },
  "comments": "Any additional notes"
}
```

#### 5.3 Test Case Category Distribution
```
Extraction: חלץ ספירה של בדיקות לפי category

Pattern:
- "BV" = Valid Behavior tests (חיובית הרצה)
- "BI" = Invalid Behavior tests (שליליים/שגיאה)

Count Examples:
- DIS: 9 BV tests
- BAS: 30+ BV tests, 15+ BI tests
- HRS: 9 BV tests, 2 BI tests
- HOGP: 50+ BV tests, 20+ BI tests

Output Format:
{
  "test_case_counts": {
    "total_test_cases": 45,
    "bv_count": 35,
    "bi_count": 10,
    "categories": {
      "Indication": 15,
      "Write": 10,
      "Read": 8,
      "Notification": 7,
      "Broadcast": 5
    }
  }
}
```

---

## 6. Test Case Mapping Table (TCMT) - Section 5

### **זה המדור המצפה הביותר.**

### מיקום
סעיף 5, בדרך כלל עמודים 85-95 (כ-90% דרך המסמך)

### מידע שאפשר להוציא

#### 6.1 TCMT Header/Introduction
```
Content Type: הסבר מה ה-TCMT עושה
Pattern Text:
"The Test Case Mapping Table (TCMT) maps test cases to specific requirements in the ICS."
"The IUT is tested in all roles for which support is declared in the ICS document."

Contains:
- מטרת ה-TCMT
- הגדרת הstruct של הטבלה
- הסבר של כל עמודה

Column Definitions להוציא:
1. "Item" - ICS requirements (logical expressions)
2. "Feature" - תיאור בן-אדם של הפיצ'ר
3. "Test Case(s)" - TCID(s) הרלוונטיים

Extraction:
1. חפש "^The columns for the TCMT are defined as follows:"
2. חלץ כל colum definition עד שתיתקל ב-"Table [number]:"
3. נקה וסדר את ההגדרות

Output Format:
{
  "tcmt_purpose": "String describing TCMT purpose",
  "tcmt_columns": {
    "Item": "Contains a logical expression based on specific entries from the associated ICS document",
    "Feature": "A brief, informal description of the feature being tested",
    "Test Case(s)": "The applicable test case identifiers..."
  },
  "item_reference_format": "y/x format - y=table number, x=feature number",
  "logic_operators_supported": ["AND", "OR", "NOT"]
}
```

#### 6.2 TCMT Table Rows (The actual mapping)
```
Content Type: טבלה מובנית

Row Structure:
┌──────────────────────────┬─────────────────────┬──────────────────────┐
│ Item (ICS Requirement)   │ Feature             │ Test Case(s)         │
├──────────────────────────┼─────────────────────┼──────────────────────┤
│ DIS 2/1 AND DIS 5/1      │ Service as primary  │ DIS/SR/SGGIT/SER/... │
│ DIS 2/2                  │ Manufacturer Name   │ DIS/SR/SGGIT/CHA/... │
│ BAS 2/1 OR BAS 2/6       │ Battery Level       │ BAS/SR/CR/BV-01-C    │
│ BAS 2/3 AND NOT BAS 2a/1 │ Complex condition   │ BAS/SR/NTF/BV-05-C   │
└──────────────────────────┴─────────────────────┴──────────────────────┘

Extraction Strategy:

1. **Find Table Start**: חפש ב-regex:
   "^(Table\s+\d+\.\d+:\s*Test\s+case\s+mapping)" או "^\s*Item\s+Feature.*Test\s+Case"

2. **Extract Rows**: חלץ טבלה עד "^[0-9]" (סעיף חדש) או "^Bluetooth SIG Proprietary"

3. **Parse Each Row**:
   - Item: טקסט לפני 2-3 spaces/tabs - יכול להיות multi-line עם AND/OR/NOT
   - Feature: טקסט בעמודה השנייה
   - Test Case(s): TCID או יותר מ-TCID מפוצלים על ידי comma

4. **Normalize**:
   - Clean whitespace
   - Parse logic expressions:
     - "DIS 2/1 AND DIS 5/1" → {operator: "AND", operands: ["DIS 2/1", "DIS 5/1"]}
     - "BAS 2/3 AND NOT BAS 2a/1" → complex expression tree
   - Parse TCID lists:
     - "BAS/SR/CR/BV-01-C" → single TCID
     - "BAS/SR/CR/BV-01-C, BAS/SR/NTF/BV-05-C" → multiple TCIDs

Output Format Per Row:
{
  "ics_requirement": {
    "raw": "DIS 2/1 AND DIS 5/1",
    "parsed_expression": {
      "operator": "AND",
      "operands": [
        {"type": "ics_item", "table": 2, "item": 1},
        {"type": "ics_item", "table": 5, "item": 1}
      ]
    },
    "references": [
      {"table": 2, "item": 1},
      {"table": 5, "item": 1}
    ]
  },
  "feature_description": "Device Information Service as a primary service",
  "test_cases": [
    {
      "tcid": "DIS/SR/SGGIT/SER/BV-01-C",
      "category": "BV",
      "role": "SR" (or similar)
    }
  ]
}

Aggregated TCMT Format:
{
  "tcmt_rows": [
    {...},
    {...},
    ...
  ],
  "total_rows": 42,
  "ics_items_referenced": [
    {"table": 2, "item": 1},
    {"table": 2, "item": 2},
    ...
  ],
  "tcids_mapped": [
    "DIS/SR/SGGIT/SER/BV-01-C",
    "DIS/SR/SGGIT/CHA/BV-01-C",
    ...
  ],
  "unmapped_tcids": [
    "TCID_X",
    "TCID_Y"
  ] /* TCIDs שמוגדרים בסעיף 4 אבל לא בTCMT */
}
```

---

## 7. Revision History and Acknowledgments - Last Section

### מיקום
סעיף 6, עמודים האחרונים של ה-TS

### מידע שאפשר להוציא

#### 7.1 Revision History
```
Content Type: טבלה היסטורית

Structure:
┌─────────────┬──────────────┬────────────┬──────────────────────────┐
│ Edition     │ Revision     │ Date       │ Comments                 │
├─────────────┼──────────────┼────────────┼──────────────────────────┤
│ 0           │ 1.0.0        │ 2011-05-24 │ Prepare for publication  │
│ 1.1.0r1     │ (version)    │ 2011-10-13 │ Changes to include...    │
└─────────────┴──────────────┴────────────┴──────────────────────────┘

Extraction:
1. חפש "^6.*Revision[Hh]istory" או "^Revision History"
2. חלץ טבלה עד סוף המסמך
3. Parse rows: extract publication, revision, date, changes

Output Format:
{
  "revision_history": [
    {
      "edition": "0",
      "revision": "1.0.0",
      "date": "2011-05-24",
      "comments": "Prepare for publication"
    },
    {
      "edition": "1",
      "revision": "1.1.0r1",
      "date": "2011-10-13",
      "comments": "Changes to include HID PnP ID characteristic per GPA discussion"
    }
  ],
  "latest_revision": "DIS.TS.p6",
  "latest_date": "2023-06-23"
}
```

#### 7.2 Major Changes Summary
```
Auto-extract key changes:
- חלץ משפטים המכילים מילים כמו:
  - "Updated"
  - "Added"
  - "Removed"
  - "Fixed"
  - "Changed"
  - "Converted" (test cases)
  - "TSE" (Test Suite Erratum)
  
Output:
{
  "recent_changes": [
    "TSE XXXX: Updated TP/SD/BV-01-C to only be for LE Transport",
    "Converted test cases to GGIT",
    "Added references to..."
  ]
}
```

---

## 8. Additional Extractable Metadata

### 8.1 References Section
```
Location: סעיף 2.1
Contains:
[1] Bluetooth Core Specification
[2] Test Strategy and Terminology Overview
[3] ICS Proforma for [Profile]
[4] HIDS Test Suite (if HOGP)
[5] GATT Test Suite
etc.

Extraction:
1. חפש "^2\.1\s+References" או "^References"
2. חלץ כל [N] reference וה-description
3. זהה סוגי references:
   - Core specifications
   - Test suites
   - ICS definitions
   - Related profiles

Output Format:
{
  "references": [
    {
      "id": 1,
      "title": "Bluetooth Core Specification",
      "version": "Version 4.2 or later",
      "type": "core_specification"
    },
    {
      "id": 2,
      "title": "Test Strategy and Terminology Overview",
      "type": "methodology"
    }
  ]
}
```

### 8.2 Acronyms and Abbreviations
```
Location: סעיף 2.3
Contains:
BV - Valid Behavior
BI - Invalid Behavior
SR - Server Role
CR - Client Role
RH - Report Host
HD - Report Device
etc.

Extraction:
1. חפש "^2\.3\s+Acronyms" או "^Abbreviations"
2. חלץ כל Acronym = Definition
3. Filter את ה-common Bluetooth abbreviations

Output Format:
{
  "acronyms": {
    "BV": "Valid Behavior",
    "BI": "Invalid Behavior",
    "SR": "Server Role",
    "CR": "Client Role",
    "IUT": "Implementation Under Test",
    "GAP": "Generic Access Profile",
    "GATT": "Generic Attribute Profile",
    "SM": "Security Manager",
    "L2CAP": "Logical Link Control and Adaptation Protocol"
  }
}
```

### 8.3 Definitions Section
```
Location: סעיף 2.2
Contains:
List of specialized terms defined in the context of this TS

Extraction similar to Acronyms

Output Format:
{
  "definitions": {
    "ICS": "Implementation Conformance Statement - document declaring ...",
    "IXIT": "Implementation Extra Information for Test - additional ...",
    ...
  }
}
```

---

## 9. Data Quality & Validation Rules

### 9.1 Consistency Checks
```
After extraction, validate:

1. **TCID Consistency**:
   - All TCIDs mentioned in TCMT must exist in Section 4 (Test Cases)
   - Flag unmapped TCIDs (in Section 4 but not in TCMT)
   - Flag missing TCIDs (in TCMT but not in Section 4)

2. **ICS Reference Consistency**:
   - All ICS references in TCMT (e.g., "DIS 2/1") should be valid
   - Format: TABLE_NUMBER/ITEM_NUMBER
   - Flag malformed references

3. **TCID Format**:
   - All TCIDs match the format defined in Section 4.1.1
   - Validate spec_abbreviation matches profile
   - Validate role codes are valid

4. **Test Group Coverage**:
   - Every test case should belong to a declared test group
   - Flag orphaned test cases

Output:
{
  "validation_report": {
    "valid": true/false,
    "unmapped_tcids": [...],
    "missing_tcids": [...],
    "malformed_references": [...],
    "orphaned_test_cases": [...],
    "warnings": [...]
  }
}
```

### 9.2 Extraction Statistics
```
Generate summary:
{
  "extraction_stats": {
    "total_test_cases": 45,
    "total_tcmt_rows": 42,
    "test_groups": 5,
    "bv_vs_bi_ratio": "35:10",
    "ics_items_referenced": 42,
    "unique_tcids": 45,
    "unmapped_ratio": 0.067,  /* 3 TCIDs not mapped */
    "feature_coverage": 42,   /* 42 features have test cases */
    "logic_complexity": {
      "simple_1to1_mappings": 35,
      "complex_expressions": 7
    }
  }
}
```

---

## 10. Processing Pipeline (High Level)

```
TS PDF Input
    ↓
[1] Extract Metadata (עמודים 1-3)
    ├─ Revision, Date, TCRL version
    └─ Output: metadata.json
    ↓
[2] Extract Test Suite Structure (סעיף 3)
    ├─ Architecture diagram
    ├─ Test strategy
    ├─ Test groups
    └─ Output: tss.json
    ↓
[3] Extract Test Cases (סעיף 4)
    ├─ TCID format convention
    ├─ Individual test case details
    ├─ Test case categorization
    └─ Output: test_cases.json
    ↓
[4] Extract TCMT (סעיף 5) ← **MAIN VALUE**
    ├─ Parse TCMT rows
    ├─ Parse ICS requirements
    ├─ Parse TCID mappings
    ├─ Validate consistency
    └─ Output: tcmt.json
    ↓
[5] Extract History (סעיף 6)
    ├─ Revision history
    ├─ Changes summary
    └─ Output: history.json
    ↓
[6] Extract References (סעיף 2)
    ├─ References
    ├─ Definitions
    ├─ Acronyms
    └─ Output: metadata_complete.json
    ↓
[7] Validate & Consolidate
    ├─ Cross-reference validation
    ├─ Generate statistics
    ├─ Flag issues
    └─ Output: validation_report.json + consolidated.json
    ↓
Complete Structured Data
```

---

## 11. Output Formats (JSON Schema)

### 11.1 Complete TS Extraction Schema

```json
{
  "profile": "DIS|BAS|HRS|HOGP",
  "metadata": {
    "revision": "string",
    "revision_date": "YYYY-MM-DD",
    "prepared_by": "string",
    "published_tcrl": "string",
    "page_count": "number"
  },
  "test_suite_structure": {
    "architecture_layers": ["string"],
    "dependencies": "object",
    "test_strategy": "string",
    "test_groups": ["string"],
    "group_count": "number"
  },
  "test_cases": {
    "total_count": "number",
    "bv_count": "number",
    "bi_count": "number",
    "tcid_format": "string",
    "cases": [
      {
        "tcid": "string",
        "title": "string",
        "category": "string",
        "roles": ["string"],
        "procedures": "object"
      }
    ]
  },
  "test_case_mapping": {
    "total_rows": "number",
    "rows": [
      {
        "ics_requirement": "object",
        "feature_description": "string",
        "test_cases": ["string"]
      }
    ],
    "unmapped_tcids": ["string"],
    "ics_items_referenced": ["object"]
  },
  "references": {
    "core_specs": ["string"],
    "test_suites": ["string"],
    "profiles": ["string"]
  },
  "definitions": "object",
  "acronyms": "object",
  "revision_history": [
    {
      "edition": "string",
      "revision": "string",
      "date": "YYYY-MM-DD",
      "comments": "string"
    }
  ],
  "validation": {
    "valid": "boolean",
    "issues": ["string"],
    "statistics": "object"
  }
}
```

---

## 12. Special Considerations

### 12.1 Multi-line Fields
```
Some fields (especially in TCMT) span multiple lines:
- Item: "BAS 2/3 AND\nBAS 2a/1" (split across lines)
- Feature: Long descriptions wrapping
- Test Case(s): Multiple TCIDs on separate lines

Handling:
- Use \n or space as delimiter?
- Preserve original formatting or normalize?
- Recommendation: Normalize to single line, preserve original in "raw" field
```

### 12.2 Table Detection Challenges
```
TCMT and other tables may have:
- Variable spacing/alignment
- Missing borders in OCR'd PDFs
- Inconsistent row heights
- Merged cells (logical)

Strategy:
- Use row-based extraction (look for TCID patterns)
- Use column-based extraction (look for position-based alignment)
- Fallback to regex patterns if needed
- Manual validation on small sample
```

### 12.3 Special Characters & Encoding
```
Potential issues:
- Bluetooth® (registered trademark symbol)
- Bullet points: •, -, *
- Dashes: –, —, -
- Quotation marks: ", ", ', '

Handling:
- Normalize special chars to ASCII equivalents
- Preserve in "raw" field if needed for display
- Use UTF-8 encoding throughout
```

### 12.4 Historic Changes (TSE - Test Suite Erratum)
```
TS often contains entries like:
"TSE 4427: Test Procedure update for 4.5 Characteristic Read test cases"
"TSE 5586: Updated TP/SD/BV-01-C to only be for LE Transport"

These indicate:
- Official errata/updates
- Important changes to specific test cases
- Traceability to SIG decision tracking

Extraction:
- Identify TSE number pattern: "TSE \d+"
- Link to affected TCID if mentioned
- Mark test case as "errata_updated"

Output:
{
  "errata": [
    {
      "tse_number": 4427,
      "affected_tcid": "optional",
      "description": "string",
      "type": "update|clarification|fix"
    }
  ]
}
```

---

## 13. Integration with Current System

### 13.1 Mapping to Existing Report Structure

Current report has:
- `tcs` (test cases from TCRL Excel)
- `mapping` (TSPC-to-TCID mapping via scoring)
- `meta` (metadata)

TS extraction provides:
- Authoritative TCMT (ICS-to-TCID mapping)
- Test case descriptions and procedures
- Test groups and categorization
- Validation data

Integration points:
1. **TCMT as confidence boost**: Use extracted TCMT to validate/update scoring confidence
2. **Test case enrichment**: Add description/procedures to existing TCIDs
3. **Categorization**: Use extracted test groups to categorize TCIDs
4. **Validation**: Cross-check current mapping against TCMT

### 13.2 Update Build Script

Current: `tools/build_pts_report_bundle.py`
Lines affected:
```
Lines 797-820: build_official_sources()
  - Add TS PDF processing
  - Store extracted TCMT

Lines 1500-1600: build_tspc_tcid_mapping()
  - Use TCMT as primary source
  - Use scoring as fallback

Lines 1900-2000: data structure construction
  - Add TS-extracted fields to JSON output
```

---

## 14. Error Handling & Edge Cases

### 14.1 Corrupted/Malformed PDFs
```
Possible issues:
- Missing pages
- OCR errors
- Non-text PDFs (scanned images)
- Incomplete sections

Handling:
1. Check page count vs expected ranges
2. Validate presence of key sections
3. Fallback to partial extraction
4. Log warnings/errors

Output:
{
  "extraction_status": "success|partial|failure",
  "completeness": 0.95,  /* 95% of expected data */
  "warnings": [...],
  "errors": [...]
}
```

### 14.2 Version Variations
```
Different TS versions may have:
- Different section numbering
- Reorganized chapters
- Changed terminology
- New test cases

Strategy:
- Use content-based detection, not page number-based
- Look for key phrases, not fixed positions
- Support multiple format variations
- Version detection: use "Revision" field
```

### 14.3 Profile-Specific Variations
```
Example: HOGP has more complex structure than DIS
- DIS: 13 pages, 9 test cases
- HID: 100 pages, 60+ test cases

Strategy:
- Parameterize expected ranges
- Profile-specific parsing rules (light)
- Generic fallback rules
- Handle profile variants (e.g., HOGP vs HID11)
```

---

## 15. Testing & Validation Checklist

```
Before passing to LLM:

[ ] Extract metadata from sample PDF
  [ ] Revision date format correct
  [ ] TCRL version parsed
  
[ ] Extract TCMT from sample
  [ ] All rows extracted
  [ ] ICS requirements parsed correctly
  [ ] TCID lists complete
  
[ ] Validate consistency
  [ ] All TCIDs exist in Section 4
  [ ] No malformed references
  [ ] ICS item format correct
  
[ ] Compare across profiles
  [ ] Different test group counts handled
  [ ] Variable TCMT sizes processed correctly
  [ ] Format variations detected
  
[ ] Output completeness
  [ ] All fields populated
  [ ] Validation stats generated
  [ ] Error reporting working
  
[ ] Performance
  [ ] PDF parsing time < 5 seconds
  [ ] JSON output < 1MB for typical TS
  [ ] Memory usage reasonable
```

---

## Summary

**זה המסמך משרת כ-specification למערכת חילוץ מידע מ-TS PDFs.**

Key points:
1. ✅ TS מכיל TCMT - המיפוי המפורש בין דרישות ICS ו-TCIDs
2. ✅ TS מכיל Test Strategy, Groups, Cases בפורמט מובנה
3. ✅ Extraction גנרי עובד על כל הפרופילים (DIS, BAS, HRS, HOGP)
4. ✅ Output JSON מובנה ניתן ישר להשתמוש בו في הדוח
5. ✅ Validation כנגד TCRL Excel עבור consistency

**Next Step**: להעביר מסמך זה ל-LLM שיכתוב את קוד החילוץ בPython.
