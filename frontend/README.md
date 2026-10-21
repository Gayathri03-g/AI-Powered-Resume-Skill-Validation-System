# 🎨 Frontend - Skill Assessment System

Premium, interactive frontend built with HTML, CSS, and Three.js.

## ✨ Features

### Visual Excellence
- **Three.js 3D Background**: Animated particle system with geometric shapes
- **Glassmorphism Design**: Modern frosted glass effects with backdrop blur
- **Premium Color Palette**: Vibrant gradients, no basic colors
- **Micro-animations**: Smooth transitions and hover effects
- **Responsive Design**: Mobile-first, works on all devices

### Components
- ✅ **Navbar** - Sticky navigation with glassmorphism
- ✅ **Hero Section** - Eye-catching landing with floating cards
- ✅ **How It Works** - 5-step process visualization
- ✅ **Features Grid** - Showcases key capabilities
- ✅ **Upload Modal** - Drag-and-drop file upload
- ✅ **Footer** - Complete site navigation

### Interactions
- 🖱️ Mouse-reactive 3D background
- 📜 Scroll-triggered animations
- 📤 Drag & drop file upload
- ⌨️ Keyboard shortcuts (ESC to close modal)
- 🎯 Smooth scroll navigation

## 📁 Structure

```
frontend/
├── index.html              # Main landing page
├── css/
│   ├── reset.css          # Modern CSS reset
│   ├── design-system.css  # Color palette, typography, spacing
│   ├── components.css     # Reusable UI components
│   └── pages.css          # Page layouts and sections
└── js/
    ├── three-background.js # Three.js particle system
    ├── animations.js       # Scroll animations, interactions
    └── app.js             # Main app logic, API calls
```

## 🚀 Usage

### Local Development
The frontend is automatically served by the FastAPI backend:

1. Start the backend:
   ```bash
   python run.py
   ```

2. Open browser:
   ```
   http://localhost:8000
   ```

### Standalone (Optional)
You can also serve the frontend with any static file server:

```bash
# Python
python -m http.server 3000

# Node.js
npx serve frontend -p 3000
```

## 🎨 Design System

### Colors
```css
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
--accent-primary: hsl(250, 70%, 65%);
--accent-cyan: hsl(185, 100%, 60%);
```

### Typography
- **Font**: Inter (modern, clean)
- **Mono**: JetBrains Mono (code)
- **Scale**: Fluid responsive type (clamp)

### Spacing
- Uses 8px base grid
- Consistent spacing tokens
- Responsive padding/margins

## 🔌 API Integration

The frontend connects to the FastAPI backend at:
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### Implemented Endpoints
- ✅ `GET /api/v1/health` - Health check
- ⏳ `POST /api/v1/upload-resume` - Resume upload (CHUNK 1.2)
- ⏳ More endpoints coming in future chunks...

## 🎬 Animations

### Entrance Animations
- `fadeInUp` - Content slides up with fade
- `fadeInDown` - Navbar slides down
- `scaleIn` - Modal pop-in effect

### Continuous Animations
- `float` - Floating cards movement
- `pulse` - Badge pulsing
- `shimmer` - Loading states

### Scroll Animations
- Intersection Observer for section reveals
- Parallax floating cards
- Active nav link highlighting

## 📱 Responsive Breakpoints

```css
/* Desktop First */
1024px - Tablet (stacks hero, 2-col footer)
768px  - Mobile (single column, simplified nav)
```

## 🎯 Next Steps

Future pages to build:
- [ ] Quiz Page - Assessment interface
- [ ] Coding Challenge Page - Code editor
- [ ] Results Page - Final report
- [ ] Dashboard - User analytics

---

**Built with premium aesthetics and zero ambiguity.**  
No placeholders. No basic colors. Pure visual excellence.
