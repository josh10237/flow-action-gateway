# Abstract - Wispr Actions

## The Problem

There are ~200 apps with 100M+ users, and the long tail is massive—each user has their own niche tools (Linear, Notion, Superhuman, etc.). To cover even 80% of user workflows, we'd need thousands of custom integrations, each requiring ongoing maintenance as APIs change. Building and maintaining N point-to-point integrations simply doesn't scale.

## The Solution

**Wispr Actions** is a voice-controlled gateway that uses the Model Context Protocol (MCP) to provide a single intelligent interface to any application. Instead of building thousands of first-party integrations, we build ONE gateway that dynamically discovers and routes to MCP servers—which app providers themselves are already building and maintaining. Users authenticate with each app they want to use, and we inherit the entire MCP ecosystem without writing custom integration code.

## Core Innovation

As the MCP ecosystem grows, our system automatically becomes more powerful **without any code changes**. Adding a new service is pure configuration—we inherit app providers' MCP servers instead of building and maintaining our own integrations.

## Key Differentiators

- **Scalability:** O(1) integration effort per service (vs O(N) for custom integrations)
- **Ecosystem leverage:** Automatically benefits from community MCP servers as they're built
- **Intelligent routing:** Single LLM call understands intent and routes across all services
- **Zero maintenance:** App providers maintain their own MCP servers; API changes are their problem, not ours
