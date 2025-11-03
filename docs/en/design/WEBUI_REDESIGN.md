# Web UI Redesign - VS Code Copilot Inspired Interface

**Created:** November 3, 2025  
**Status:** Design Specification  
**Target:** Sophia 2.0 Web Interface  
**Inspiration:** VS Code Copilot Chat, Claude.ai, ChatGPT

---

## 🎯 Design Goals

### Primary Objectives
1. **Professional & Clean** - Modern, minimalist design similar to VS Code
2. **Real-time Communication** - Instant feedback, live status updates
3. **Multi-tasking Visibility** - Show all active tasks/conversations
4. **Developer-Friendly** - Code highlighting, markdown rendering, keyboard shortcuts
5. **Accessibility** - Dark/light themes, responsive design, screen reader support

### Success Criteria
- ✅ User can see Sophia's current state at a glance
- ✅ Multiple conversations in tabs (like browser tabs)
- ✅ Code blocks have syntax highlighting
- ✅ Real-time updates without page refresh
- ✅ Works on desktop, tablet, mobile
- ✅ Load time < 2 seconds

---

## 🎨 Visual Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] Sophia 2.0          [Status] [Settings] [Theme] [⋮] │  Header (60px)
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┬─────────────────────────────────────────────┐ │
│  │          │  ┌─────────────────────────────────────┐    │ │
│  │          │  │ Tab 1 │ Tab 2 │ Tab 3 │ [+]         │    │ │  Tabs (40px)
│  │          │  └─────────────────────────────────────┘    │ │
│  │          │                                              │ │
│  │ Sidebar  │  ┌──────────────────────────────────────┐  │ │
│  │          │  │                                        │  │ │
│  │ - Conv   │  │   Message List (Scrollable)           │  │ │
│  │ - Tasks  │  │                                        │  │ │  Main Area
│  │ - Memory │  │   [User]: Hello                       │  │ │
│  │ - Logs   │  │   [Sophia]: Hi! How can I help?       │  │ │
│  │ - Files  │  │                                        │  │ │
│  │          │  │                                        │  │ │
│  │ (240px)  │  └──────────────────────────────────────┘  │ │
│  │          │                                              │ │
│  │          │  ┌──────────────────────────────────────┐  │ │
│  │          │  │ [📎] Type your message...      [Send]│  │ │  Input (80px)
│  │          │  └──────────────────────────────────────┘  │ │
│  └──────────┴─────────────────────────────────────────────┘ │
│                                                               │
│  [Phase: LISTENING] [Plugin: tool_llm] [Memory: 45MB/20GB]  │  Status Bar (30px)
└─────────────────────────────────────────────────────────────┘
```

### Color Scheme

#### Dark Theme (Default)
```css
--bg-primary: #1e1e1e;          /* VS Code dark background */
--bg-secondary: #252526;        /* Sidebar background */
--bg-tertiary: #2d2d30;         /* Elevated surfaces */
--text-primary: #cccccc;        /* Main text */
--text-secondary: #858585;      /* Muted text */
--accent-primary: #007acc;      /* Links, buttons */
--accent-secondary: #00a8e8;    /* Hover states */
--success: #4ec9b0;             /* Success messages */
--warning: #ce9178;             /* Warnings */
--error: #f48771;               /* Errors */
--border: #3e3e42;              /* Borders, dividers */
```

#### Light Theme
```css
--bg-primary: #ffffff;
--bg-secondary: #f3f3f3;
--bg-tertiary: #e8e8e8;
--text-primary: #333333;
--text-secondary: #6c6c6c;
--accent-primary: #0066cc;
--accent-secondary: #005bb5;
--success: #16825d;
--warning: #b87333;
--error: #d73a49;
--border: #d4d4d4;
```

---

## 🧩 Component Specifications

### 1. Header Component

**Purpose:** Branding, global actions, status indicator

```html
<header class="sophia-header">
  <div class="header-left">
    <img src="/logo.svg" alt="Sophia" class="logo" />
    <span class="version">v2.0</span>
    <span class="status-indicator" data-state="active">
      ● Active
    </span>
  </div>
  
  <div class="header-right">
    <button class="icon-btn" title="Settings">⚙️</button>
    <button class="icon-btn" title="Toggle Theme">🌓</button>
    <button class="icon-btn" title="Menu">⋮</button>
  </div>
