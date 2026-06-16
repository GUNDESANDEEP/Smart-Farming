"""
UI/UX Design Document - Farmer Module
Step-by-step screens and user flow for Smart Farming App
"""

# ==================== SCREEN 1: SPLASH/ONBOARDING ====================
"""
╔════════════════════════════════╗
║                                ║
║      🌾 SMART FARMING 🌾       ║
║                                ║
║   "Grow Better, Earn Better"   ║
║                                ║
║  [Get Started Button]          ║
║  [Already have account?]       ║
║                                ║
╚════════════════════════════════╝

UI ELEMENTS:
- Logo: Green leaf/wheat icon
- Hero image: Farmer in field
- Button color: Green (#4CAF50)
- Font: Large, Bold for title
- CTA buttons at bottom
"""

# ==================== SCREEN 2: PHONE ENTRY ====================
"""
╔════════════════════════════════╗
║  ← Back        Sign Up         ║
╠════════════════════════════════╣
║                                ║
║   Enter Your Phone Number      ║
║   (Enter once, use forever)    ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ 🇮🇳 +91 │ 9876543210    │ ║
║   └──────────────────────────┘ ║
║                                ║
║   [Continue] (disabled until  ║
║             10 digits)         ║
║                                ║
║   Already registered?          ║
║   [Login]                      ║
║                                ║
╚════════════════════════════════╝

UI FEATURES:
- Country code selector (locked to +91 for India)
- Input validation (real-time)
- Phone icon in field
- Helper text about usage
- Link to login page

VALIDATION:
✓ Exactly 10 digits
✓ Format: XXXX XXXXXX
✓ Real-time feedback
"""

# ==================== SCREEN 3: OTP VERIFICATION ====================
"""
╔════════════════════════════════╗
║  ← Back     Verification       ║
╠════════════════════════════════╣
║                                ║
║   Enter 6-digit OTP            ║
║   Sent to: 98765****10         ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ [_] [_] [_] [_] [_] [_]  │ ║
║   └──────────────────────────┘ ║
║                                ║
║   Timer: 4:55  ⏱️              ║
║                                ║
║   Didn't receive OTP?          ║
║   [Resend OTP] (grayed out)    ║
║                                ║
║   [Continue] (enabled after   ║
║             all 6 entered)     ║
║                                ║
╚════════════════════════════════╝

UI FEATURES:
- 6 separate input boxes (auto-focus next)
- Countdown timer (10 minutes)
- Masked phone number
- Resend button (appears after 30s)
- Auto-submit when all 6 digits entered
- Error message if OTP wrong

ANIMATION:
- Shake animation on wrong OTP
- Green checkmark on correct
"""

# ==================== SCREEN 4: CREATE ACCOUNT ====================
"""
╔════════════════════════════════╗
║  ← Back     Create Account     ║
╠════════════════════════════════╣
║                                ║
║   ┌──────────────────────────┐ ║
║   │ First Name               │ ║
║   │ [_____________________] │ ║
║   └──────────────────────────┘ ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ Last Name (Optional)     │ ║
║   │ [_____________________] │ ║
║   └──────────────────────────┘ ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ Email                    │ ║
║   │ [_____________________] │ ║
║   └──────────────────────────┘ ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ Location/District        │ ║
║   │ [Dropdown ▼]             │ ║
║   └──────────────────────────┘ ║
║                                ║
║   ┌──────────────────────────┐ ║
║   │ Password (8+ chars)      │ ║
║   │ [_____________________] │ ║
║   │         👁 (show)        │ ║
║   └──────────────────────────┘ ║
║                                ║
║   [Create Account] (Green)     ║
║                                ║
╚════════════════════════════════╝

UI FEATURES:
- Progressive disclosure (scroll)
- Input hints for each field
- Show/hide password toggle
- Location dropdown with search
- Form validation (green check marks)
- Error messages below fields
"""

