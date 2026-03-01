# Design System Standards

Design principles and standards for UI/UX audit reference.

---

## Core Design Principles

### 1. Simplicity Is Architecture
- Every element must justify its existence
- If it doesn't serve the user's immediate goal, it's clutter
- The best interface is the one the user never notices
- Complexity is a design failure, not a feature

### 2. Consistency Is Non-Negotiable
- The same component must look and behave identically everywhere
- All values must reference design system tokens — no hardcoded values
- If you find inconsistency, flag it. Do not invent a third variation.

### 3. Hierarchy Drives Everything
- Every screen has one primary action. Make it unmissable.
- Secondary actions support, they never compete
- If everything is bold, nothing is bold
- Visual weight must match functional importance

### 4. Alignment Is Precision
- Every element sits on a grid. No exceptions.
- If something is off by 1-2 pixels, it's wrong
- Alignment is what separates premium from good-enough

### 5. Whitespace Is a Feature
- Space is not empty. It is structure.
- Crowded interfaces feel cheap. Breathing room feels premium.
- When in doubt, add more space, not more elements

---

## Accessibility Standards (WCAG 2.1 AA)

### Color Contrast
- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text**: Minimum 3:1 contrast ratio
- **UI components**: Minimum 3:1 contrast ratio against adjacent colors

### Touch Targets
- **Minimum size**: 44x44 pixels (iOS), 48x48 pixels (Android)
- **Spacing**: Adequate spacing between interactive elements

### Focus States
- All interactive elements must have visible focus indicators
- Focus order must follow logical reading sequence
- Focus must never be trapped

### ARIA and Semantics
- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`, etc.)
- Provide ARIA labels for interactive elements without visible text
- Ensure screen reader compatibility

---

## Responsive Design Standards

### Breakpoints
| Name | Min Width | Usage |
|------|-----------|-------|
| Mobile | 0px | Phone devices |
| Tablet | 768px | Tablet devices |
| Desktop | 1024px | Desktop screens |
| Wide | 1440px | Large monitors |

### Mobile-First Approach
- Design for mobile first, then enhance for larger screens
- Touch targets sized for thumbs
- Content prioritized for small screens

---

## Motion Standards

### Duration Guidelines
| Type | Duration | Usage |
|------|----------|-------|
| Fast | 100-150ms | Micro-interactions, hover states |
| Normal | 200-300ms | Standard transitions |
| Slow | 400-500ms | Complex animations, page transitions |

### Easing
- Prefer `ease-out` for entering elements
- Prefer `ease-in` for exiting elements
- Use `ease-in-out` for movements within the viewport

### Principles
- Motion should feel natural and purposeful
- Avoid motion that exists for decoration alone
- Respect `prefers-reduced-motion` user preference

---

## Empty, Loading, and Error States

### Empty States
- Guide users toward their first action
- Explain what will appear when data exists
- Feel intentional, not broken

### Loading States
- Use skeleton screens when possible
- Provide progress indication for long operations
- Maintain layout stability during loading

### Error States
- Be helpful and clear, not hostile
- Explain what went wrong and how to fix it
- Preserve user input where possible

---

## Quality Checklist

Before any design is considered complete:

- [ ] Visual hierarchy is clear (primary action is obvious)
- [ ] Spacing is consistent and intentional
- [ ] Typography establishes clear hierarchy
- [ ] Color is used with restraint and purpose
- [ ] All elements align to the grid
- [ ] Components are consistent across screens
- [ ] Icons are from a cohesive set
- [ ] Transitions feel natural
- [ ] Empty states are designed
- [ ] Loading states are consistent
- [ ] Error states are helpful
- [ ] Dark mode works (if supported)
- [ ] Nothing can be removed without losing meaning
- [ ] Works at mobile, tablet, and desktop
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader compatible

---

**Reference**: These standards align with the Jobs/Ive design philosophy in `SOUL.md`.