</header>
```

**States:**
- `active` (green dot) - Sophia is responsive
- `thinking` (blue pulse) - Processing
- `error` (red dot) - Error state
- `offline` (gray dot) - Not connected

### 2. Sidebar Component

**Purpose:** Navigation, context switching, system overview

```html
<aside class="sidebar">
  <nav class="sidebar-nav">
    <button class="nav-item active" data-view="conversations">
      💬 Conversations
    </button>
    <button class="nav-item" data-view="tasks">
      ✓ Active Tasks <span class="badge">3</span>
    </button>
    <button class="nav-item" data-view="memory">
      🧠 Memory <span class="usage">45MB/20GB</span>
    </button>
    <button class="nav-item" data-view="logs">
      📄 Logs
    </button>
    <button class="nav-item" data-view="files">
      📁 Sandbox Files
    </button>
  </nav>
  
  <!-- View-specific content -->
  <div class="sidebar-content" data-view="conversations">
    <div class="conversation-item active">
      <div class="conv-title">Code Review Task</div>
      <div class="conv-meta">2 min ago</div>
    </div>
    <!-- More conversations -->
  </div>
</aside>
```

### 3. Tab Bar Component

**Purpose:** Multiple simultaneous conversations

```html
<div class="tab-bar">
  <div class="tab active" data-session="session-1">
    <span class="tab-title">General Chat</span>
    <button class="tab-close">×</button>
  </div>
  <div class="tab" data-session="session-2">
    <span class="tab-title">Code Review</span>
    <button class="tab-close">×</button>
  </div>
  <button class="tab-new" title="New Conversation">+</button>
</div>
```

**Features:**
- Drag to reorder tabs
- Close with middle-click
- Keyboard shortcuts (Ctrl+1-9 to switch)
- Unsaved indicator (dot before title)

### 4. Message List Component

**Purpose:** Conversation history display

```html
<div class="message-list" id="messageList">
  <!-- User Message -->
  <div class="message user-message">
    <div class="message-header">
      <img src="/user-avatar.svg" class="avatar" />
      <span class="sender">You</span>
      <span class="timestamp">14:23</span>
    </div>
    <div class="message-content">
      <p>Can you analyze the kernel.py file?</p>
    </div>
  </div>
  
  <!-- Sophia Message -->
  <div class="message sophia-message">
    <div class="message-header">
      <img src="/sophia-avatar.svg" class="avatar" />
      <span class="sender">Sophia</span>
      <span class="timestamp">14:23</span>
      <span class="model-badge">DeepSeek Chat</span>
    </div>
    <div class="message-content">
      <p>I'll analyze <code>core/kernel.py</code> for you.</p>
      
      <!-- Code Block with Syntax Highlighting -->
      <pre class="code-block" data-lang="python"><code class="language-python">class Kernel:
    """
    Manages the main lifecycle (Consciousness Loop)
    """
    def __init__(self):
        self.plugin_manager = PluginManager()
        ...</code></pre>
      
      <p>The kernel implements the consciousness loop pattern...</p>
    </div>
    <div class="message-actions">
      <button class="action-btn" title="Copy">📋</button>
      <button class="action-btn" title="Regenerate">🔄</button>
      <button class="action-btn" title="Edit">✏️</button>
    </div>
  </div>
  
  <!-- Thinking Indicator -->
  <div class="message sophia-message thinking">
    <div class="message-header">
      <img src="/sophia-avatar.svg" class="avatar" />
      <span class="sender">Sophia</span>
    </div>
    <div class="message-content">
      <div class="thinking-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="phase-text">Planning...</span>
      </div>
    </div>
  </div>
</div>
```

**Message Types:**
- User messages (right-aligned in some designs, left in VS Code style)
- Sophia text responses (markdown rendered)
- Code blocks (syntax highlighted via Prism.js or Highlight.js)
- Tool execution results (collapsible)
- Error messages (red border, error icon)
- System messages (gray, italic)

### 5. Input Area Component

**Purpose:** User message input with attachments, voice, commands

```html
<div class="input-area">
  <div class="input-toolbar">
    <button class="toolbar-btn" title="Attach File">📎</button>
    <button class="toolbar-btn" title="Voice Input">🎤</button>
    <button class="toolbar-btn" title="Insert Code">💻</button>
    <button class="toolbar-btn" title="Commands">/</button>
  </div>
  
  <div class="input-wrapper">
    <textarea 
      id="messageInput"
      class="message-input"
      placeholder="Type your message... (Shift+Enter for new line)"
      rows="1"
      autofocus
    ></textarea>
    <button class="send-btn" id="sendBtn" disabled>
      <span class="send-icon">➤</span>
    </button>
  </div>
  
  <div class="input-hints">
    <span class="hint">Tip: Use <code>/help</code> for commands</span>
  </div>
