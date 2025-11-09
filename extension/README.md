# AI Message Composer - Chrome Extension

A Chrome extension that rewrites your messages professionally using AI with conversation context stored in Neo4j.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked"
4. Select the `extension` folder

## Features

- 🤖 AI-powered message rewriting
- 💬 Conversation context awareness using RAG
- 🔄 Support for LinkedIn and Gmail
- 📊 Neo4j knowledge graph storage
- ⚙️ Customizable tone and preferences

## Usage

1. Navigate to LinkedIn or Gmail
2. Start composing a message in your own words
3. Click the extension icon that appears in the message field
4. Your message will be rewritten professionally with AI context

## Configuration

Click the extension icon in Chrome toolbar and go to Settings to configure:
- Backend API URL
- LLM Model selection
- Default tone preferences
- Auto-store conversations

## Requirements

- Backend server running (see `../server/README.md`)
- Neo4j database instance
- Chrome browser (Manifest V3 compatible)

