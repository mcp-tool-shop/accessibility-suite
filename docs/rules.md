# Accessibility Rule Guidelines

This document provides explanations and remediation steps for common accessibility findings reported by the `a11y-ci` suite.

## Index

- [Image Missing Alt Text](#a11yimgalt)
- [Form Missing Label](#a11yformlabel)
- [Button Missing Name](#a11ybtnname)
- [Link Missing Name](#a11ylinkname)
- [Color Contrast](#a11ycolorcontrast)
- [Document Title](#a11ydoctitle)

---

### <a id="a11yimgalt"></a>Image Missing Alt Text (A11Y.IMG.ALT)

**Why it matters:**  
Screen reader users rely on alternative text to understand the content and function of images. Without it, they might hear "image" or a filename, missing context.

**How to fix:**
- **Informative Images:** Add `alt="Description of image"` covering the visual meaning.
- **Decorative Images:** Add `alt=""` (empty string) so assistive technology ignores it.
- **Complex Images:** Use `aria-describedby` or a caption if a short alt text isn't enough.

---

### <a id="a11yformlabel"></a>Form Missing Label (A11Y.FORM.LABEL)

**Why it matters:**  
Users need to know what data is expected in a form field. Visual labels help everyone; programmatic labels allow screen readers to announce the field's purpose when focused.

**How to fix:**
- **Best:** Use a visible `<label for="input-id">Label Text</label>`.
- **Alternative:** Use `aria-label="Label Text"` if no visual label is possible (e.g. search icon).
- **Alternative:** Use `aria-labelledby="id-of-visible-text"`.

---

### <a id="a11ybtnname"></a>Button Missing Name (A11Y.BTN.NAME)

**Why it matters:**  
Buttons without names are often announced as just "Button" to screen reader users, providing no clue about what action will occur.

**How to fix:**
- **Text Content:** Ensure the button has text content inside the `<button>` tag.
- **Icon Buttons:** If using an icon, add `aria-label="Action Name"` or visually hidden text.

---

### <a id="a11ylinkname"></a>Link Missing Name (A11Y.LINK.NAME)

**Why it matters:**  
Links must have discernable text so users can understand the destination. "Click here" or empty links are major barriers.

**How to fix:**
- Ensure the anchor tag `<a>` contains text.
- If using an icon-only link, use `aria-label` to describe the destination.

---

### <a id="a11ycolorcontrast"></a>Low Color Contrast (A11Y.COLOR.CONTRAST)

**Why it matters:**  
Low contrast text is difficult or impossible for users with low vision or color blindness to read.

**How to fix:**
- Ensure a contrast ratio of at least **4.5:1** for normal text.
- Ensure a contrast ratio of at least **3.0:1** for large text (18pt+ or 14pt+ bold).

---

### <a id="a11ydoctitle"></a>Missing Document Title (A11Y.DOC.TITLE)

**Why it matters:**  
The page title is the first thing a screen reader user hears. It allows users to orient themselves and distinguish between open tabs.

**How to fix:**
- Ensure the `<title>` element exists in the `<head>`.
- Provide a unique, descriptive title for every page (e.g., "Checkout - Store Name").

---

### <a id="clicoloronly"></a>Color-Only Information (CLI.COLOR.ONLY)

**Why it matters:**  
conveying information only via color (like red for error) excludes users who are colorblind or using text-only interfaces.

**How to fix:**
- Add text prefixes (e.g., `Error:`, `Warning:`).
- Use icons or symbols alongside color.