</div>
```

**Features:**
- Auto-resize textarea as user types
- Send on Enter, new line on Shift+Enter
- File drag-and-drop support
- Paste images/files
- Command autocomplete (when typing `/`)
- Character/token counter (optional)

### 6. Status Bar Component

**Purpose:** System status, phase indicator, resource usage

```html
<footer class="status-bar">
  <div class="status-left">
    <span class="status-item phase">
      <span class="phase-icon">🔄</span>
      <span class="phase-text">Phase: LISTENING</span>
    </span>
    <span class="status-item plugin">
      <span class="plugin-icon">🔧</span>
      <span class="plugin-text">Plugin: None</span>
    </span>
  </div>
  
  <div class="status-right">
    <span class="status-item memory">
      🧠 Memory: 45MB/20GB
    </span>
    <span class="status-item budget">
      💰 Budget: $0.23/$1.00 today
    </span>
    <span class="status-item connection">
      <span class="connection-indicator online"></span>
      Connected
    </span>
  </div>
</footer>
```

**Real-time Updates:**
- Phase changes (LISTENING → PLANNING → EXECUTING → etc.)
- Active plugin name
- Memory usage (updates every 30s)
- Budget consumption (updates on each LLM call)
- Connection status (WebSocket state)

---

## ⚡ Interactive Features

### 1. Real-time Streaming

**Sophia's responses stream word-by-word:**
```javascript
// Server sends chunks via WebSocket
socket.on('response_chunk', (chunk) => {
  appendToLastMessage(chunk.text);
  scrollToBottom();
});
```

**User sees:**
```
Sophia: I'll analyze the file for you. The kernel.py 
        file contains... [text appears gradually]
```

### 2. Tool Execution Visualization

**When Sophia uses tools, show progress:**

```html
<div class="tool-execution">
  <div class="tool-header">
    <span class="tool-icon">🔧</span>
    <span class="tool-name">tool_file_system.read_file</span>
    <span class="tool-status running">Running...</span>
  </div>
  <div class="tool-details collapsed">
    <pre class="tool-args">
{
  "file_path": "core/kernel.py",
  "start_line": 1,
  "end_line": 50
}
    </pre>
  </div>
  <div class="tool-result">
    <pre class="result-preview">
Lines 1-50 of core/kernel.py (click to expand)
    </pre>
  </div>
</div>
```

**States:**
- `queued` - Waiting to execute
- `running` - Currently executing (spinner)
- `success` - Completed (green checkmark)
- `failed` - Error (red X, show error message)

### 3. Code Block Features

**Interactive code blocks:**
```html
<div class="code-block-wrapper">
  <div class="code-header">
    <span class="code-lang">Python</span>
    <div class="code-actions">
      <button class="code-btn" data-action="copy">📋 Copy</button>
      <button class="code-btn" data-action="insert">➕ Insert to Sandbox</button>
      <button class="code-btn" data-action="run">▶️ Run</button>
    </div>
  </div>
  <pre class="code-content"><code class="language-python">
# Syntax highlighted code here
def hello():
    print("Hello, Sophia!")
  </code></pre>
</div>
```

### 4. Markdown Rendering

**Full markdown support:**
- **Bold**, *italic*, `code`
- Headers (H1-H6)
- Lists (ordered, unordered, checklists)
- Tables
- Blockquotes
- Links (open in new tab)
- Images (inline preview)
- Math equations (KaTeX)

### 5. Keyboard Shortcuts

```
Ctrl/Cmd + Enter     - Send message
Ctrl/Cmd + K         - Clear conversation
Ctrl/Cmd + /         - Show command palette
Ctrl/Cmd + N         - New conversation tab
Ctrl/Cmd + W         - Close current tab
Ctrl/Cmd + 1-9       - Switch to tab N
Ctrl/Cmd + L         - Focus input
Ctrl/Cmd + F         - Search in conversation
Esc                  - Cancel current operation
```

### 6. Command Palette

**Type `/` to open command palette:**
```
/help           - Show all commands
/clear          - Clear current conversation
/new            - Start new conversation
/save           - Save conversation
/load           - Load conversation
/export         - Export as markdown
/settings       - Open settings
/stop           - Emergency stop
/debug          - Show debug panel
```

---

## 🎭 Theme System

### Theme Switcher

```javascript
const themes = {
  dark: 'VS Code Dark',
  light: 'VS Code Light',
  highContrast: 'High Contrast',
  custom: 'Custom Theme'
};