# ==================== SCREEN 5: DASHBOARD (Main Hub) ====================
"""
╔════════════════════════════════╗
║  Ravi Kumar ⚙️ 🔔              ║
╠════════════════════════════════╣
║                                ║
║  ☀️ Sunny, 32°C                ║
║  📍 Hyderabad, Telangana       ║
║                                ║
║  ┌──────────┬──────────────┐  ║
║  │ 📦 4     │ ₹12,450      │  ║
║  │ Products │ Today Sales  │  ║
║  └──────────┴──────────────┘  ║
║                                ║
║  ┌──────────┬──────────────┐  ║
║  │ 📄 2     │ ₹54,230      │  ║
║  │ Pending  │ Total        │  ║
║  │ Orders   │ Earnings     │  ║
║  └──────────┴──────────────┘  ║
║                                ║
║  📋 Recent Orders              ║
║  ┌──────────────────────────┐ ║
║  │ 🍅 Tomato × 10 kg        │ ║
║  │ Buyer: Ramesh - @pending │ ║
║  │ ₹2,500  [Accept] [Reject]│ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ 🥕 Carrot × 5 kg         │ ║
║  │ Buyer: Priya - @accepted │ ║
║  │ ₹1,200  [Track]          │ ║
║  └──────────────────────────┘ ║
║                                ║
║  💡 AI Suggestions             ║
║  ┌──────────────────────────┐ ║
║  │ Crop: Chilli             │ ║
║  │ Price: ₹8,500 per ton    │ ║
║  │ [View Details]           │ ║
║  └──────────────────────────┘ ║
║                                ║
║  Bottom Tab Bar:               ║
║  [Home] [Products] [Orders]    ║
║  [AI] [Wallet]                 ║
║                                ║
╚════════════════════════════════╝

UI COLORS:
- Primary: Green (#4CAF50)
- Secondary: Orange (#FF9800)
- Danger: Red (#f44336)
- Background: Light gray (#f5f5f5)
- Cards: White with shadow

COMPONENTS:
- Stat cards with icons
- Order cards with action buttons
- Weather widget
- Quick action buttons
- Bottom navigation bar
"""

# ==================== SCREEN 6: PRODUCTS MANAGEMENT ====================
"""
╔════════════════════════════════╗
║  My Products             [+Add]║
╠════════════════════════════════╣
║                                ║
║  Filters: [All] [Active] [Low] ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ [🍅 Image]               │ ║
║  │ Tomato - Fresh           │ ║
║  │ Category: Vegetables     │ ║
║  │ Qty: 50 kg, Price: ₹45   │ ║
║  │ ⭐ 4.5 (12 reviews)       │ ║
║  │ [Edit] [View] [Delete]   │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ [🥕 Image]               │ ║
║  │ Carrot - Organic         │ ║
║  │ Category: Vegetables     │ ║
║  │ Qty: 30 kg, Price: ₹60   │ ║
║  │ ⭐ 4.8 (25 reviews)       │ ║
║  │ [Edit] [View] [Delete]   │ ║
║  └──────────────────────────┘ ║
║                                ║
╚════════════════════════════════╝

PRODUCT CARD FEATURES:
- Product image with placeholder
- Name and description
- Category badge
- Quantity and price
- Rating and review count
- Action buttons: Edit, View, Delete
- Stock status (Out, Low, Available)
"""

# ==================== SCREEN 7: ADD PRODUCT ====================
"""
╔════════════════════════════════╗
║  ← Back         Add Product    ║
╠════════════════════════════════╣
║                                ║
║  [📷 Upload Images (3+)]       ║
║  ┌──────────────────────────┐ ║
║  │ [📷] [📷] [📷]           │ ║
║  │ Tap to add more          │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Product Name             │ ║
║  │ [_____________________] │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Category [Dropdown ▼]    │ ║
║  │ (Vegetables, Grains...) │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Description              │ ║
║  │ [_____________________] │ ║
║  │ [_____________________] │ ║
║  │ (e.g., "Fresh, organic")│ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Harvest Date             │ ║
║  │ [📅 DD/MM/YYYY]          │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Quantity [100] [Unit ▼]  │ ║
║  │         kg (kg/ton/bags)  │ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Price per Unit           │ ║
║  │ ₹ [__________] per kg    │ ║
║  └──────────────────────────┘ ║
║                                ║
║  [List Product] [Save Draft]   ║
║                                ║
╚════════════════════════════════╝

UPLOAD LOGIC:
- Multiple image selection (min 3)
- Image preview thumbnails
- Drag-drop support
- Compress images before upload
- S3 integration for storage
"""

