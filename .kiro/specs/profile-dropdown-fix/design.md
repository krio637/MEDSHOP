# Design Document: Profile Dropdown Fix

## Overview

This design addresses the incomplete profile dropdown implementation in the navbar. The current implementation has a profile button but lacks the dropdown menu structure and JavaScript functionality. The solution will implement a Bootstrap-based dropdown menu with custom styling that matches the application's gold theme and provides a Google-style user experience.

## Architecture

The profile dropdown will be implemented using:
1. **HTML Structure**: Bootstrap dropdown markup with proper ARIA attributes
2. **CSS Styling**: Custom styles that override Bootstrap defaults to match the gold theme
3. **JavaScript**: Event handlers for dropdown toggle, outside click detection, and keyboard navigation

### Component Hierarchy
```
Navbar
└── Profile Dropdown (li.nav-item.dropdown)
    ├── Profile Button (button#navbarDropdown)
    └── Dropdown Menu (div.dropdown-menu)
        ├── User Info Section
        │   ├── Avatar Icon
        │   ├── Username
        │   └── Email
        ├── Divider
        ├── Profile Link
        ├── Order History Link
        ├── Divider
        └── Logout Link
```

## Components and Interfaces

### 1. HTML Structure

The profile dropdown will replace the current incomplete implementation in `templates/base.html`:

**Current Implementation (Incomplete):**
```html
<li class="nav-item">
    <button class="nav-link btn btn-link px-2" id="profileButton">
        <i class="fas fa-user-circle fa-2x"></i>
    </button>
</li>
```

**New Implementation:**
```html
<li class="nav-item dropdown">
    <button class="nav-link dropdown-toggle" 
            id="navbarDropdown" 
            data-bs-toggle="dropdown" 
            aria-expanded="false">
        <i class="fas fa-user-circle fa-2x"></i>
    </button>
    <div class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
        <!-- User info section -->
        <div class="dropdown-header">
            <div class="user-avatar">
                <i class="fas fa-user-circle fa-3x text-primary"></i>
            </div>
            <div class="user-info">
                <strong>{{ user.username }}</strong>
                <small class="text-muted d-block">{{ user.email }}</small>
            </div>
        </div>
        <div class="dropdown-divider"></div>
        <!-- Navigation links -->
        <a class="dropdown-item" href="{% url 'profile' %}">
            <i class="fas fa-user me-2"></i>Profile
        </a>
        <a class="dropdown-item" href="{% url 'order_history' %}">
            <i class="fas fa-history me-2"></i>Order History
        </a>
        <div class="dropdown-divider"></div>
        <a class="dropdown-item text-danger" href="{% url 'logout' %}">
            <i class="fas fa-sign-out-alt me-2"></i>Logout
        </a>
    </div>
</li>
```

### 2. CSS Styling

Custom styles will be added to `static/css/dropdown-fix.css` to:
- Position the dropdown correctly
- Style the user info section
- Apply hover effects with the gold gradient
- Ensure mobile responsiveness

**Key Style Rules:**
- `.dropdown-menu`: Positioned absolutely, right-aligned, with shadow
- `.dropdown-header`: Custom styling for user info display
- `.dropdown-item:hover`: Gold gradient background
- `.user-avatar`: Centered avatar icon
- `.user-info`: Text alignment and spacing

### 3. JavaScript Functionality

Bootstrap 5's dropdown component will handle most functionality automatically through `data-bs-toggle="dropdown"`. Additional custom JavaScript will:
- Handle ESC key to close dropdown
- Ensure proper z-index stacking
- Handle mobile touch events

## Data Models

No new data models are required. The dropdown will use existing user data:
- `user.username`: Display name
- `user.email`: User email address
- `user.is_authenticated`: Conditional rendering

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

After analyzing the acceptance criteria, several properties can be consolidated to eliminate redundancy:

**Property 1: Dropdown toggle on click**
*For any* user session, clicking the profile icon should toggle the dropdown menu visibility (show if hidden, hide if shown)
**Validates: Requirements 1.1, 1.3**

**Property 2: Outside click closes dropdown**
*For any* element outside the dropdown menu, clicking that element when the dropdown is open should close the dropdown
**Validates: Requirements 1.2**

**Property 3: Escape key closes dropdown**
*For any* open dropdown, pressing the Escape key should close the dropdown menu
**Validates: Requirements 1.4**

**Property 4: User information display**
*For any* authenticated user, opening the dropdown should display the user's username, email, and avatar icon in the header section
**Validates: Requirements 2.1, 2.2, 2.3**

**Property 5: Navigation links presence**
*For any* open dropdown, the menu should contain links to Profile, Order History, and Logout with correct href attributes
**Validates: Requirements 3.1, 3.2, 3.3**

**Property 6: Link click closes dropdown**
*For any* link within the dropdown menu, clicking that link should close the dropdown
**Validates: Requirements 3.4**

**Property 7: Dropdown styling**
*For any* displayed dropdown, it should have a white background, box shadow, and be positioned aligned to the right edge of the profile button
**Validates: Requirements 4.1, 4.2**

**Property 8: Hover state styling**
*For any* menu item in the dropdown, hovering over it should apply a gradient background
**Validates: Requirements 4.3**

**Property 9: Visual separators**
*For any* displayed dropdown, divider elements should separate the user info section, navigation links, and logout link
**Validates: Requirements 4.4**

