# Peacock Save Editor - Advanced JSON Editor for Hitman

![Editor Preview](preview.png) <!-- Add a screenshot here if available -->

An advanced GUI-based JSON editor specifically designed for modifying Peacock (Hitman fan server) user save files. Provides both tree-based and raw JSON editing with cheat features for common modifications.

## Features

### Core Functionality
- **Automatic File Detection**: 
  - Scans common directories to find Peacock user JSON files
  - Supports UUID-patterned filenames in Peacock/userdata/users folders
- **Dual Editing Modes**:
  - **Tree View**: 
    - Hierarchical display of JSON structure
    - Editable values with type detection
    - Copy/paste paths/values through context menu
  - **Raw JSON Editor**:
    - Syntax highlighting (strings, numbers, keywords)
    - Real-time synchronization with tree view
    - Error checking with JSON validation
- **Advanced Search**:
  - Quick search for common values (money, XP, profile levels)
  - Auto-expand parents for found items
  - Search-as-you-type with 500ms debounce

### Cheat System
- **Bulk Operations**:
  - Set All Location Levels (1-100)
  - Set All Sublocations XP/ActionXP
  - Set Challenge Progression States (Ticked/Completed)
- **Data Copying Tools**:
  - Copy Locations to Sublocations
  - Mirror Peacock Escalations to:
    - Played Contracts
    - Completed Escalations
- **Context-Aware Editing**:
  - Multi-select editing
  - Add/remove keys through context menu
  - Path display for selected nodes

### UX Features
- Real-time JSON validation
- Status bar notifications
- Clipboard integration
- Keyboard shortcuts (Ctrl+S, Ctrl+Q, Ctrl+F)
- Collapsible/expandable tree nodes
- Path breadcrumbs for navigation

## Installation

### Prerequisites
- Python 3.9+
- Pip package manager

### Steps
1. Clone repository:
   ```bash
   git clone https://github.com/yourusername/peacock-save-editor.git
   cd peacock-save-editor
