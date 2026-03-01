# Design System Components

Standard UI components for audit reference.

---

## Buttons

### Primary Button
- **Token Reference**: `--color-primary`, `--radius-md`
- **States**: default, hover, active, disabled, loading
- **Sizes**: sm, md, lg

### Secondary Button
- **Token Reference**: `--color-border`, `--radius-md`
- **States**: default, hover, active, disabled, loading
- **Sizes**: sm, md, lg

### Icon Button
- **Token Reference**: `--radius-full` or `--radius-md`
- **States**: default, hover, active, disabled
- **Sizes**: sm, md, lg

---

## Form Elements

### Text Input
- **Token Reference**: `--radius-md`, `--color-border`
- **States**: default, focus, error, disabled
- **Parts**: label, input, helper text, error message

### Select
- **Token Reference**: `--radius-md`, `--color-border`
- **States**: default, open, focus, error, disabled

### Checkbox
- **States**: unchecked, checked, indeterminate, disabled

### Radio
- **States**: unchecked, checked, disabled

### Toggle/Switch
- **States**: off, on, disabled

---

## Feedback

### Alert/Banner
- **Variants**: info, success, warning, error
- **Parts**: icon, title, description, dismiss action

### Toast/Notification
- **Variants**: info, success, warning, error
- **Parts**: icon, message, action, dismiss

### Progress Indicator
- **Types**: linear, circular
- **States**: determinate, indeterminate

---

## Layout

### Card
- **Token Reference**: `--radius-lg`, `--shadow-md`
- **Parts**: header, body, footer

### Modal/Dialog
- **Token Reference**: `--radius-xl`, `--shadow-xl`
- **Parts**: header, body, footer, close action

### Drawer/Panel
- **Positions**: left, right, bottom
- **Parts**: header, body, footer

---

## Navigation

### Tabs
- **States**: default, active, disabled
- **Parts**: tab list, tab panel

### Breadcrumbs
- **Parts**: items, separator, current

### Pagination
- **Parts**: prev, next, page numbers, current

---

## Data Display

### Table
- **Parts**: header, rows, cells, pagination

### List
- **Variants**: plain, bordered, interactive

### Badge/Chip
- **Variants**: filled, outlined
- **Sizes**: sm, md

### Avatar
- **Sizes**: xs, sm, md, lg, xl
- **Variants**: image, initials, icon

---

## Typography Components

### Heading
- **Levels**: H1, H2, H3, H4, H5, H6
- **Token Reference**: `--text-*xl`, `--font-display`

### Body Text
- **Sizes**: sm, base, lg
- **Token Reference**: `--text-sm`, `--text-base`, `--text-lg`

### Link
- **States**: default, hover, visited, disabled

---

**Note**: This is a reference template. Component specifications should be defined based on the actual design system being audited.