**Property 10: Mobile viewport compatibility**
*For any* mobile viewport (width < 768px), the dropdown should display within viewport bounds and respond to touch events for closing
**Validates: Requirements 5.1, 5.2, 5.3**

## Error Handling

### Dropdown Positioning Errors
- **Issue**: Dropdown may overflow viewport on small screens
- **Solution**: Use Bootstrap's `dropdown-menu-end` class and add CSS to ensure dropdown stays within viewport bounds
- **Fallback**: On very small screens, reduce dropdown width

### Missing User Data
- **Issue**: User email or username may be missing
- **Solution**: Use Django template filters with default values: `{{ user.email|default:"No email" }}`
- **Fallback**: Display generic placeholder text

### JavaScript Errors
- **Issue**: Bootstrap JavaScript may not load
- **Solution**: Include fallback vanilla JavaScript for basic toggle functionality
- **Fallback**: Dropdown remains visible as a static menu

### Z-Index Conflicts
- **Issue**: Other elements may overlap the dropdown
- **Solution**: Set explicit z-index of 9999 on dropdown-menu
- **Fallback**: Use !important declarations if necessary

## Testing Strategy

### Unit Testing
Unit tests will verify specific examples and edge cases:

1. **Dropdown HTML Structure Test**
   - Verify dropdown markup contains all required elements
   - Check ARIA attributes are present
   - Validate class names match Bootstrap conventions

2. **User Data Rendering Test**
   - Test with user having both username and email
   - Test with user missing email
   - Test with very long username/email (truncation)

3. **Link URL Test**
   - Verify each link has correct href attribute
   - Check icon classes are present
   - Validate link text content

### Property-Based Testing
Property-based tests will verify universal behaviors across all inputs:

**Testing Framework**: We will use Playwright for end-to-end property-based testing of the UI interactions, configured to run a minimum of 100 iterations per property.

**Property Test 1: Dropdown Toggle Consistency**
- Generate random sequences of click events on the profile button
- Verify that the dropdown visibility alternates correctly (open → close → open)
- **Validates: Property 1**

**Property Test 2: Outside Click Closure**
- Generate random coordinates outside the dropdown bounds
- Simulate clicks at those coordinates when dropdown is open
- Verify dropdown closes for all outside clicks
- **Validates: Property 2**

**Property Test 3: Keyboard Navigation**
- Generate random sequences of key presses including Escape
- Verify Escape always closes the dropdown when open
- Verify other keys don't unintentionally close the dropdown
- **Validates: Property 3**

**Property Test 4: User Info Display Completeness**
- Generate random user objects with various username/email combinations
- Render dropdown for each user
- Verify all user info elements are present in the DOM
- **Validates: Property 4**

**Property Test 5: Navigation Links Integrity**
- For any dropdown render, verify all required links exist
- Check each link has valid href and icon
- **Validates: Property 5**

**Property Test 6: Responsive Behavior**
- Generate random viewport widths from 320px to 1920px
- Open dropdown at each width
- Verify dropdown stays within viewport bounds
- **Validates: Property 10**

### Integration Testing
- Test dropdown interaction with navbar collapse on mobile
- Test dropdown with different user roles (staff vs regular user)
- Test dropdown behavior during page navigation

### Manual Testing Checklist
- Visual inspection of dropdown styling
- Test on multiple browsers (Chrome, Firefox, Safari, Edge)
- Test on multiple devices (desktop, tablet, mobile)
- Verify accessibility with screen readers
- Test keyboard navigation (Tab, Shift+Tab, Escape)

## Implementation Notes

### Bootstrap Integration
- Use Bootstrap 5.1.3 dropdown component (already included in project)
- Leverage `data-bs-toggle="dropdown"` for automatic functionality
- Override Bootstrap styles with custom CSS

### Accessibility Considerations
- Include proper ARIA attributes (`aria-expanded`, `aria-labelledby`)
- Ensure keyboard navigation works (Tab, Escape)
- Maintain focus management when dropdown opens/closes
- Use semantic HTML elements

### Performance Considerations
- Minimize JavaScript execution on dropdown toggle
- Use CSS transitions for smooth animations
- Avoid layout thrashing by batching DOM reads/writes

### Browser Compatibility
- Target modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Use CSS features with good support (flexbox, CSS variables)
- Provide fallbacks for older browsers if needed

### Mobile Considerations
- Use touch-friendly target sizes (minimum 44x44px)
- Ensure dropdown doesn't require horizontal scrolling
- Test on various mobile devices and orientations
- Consider using a modal on very small screens (< 375px width)

## Dependencies

- Bootstrap 5.1.3 (already included)
- Font Awesome 6.0.0 (already included)
- Django template system (already in use)
- No additional dependencies required

## Migration Path

1. Update `templates/base.html` with new dropdown markup
2. Update `static/css/dropdown-fix.css` with new styles
3. Remove incomplete profile modal code from base.html
4. Test dropdown functionality across all pages
5. Deploy changes to staging environment
6. Perform user acceptance testing
7. Deploy to production

## Future Enhancements

- Add user avatar image support (currently using icon)
- Add notification badge to profile icon
- Add quick settings toggle in dropdown
- Add theme switcher in dropdown
- Add language selector in dropdown