# ==================== SCREEN 8: WALLET & EARNINGS ====================
"""
╔════════════════════════════════╗
║  My Wallet               [?]   ║
╠════════════════════════════════╣
║                                ║
║  ╔══════════════════════════╗  ║
║  ║   Available Balance      ║  ║
║  ║   ₹12,450                ║  ║
║  ║                          ║  ║
║  ║   [Withdraw] [Add Bank]  ║  ║
║  ╚══════════════════════════╝  ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ Total Earnings: ₹54,230   │ ║
║  │ Total Withdrawn: ₹41,780  │ ║
║  └──────────────────────────┘ ║
║                                ║
║  Transaction History           ║
║  ┌──────────────────────────┐ ║
║  │ ✅ Order #001            │ ║
║  │ Tomato Sale              │ ║
║  │ +₹2,500           12:30PM│ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ ✅ Withdrawal to SBI     │ ║
║  │ Bank Transfer            │ ║
║  │ -₹10,000         Yesterday│ ║
║  └──────────────────────────┘ ║
║                                ║
║  ┌──────────────────────────┐ ║
║  │ ⏳ Withdrawal Pending    │ ║
║  │ Bank Transfer            │ ║
║  │ -₹5,000      Processing..│ ║
║  └──────────────────────────┘ ║
║                                ║
╚════════════════════════════════╝

WALLET FEATURES:
- Large balance display (primary card)
- Quick action buttons
- Transaction list (newest first)
- Filter by type (credit/debit)
- Withdrawal status tracking
"""

# ==================== COLOR PALETTE ====================
"""
PRIMARY COLORS:
- Green (Primary): #4CAF50 (Trust, Agriculture)
- Orange (Secondary): #FF9800 (Energy, Offers)
- Red (Danger): #f44336 (Cancel, Urgent)

NEUTRAL COLORS:
- Background: #f5f5f5
- Card: #FFFFFF
- Text Primary: #212121 (Dark gray)
- Text Secondary: #757575 (Medium gray)
- Border: #e0e0e0 (Light gray)

SUCCESS/STATUS COLORS:
- Success: #4CAF50
- Warning: #FFC107
- Error: #f44336
- Info: #2196F3
"""

# ==================== TYPOGRAPHY ====================
"""
FONTS:
- Font Family: Roboto / System Font (Android), SF Pro (iOS)

SIZES:
- Title (Large): 28px, Bold
- Heading 1: 24px, Bold
- Heading 2: 20px, Medium
- Body Text: 16px, Regular
- Small Text: 14px, Regular
- Captions: 12px, Regular

WEIGHTS:
- Bold: 700
- Medium: 500
- Regular: 400
"""

# ==================== SPACING ====================
"""
GRID: 8px base unit

PADDING:
- Screens: 16px (2 units)
- Cards: 12px (1.5 units)
- Buttons: 12px horizontal, 8px vertical

MARGINS:
- Between sections: 16px
- Between items: 8px
"""

# ==================== BUTTONS ====================
"""
PRIMARY BUTTON:
- Background: #4CAF50
- Text: White
- Padding: 12px 24px
- Border Radius: 8px
- Height: 44px (touch-friendly)

SECONDARY BUTTON:
- Background: Transparent
- Border: 1px #4CAF50
- Text: #4CAF50
- Padding: 12px 24px

DANGER BUTTON:
- Background: #f44336
- Text: White
- Padding: 12px 24px

BUTTON STATES:
- Normal: Full opacity
- Pressed: 80% opacity
- Disabled: 50% opacity
"""

# ==================== INPUT FIELDS ====================
"""
TEXT INPUT:
- Height: 44px
- Border: 1px #e0e0e0
- Border Radius: 8px
- Padding: 12px 16px
- Focus: Border color → #4CAF50

DROPDOWN:
- Similar to text input
- Shows selected value
- Icon: Chevron down (▼)

ERRORS:
- Text color: #f44336
- Below input field
- Icon: ⚠️
"""

# ==================== CARDS ====================
"""
PRODUCT/ORDER CARD:
- Background: White
- Radius: 8px
- Shadow: elevation 2 (0px 3px 6px rgba(0,0,0,0.12))
- Padding: 12px
- Margin: 8px

STAT CARD:
- 2-column grid
- Icon + Value
- Background: Light color variant
- Clickable for details
"""

# ==================== ANIMATIONS ====================
"""
TRANSITIONS:
- All properties: 200ms ease-in-out
- Color changes: 150ms

LOADING:
- Spinner: Rotating circle (0.8s rotation)
- Skeleton loading for lists

GESTURES:
- Tap feedback: 80% opacity
- Swipe: Slide left for delete
- Pull-to-refresh: Circle animation
"""

# ==================== RESPONSIVENESS ====================
"""
BREAKPOINTS:
- Mobile: Up to 600px (Main)
- Tablet: 600px - 960px

ADJUSTMENTS:
- Font sizes: -2px on smaller devices
- Padding: -4px on smaller devices
- Card width: Full width with margins
"""