function setTheme(themeName) {
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem('sophia-theme', themeName);
}
```

### Auto Theme Detection
```javascript
// Follow system preference
if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  setTheme('dark');
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', e => {
    setTheme(e.matches ? 'dark' : 'light');
  });
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile: < 768px */
@media (max-width: 767px) {
  .sidebar { display: none; } /* Hide sidebar, show hamburger menu */
  .tab-bar { overflow-x: auto; } /* Horizontal scroll for tabs */
}

/* Tablet: 768px - 1024px */
@media (min-width: 768px) and (max-width: 1024px) {
  .sidebar { width: 200px; } /* Narrower sidebar */
}

/* Desktop: > 1024px */
@media (min-width: 1025px) {
  .sidebar { width: 240px; }
  /* Full feature set */
}
```

### Mobile Adaptations
- Sidebar becomes bottom sheet (swipe up)
- Tabs become dropdown menu
- Status bar condensed (icons only)
- Touch-optimized buttons (min 44px)
- No hover states, use long-press

---

## 🔌 WebSocket Communication

### Message Protocol

**Client → Server:**
```json
{
  "type": "user_message",
  "session_id": "session-uuid",
  "content": "Hello, Sophia!",
  "timestamp": "2025-11-03T14:23:00Z"
}
```

**Server → Client:**
```json
{
  "type": "response_chunk",
  "session_id": "session-uuid",
  "chunk": "Hello! How can I help you today?",
  "is_final": false
}
```

**Status Updates:**
```json
{
  "type": "status_update",
  "phase": "EXECUTING",
  "plugin": "tool_llm",
  "timestamp": "2025-11-03T14:23:05Z"
}
```

**Tool Execution:**
```json
{
  "type": "tool_start",
  "tool_name": "tool_file_system.read_file",
  "arguments": {"file_path": "core/kernel.py"}
}

{
  "type": "tool_complete",
  "tool_name": "tool_file_system.read_file",
  "result": "...",
  "success": true
}
```

---

## 🎨 UI Components Library

### Technology Stack

**Frontend:**
- **Framework:** Vue.js 3 or React 18 (lightweight, reactive)
- **Styling:** Tailwind CSS + Custom CSS Variables
- **Icons:** Lucide Icons or Heroicons
- **Syntax Highlighting:** Prism.js or Highlight.js
- **Markdown:** Marked.js + DOMPurify (XSS protection)
- **Math:** KaTeX
- **WebSocket:** Socket.io-client
- **State:** Pinia (Vue) or Zustand (React)

**Backend (already exists):**
- FastAPI + WebSockets (from `interface_webui.py`)

### Component Examples

#### Button Component
```vue
<template>
  <button 
    :class="['btn', `btn-${variant}`, { 'btn-loading': loading }]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="spinner"></span>
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'primary' }, // primary, secondary, danger
  loading: Boolean,
  disabled: Boolean
});
</script>
```

#### Message Component
```vue
<template>
  <div :class="['message', `message-${sender}`]">
    <div class="message-header">
      <img :src="avatarSrc" class="avatar" />
      <span class="sender-name">{{ senderName }}</span>
      <span class="timestamp">{{ formattedTime }}</span>
    </div>
    <div class="message-content" v-html="renderedContent"></div>
    <div v-if="sender === 'sophia'" class="message-actions">
      <button @click="copyMessage">📋</button>
      <button @click="regenerate">🔄</button>
    </div>
  </div>
