# GePS - Government e-Procurement System (Frontend)

AI-based tender evaluation and eligibility analysis system for CRPF procurement.

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Application Flow](#application-flow)
- [Navigation Rules](#navigation-rules)
- [Demo Mode vs Real Data Mode](#demo-mode-vs-real-data-mode)
- [Mock Data Usage](#mock-data-usage)
- [Current Feature Status](#current-feature-status)
- [Future Enhancements](#future-enhancements)
- [Dependencies](#dependencies)
- [Color Scheme](#color-scheme)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** v18 or higher ([Download](https://nodejs.org/))
- **npm** v9 or higher (comes with Node.js)

### Installation & Running

```bash
# 1. Clone or download the project
cd geps-frontend

# 2. Install all dependencies
npm install

# 3. Start the development server
npm start
```

The application will automatically open at `http://localhost:3000`

#### Alternative - Using different port
```bash
npm start -- --port 3001
```

---

## 📁 Project Structure

```
geps-frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── HomePage.jsx           # Landing page with feature cards
│   │   ├── TenderUpload.jsx       # Tender document upload
│   │   ├── BidderUpload.jsx       # Bidder documents upload
│   │   ├── ProcessingPage.jsx     # AI evaluation with progress animation
│   │   ├── ResultsPage.jsx        # Evaluation results display
│   │   ├── HumanReviewPage.jsx    # Manual review interface
│   │   ├── FeedbackPage.jsx       # Analytics dashboard
│   │   └── Navbar.jsx             # Navigation with step indicators
│   ├── context/
│   │   └── AppContext.jsx         # Global state management (no persistence yet)
│   ├── services/
│   │   └── api.js                 # API service layer + MOCK data
│   ├── utils/
│   │   └── helpers.js             # Utility functions
│   ├── App.jsx                    # Main app with routing
│   ├── index.js                   # Entry point
│   └── index.css                  # Global styles with CSS variables
├── package.json
└── README.md
```

---

## 🔄 Application Flow

### Step-by-Step Process

```
Home → Tender Upload → Add Bidders → Processing → Results → Review → Feedback
  ↓         ↓              ↓            ↓          ↓         ↓          ↓
Start    Upload PDF    Add bidders    AI        View      Manual     Analytics
         document      & documents    evaluates  results   review     dashboard
```

### Detailed Flow Description

1. **Home Page** - Landing page showing feature cards and system overview
2. **Tender Upload** - Upload tender PDF document (max 50MB, validation included)
3. **Add Bidders** - Add multiple bidders, upload their supporting documents
4. **Processing** - AI evaluates documents with animated progress stages
5. **Results** - View detailed evaluation results per bidder with expandable tables
6. **Review** - Manually review low-confidence cases with override capability
7. **Feedback** - Analytics dashboard showing error distribution and accuracy trends

---

## 🚦 Navigation Rules

### What's Enabled (Accessible)

| Step | Accessibility | Condition |
|------|---------------|-----------|
| Home | ✅ Always | No conditions |
| Tender Upload | ✅ Always | No conditions |
| Add Bidders | 🔒 Conditional | Requires: Tender document uploaded first |
| Processing | ✅ Always | Shows demo if no data, real processing if data exists |
| Results | ✅ Always | Shows demo if no data, real results if evaluation done |
| Review | 🔒 Conditional | Requires: Evaluation results exist |
| Feedback | ✅ Always | No conditions |

### Warning Messages

| Trying to access | Warning Message |
|------------------|-----------------|
| Add Bidders (no tender) | ⚠️ Please upload a tender document first before adding bidders. |
| Processing (no tender/docs) | (Shows demo mode instead, no warning) |
| Results (no evaluation) | (Shows demo results instead, no warning) |
| Review (no results) | ⚠️ Please complete the evaluation first. Go to Processing page. |

---

## 🎭 Demo Mode vs Real Data Mode

### Intelligent Mode Switching

The application automatically switches between Demo and Real mode based on uploaded data:

| Scenario | Mode | Processing Page Shows | Results Page Shows |
|----------|------|----------------------|-------------------|
| No documents uploaded | 🎬 Demo | "🎬 Demo Evaluation Complete" with sample data | "🎬 Demo Evaluation Results" with mock data |
| Documents uploaded, not evaluated | 📄 Real Ready | "Ready to Evaluate" with real file names | "Run evaluation first" message |
| Evaluation completed | ✅ Real Results | "✅ Evaluation Complete" with real summary | Real results with actual bidder names |

### Visual Indicators

| Element | Demo Mode | Real Mode |
|---------|-----------|-----------|
| Theme Color | Purple (#8b5cf6) | Blue (#3b82f6) |
| Badge | 🎬 Demo Mode | ✓ Evaluation Complete |
| Button Text | "🎬 Try Demo Evaluation" | "🚀 Start AI Evaluation" |
| Result Title | "🎬 Demo Evaluation Results" | "✅ Evaluation Results" |

---

## 📊 Mock Data Usage

### Where Mock Data is Used

Mock data is defined in `src/services/api.js` as `MOCK_EVALUATION_RESULTS` and includes:

```javascript
{
  tender_id: 'T-2026-001',
  tender_name: 'CRPF Infrastructure Development Tender',
  bidders: [
    {
      bidder_name: 'ABC Infrastructure Pvt. Ltd.',
      overall_verdict: 'ELIGIBLE',
      overall_confidence: 0.92,
      criteria: [ /* Financial, Technical, Compliance criteria */ ]
    },
    {
      bidder_name: 'XYZ Construction Ltd.',
      overall_verdict: 'NOT ELIGIBLE',
      overall_confidence: 0.85
    },
    {
      bidder_name: 'Sunrise Builders & Co.',
      overall_verdict: 'NEEDS REVIEW',
      overall_confidence: 0.64
    }
  ],
  review_queue: [ /* Items needing human review */ ],
  audit_log: [ /* System audit trail */ ]
}
```

### When Mock Data is Displayed

| Page | Mock Data Usage |
|------|-----------------|
| Processing Page | Shows demo evaluation when no real documents uploaded |
| Results Page | Shows demo results when no real evaluation exists |
| Home Page | Shows "🎬 Try Demo Evaluation" and "🎬 View Demo Results" badges |

### When Real Data Takes Over

- Once user uploads a tender document → Real data mode activates
- Once user adds bidders → Real file names appear in summary
- Once evaluation completes → Real results stored in context

---

## ✅ Current Feature Status

### Fully Functional Features

| Feature | Status | Description |
|---------|--------|-------------|
| Tender PDF Upload | ✅ Working | Drag-drop, validation, file size check (50MB max) |
| Multiple Bidder Management | ✅ Working | Add/delete bidders, rename, upload documents per bidder |
| Document Upload per Bidder | ✅ Working | PDF, PNG, JPG support, delete individual files |
| AI Evaluation Animation | ✅ Working | Progress stages with animated loader |
| Results Dashboard | ✅ Working | Expandable bidder cards, detailed criteria tables |
| Human Review Interface | ✅ Working | Queue management, override decisions, error classification |
| Feedback Analytics | ✅ Working | Charts for error distribution, accuracy trends |
| Navigation with Guards | ✅ Working | Warning popups, disabled states, step indicators |
| Demo Mode | ✅ Working | Purple theme, sample data, clear demo indicators |
| Responsive Design | ✅ Working | Works on desktop and tablet |

### Currently Using Mock Data (No Backend)

| Component | Mock Data Source | Real Data Alternative |
|-----------|------------------|----------------------|
| Processing Results | MOCK_EVALUATION_RESULTS | Would come from backend API |
| Evaluation Logic | Simulated with progress | Would use actual ML models |
| File Storage | Browser memory | Would upload to server |
| User Authentication | Not implemented | Would use OAuth/SSO |

### Disabled (Conditional Access)

| Feature | Disabled Until |
|---------|----------------|
| Add Bidders | Tender document uploaded |
| Review Tab | Evaluation results exist |
| Processing (real mode) | Tender + bidders added |

---

## 🔮 Future Enhancements

### Phase 1 - Backend Integration (To Be Enabled)

```javascript
// Currently using mock data:
const results = MOCK_EVALUATION_RESULTS;

// Future implementation:
const results = await fetch('/api/evaluate', {
  method: 'POST',
  body: JSON.stringify({ tenderId, bidderIds })
});
```

**Planned Backend Features:**
- Real OCR processing for scanned documents
- Actual LLM-based rule extraction
- Persistent document storage
- User authentication and sessions

### Phase 2 - Extended Features (To Be Added)

| Feature | Status | Priority |
|---------|--------|----------|
| Document Versioning | 🔜 Planned | High |
| Fraud Detection Alerts | 🔜 Planned | High |
| Multi-language Support (Hindi, Kannada) | 🔜 Planned | Medium |
| Export Reports (PDF, Excel) | 🔜 Planned | Medium |
| Email Notifications | 🔜 Planned | Low |
| Bidder Comparison View | 🔜 Planned | Low |

### Phase 3 - Performance Optimizations (To Be Implemented)

- Lazy loading for large components
- Pagination for bidder lists (for 50+ bidders)
- Caching evaluation results in localStorage
- Virtual scrolling for criteria tables

---

## 📦 Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.2.0 | UI library |
| react-dom | ^18.2.0 | DOM rendering |
| react-scripts | 5.0.1 | Build tooling |

### UI & Styling

| Package | Version | Purpose |
|---------|---------|---------|
| framer-motion | ^11.0.0 | Smooth animations |
| lucide-react | ^0.383.0 | Modern icons |
| recharts | ^2.12.0 | Charts for analytics |

### File Upload & Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| react-dropzone | ^14.2.3 | Drag-drop file upload |
| react-router-dom | ^6.22.0 | Navigation (minimal) |

### All Dependencies Installation

```bash
npm install react react-dom react-scripts framer-motion lucide-react recharts react-dropzone react-router-dom
```

---

## 🎨 Color Scheme

### Primary Colors

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| Primary Blue | #1e40af | Buttons, active links, logo |
| Secondary Blue | #3b82f6 | Hover states, accents |
| Success Green | #10b981 | PASS/Eligible status |
| Error Red | #ef4444 | FAIL/Not Eligible status |
| Warning Orange | #f59e0b | NEEDS REVIEW status |
| Demo Purple | #8b5cf6 | Demo mode indicators |

### Status Badges

| Status | Background | Text Color | Border |
|--------|-----------|-----------|--------|
| PASS/Eligible | #dcfce7 | #166534 | #bbf7d0 |
| FAIL/Not Eligible | #fee2e2 | #991b1b | #fecaca |
| NEEDS REVIEW | #fed7aa | #92400e | #fed7aa |
| Pending | #f1f5f9 | #475569 | #e2e8f0 |

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue 1: 'react-scripts' is not recognized

```bash
# Solution: Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Issue 2: Port 3000 already in use

```bash
# Solution A: Kill the process using port 3000
# Windows: netstat -ano | findstr :3000
# Mac/Linux: lsof -i :3000
# Then kill the process ID

# Solution B: Use different port
npm start -- --port 3001
```

#### Issue 3: Blank page / components not loading

```bash
# Solution: Clear browser cache and hard refresh
# Chrome/Edge: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
# Firefox: Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)
```

#### Issue 4: File upload not working

```bash
# Check: File size must be less than 50MB
# Check: File type must be PDF
# Check: Browser console for errors (F12)
```

#### Issue 5: Styles not applying correctly

```bash
# Solution: Clear browser cache or use incognito mode
# Or restart development server
npm start
```

### Debugging Tips

- **Check Browser Console (F12)** - Look for red error messages
- **Check Network Tab** - See if API calls are working (when backend integrated)
- **LocalStorage** - Application state is stored here, clear if needed:

```javascript
localStorage.clear(); // Run in browser console
```

- **React DevTools** - Install extension to inspect component state

---

## 📝 Important Notes

### Current Limitations

- **No Backend Integration** - All data is client-side only
- **File Storage** - Files are stored in browser memory, not uploaded to server
- **Evaluation Logic** - Simulated with progress animation, not real AI
- **Authentication** - No login system, single user mode
- **Persistence** - State resets on page refresh (no localStorage yet)

### Data Persistence Status

| Data Type | Persistence | Method |
|-----------|-------------|--------|
| Tender File | ❌ Lost on refresh | Browser memory only |
| Bidder Documents | ❌ Lost on refresh | Browser memory only |
| Evaluation Results | ❌ Lost on refresh | Browser memory only |
| Review Decisions | ❌ Lost on refresh | Browser memory only |
| Feedback Log | ❌ Lost on refresh | Browser memory only |

### Demo Data Details

The mock data includes:
- 3 sample bidders (Eligible, Not Eligible, Needs Review)
- 5 criteria per bidder (Financial, Technical, Compliance, Certification)
- 2 review queue items for manual review
- 7 audit log entries showing system actions

---

## 📄 License

Internal use only - CRPF Government Procurement System

---

## 👥 Support

For issues or questions:
- Check the [troubleshooting](#troubleshooting) section above
- Verify Node.js version with `node --version`
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall as last resort