</template>
```

---

## 🚀 Implementation Plan

### Phase 1: Core UI (Week 1)
- [ ] Set up Vue.js/React project
- [ ] Implement layout (header, sidebar, main, status bar)
- [ ] Create basic message list
- [ ] WebSocket connection
- [ ] Theme system (dark/light)

### Phase 2: Rich Features (Week 2)
- [ ] Syntax highlighting for code blocks
- [ ] Markdown rendering
- [ ] File attachment support
- [ ] Command palette
- [ ] Keyboard shortcuts

### Phase 3: Advanced Features (Week 3)
- [ ] Tab system for multiple conversations
- [ ] Tool execution visualization
- [ ] Real-time status updates
- [ ] Sidebar views (tasks, memory, logs)
- [ ] Responsive design (mobile/tablet)

### Phase 4: Polish & Testing (Week 4)
- [ ] Accessibility (ARIA labels, keyboard nav)
- [ ] Performance optimization
- [ ] Error handling & retry logic
- [ ] User testing & feedback
- [ ] Documentation

---

## 📐 Design Mockups (ASCII)

### Desktop View - Chat Active

```
┌──────────────────────────────────────────────────────────────────┐
│ 🤖 Sophia 2.0  v2.0    [●Active]        [⚙️] [🌓] [⋮]           │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┬───────────────────────────────────────────────────┐│
│  │          │ General │ Code Review │ Research │ [+]            ││
│  │          ├───────────────────────────────────────────────────┤│
│  │ 💬 Conv  │                                                    ││
│  │ ✓ Tasks  │  👤 You (14:20)                                   ││
│  │   (3)    │  Can you help me refactor kernel.py?             ││
│  │          │                                                    ││
│  │ 🧠 Memory│  🤖 Sophia (14:20) [DeepSeek Chat]               ││
│  │  45MB    │  Of course! I'll analyze the file structure...   ││
│  │          │                                                    ││
│  │ 📄 Logs  │  🔧 tool_file_system.read_file ✓                 ││
│  │          │  ```python                                        ││
│  │ 📁 Files │  class Kernel:                                    ││
│  │          │      def __init__(self):...                       ││
│  │          │  ```                                              ││
│  │          │                                                    ││
│  │          │  Based on my analysis, I suggest...              ││
│  │          │  [📋 Copy] [🔄 Regenerate]                       ││
│  │          │                                                    ││
│  │          │  🤖 Sophia is thinking...                        ││
│  │          │  ⋯ Planning...                                    ││
│  │          │                                                    ││
│  │          ├───────────────────────────────────────────────────┤│
│  │          │ [📎] Type your message...              [Send ➤]  ││
│  └──────────┴───────────────────────────────────────────────────┘│
│                                                                    │
│ 🔄 EXECUTING | 🔧 tool_llm    🧠 45MB/20GB  💰 $0.23/$1.00  ●On │
└──────────────────────────────────────────────────────────────────┘
```

### Mobile View - Conversation

```
┌────────────────────────────┐
│ ☰  Sophia 2.0    [●] [🌓] │
├────────────────────────────┤
│ ▼ General Chat            │
├────────────────────────────┤
│                            │
│ 👤 You (14:20)             │
│ Help with kernel.py        │
│                            │
│ 🤖 Sophia (14:20)          │
│ Sure! I'll analyze it.     │
│                            │
│ 🔧 read_file ✓             │
│ ```python                  │
│ class Kernel:              │
│ ```                        │
│                            │
│ I suggest refactoring...   │
│                            │
├────────────────────────────┤
│ [📎] Message...   [Send ➤]│
├────────────────────────────┤
│ 🔄 EXECUTING  ●Connected   │
└────────────────────────────┘
```

---

## 🎯 Success Metrics

### Performance
- Initial load: < 2s
- WebSocket latency: < 100ms
- Message render time: < 50ms
- Smooth scrolling: 60 FPS
- Memory usage: < 100MB (desktop)

### Usability
- Time to send first message: < 5s (new user)
- Command discovery: > 80% find help within 30s
- Error recovery: Clear error messages with actions
- Mobile usability: > 4.5/5 user rating

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation: 100% features accessible
- Screen reader support: Full ARIA labels
- Color contrast: > 4.5:1 for text

---

## 🔗 Navigation & Links

**← Back to:** [Implementation Action Plan](../IMPLEMENTATION_ACTION_PLAN.md)  
**Related:** [Terminal UX Design](./TERMINAL_UX_DESIGN.md)  
**Next:** Implementation (Week 1-4 of Sophia 2.0 roadmap)

---

## 📝 Notes for Developers

### Integration with Existing Code

**Current Web UI:** `plugins/interface_webui.py`
```python
class WebUIInterface(BasePlugin):
    def setup(self, config):
        # FastAPI + WebSocket server
        # Serves frontend/chat.html
```

**Replacement Strategy:**
1. Keep existing WebSocket protocol compatible
2. Replace `frontend/chat.html` with new Vue/React app
3. Extend WebSocket messages for new features (status updates, tool visualization)
4. Maintain backwards compatibility during transition

### File Structure
```
frontend/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── components/
│   │   ├── Header.vue
│   │   ├── Sidebar.vue
│   │   ├── MessageList.vue
│   │   ├── Message.vue
│   │   ├── InputArea.vue
│   │   ├── StatusBar.vue
│   │   └── ...
│   ├── composables/
│   │   ├── useWebSocket.js
│   │   ├── useTheme.js
│   │   └── useKeyboard.js
│   ├── stores/
│   │   ├── conversation.js
│   │   ├── ui.js
│   │   └── settings.js
│   └── styles/
│       ├── variables.css
│       ├── themes.css
│       └── components.css
└── public/
    ├── logo.svg
    └── ...
```

---

**Status:** ✅ Design Complete - Ready for Implementation  
**Priority:** HIGH (Part of UX improvement initiative)  
**Estimated Effort:** 3-4 weeks  
**Dependencies:** None (can develop in parallel with backend work)
