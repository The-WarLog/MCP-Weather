# Implementation Plan

- [x] 1. Set up enhanced project structure and configuration


  - Extend existing configuration system to support Gemini API key and search settings
  - Add new dependencies to pyproject.toml for web scraping and enhanced HTTP handling
  - Create configuration validation for all required API keys and settings
  - _Requirements: 5.1, 5.2_

- [x] 2. Implement core data models and validation


  - [ ] 2.1 Create chat service data models
    - Define ChatRequest, ChatResponse dataclasses with proper validation
    - Implement input sanitization functions for chat messages
    - Add unit tests for data model validation

    - _Requirements: 1.2, 1.3_

  - [ ] 2.2 Create search service data models
    - Define SearchResult, SearchResponse dataclasses
    - Implement query validation and sanitization functions
    - Add unit tests for search data models


    - _Requirements: 3.1, 3.2_

- [ ] 3. Implement Gemini Chat Service
  - [ ] 3.1 Create ChatService class with Gemini API integration
    - Implement async HTTP client integration for Gemini API calls
    - Add proper request/response handling with error mapping
    - Implement retry logic with exponential backoff for transient failures
    - _Requirements: 1.2, 1.4_

  - [ ] 3.2 Add chat message processing and context handling
    - Implement message formatting for Gemini API requests
    - Add conversation context management capabilities
    - Create unit tests for message processing logic
    - _Requirements: 1.2, 1.3_

  - [ ] 3.3 Integrate ChatService with MCP tool registry
    - Create @mcp.tool() decorated chat function


    - Wire ChatService into the existing FastMCP server
    - Add proper error handling and response formatting
    - _Requirements: 1.1, 1.3, 4.3_



- [ ] 4. Implement Google Search Service
  - [ ] 4.1 Create web scraping foundation
    - Implement SearchService class with async HTTP client
    - Add User-Agent rotation and request throttling mechanisms
    - Create HTML parsing utilities using BeautifulSoup or similar
    - _Requirements: 3.1, 3.3_

  - [ ] 4.2 Implement Google search result extraction
    - Create search result parsing logic for Google's HTML structure
    - Implement result filtering and formatting
    - Add fallback handling for parsing failures
    - _Requirements: 3.1, 3.2_

  - [ ] 4.3 Add search service error handling and rate limiting
    - Implement respectful scraping with delays between requests
    - Add circuit breaker pattern for persistent failures
    - Create comprehensive error handling for scraping scenarios
    - _Requirements: 3.3, 3.4_

  - [ ] 4.4 Integrate SearchService with MCP tool registry
    - Create @mcp.tool() decorated search_web function
    - Wire SearchService into the existing FastMCP server
    - Add input validation and response formatting
    - _Requirements: 3.1, 4.3_

- [ ] 5. Enhance existing weather service integration
  - [ ] 5.1 Update weather service for consistent error handling
    - Ensure weather service follows the same error response format as new services
    - Add any missing input validation to match new standards
    - Update logging to be consistent with enhanced logging patterns
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ] 5.2 Add weather service to unified tool registry
    - Ensure weather tool is properly registered alongside new chat and search tools
    - Verify tool discovery and routing works correctly
    - Test integration with existing WhatsApp adapter
    - _Requirements: 4.1, 4.2_

- [ ] 6. Implement comprehensive error handling and logging
  - [ ] 6.1 Create unified error handling system
    - Implement consistent error response formatting across all services
    - Add error categorization and proper HTTP status mapping
    - Create error logging with appropriate detail levels
    - _Requirements: 1.4, 3.4, 4.4_

  - [ ] 6.2 Enhance logging and observability
    - Extend existing structured logging to cover new services
    - Add performance timing logs for API calls and scraping operations
    - Implement request/response logging with sensitive data masking
    - _Requirements: 5.3, 5.4_

- [ ] 7. Add configuration management and validation
  - [ ] 7.1 Extend configuration system for new services
    - Add Gemini API key configuration with validation
    - Add search service configuration options (user agent, timeouts, etc.)
    - Implement startup configuration validation with clear error messages
    - _Requirements: 5.1, 5.2_

  - [ ] 7.2 Update CLI and server startup logic
    - Extend existing CLI argument parsing for new configuration options
    - Add configuration validation to server startup process
    - Update help text and documentation for new features
    - _Requirements: 5.3, 5.4_

- [ ] 8. Create comprehensive test suite
  - [ ] 8.1 Add unit tests for new services
    - Create unit tests for ChatService with mocked Gemini API responses
    - Add unit tests for SearchService with mocked HTML parsing
    - Test error handling scenarios for all new services
    - _Requirements: 1.4, 3.4, 4.4_

  - [ ] 8.2 Add integration tests for MCP tools
    - Test chat tool end-to-end with mock Gemini responses
    - Test search_web tool with mock scraping results
    - Verify tool registration and discovery works correctly
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 8.3 Add performance and reliability tests
    - Test retry logic and timeout handling for all services
    - Add concurrent request testing for HTTP client management
    - Test graceful degradation when services are unavailable
    - _Requirements: 1.4, 3.3, 4.4_

- [ ] 9. Update documentation and examples
  - [ ] 9.1 Update README with new features and setup instructions
    - Document new environment variables and configuration options
    - Add usage examples for chat and search tools
    - Include troubleshooting guide for common setup issues
    - _Requirements: 5.1, 5.2, 5.4_

  - [ ] 9.2 Create example usage scripts
    - Create CLI examples demonstrating chat functionality
    - Add search examples with different query types
    - Create combined examples showing tool integration
    - _Requirements: 1.1, 3.1, 4.1_

- [ ] 10. Final integration and testing
  - [ ] 10.1 Test complete system integration
    - Verify all three tools (weather, chat, search) work together
    - Test existing WhatsApp adapter with new chat capabilities
    - Perform end-to-end testing with real API calls
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 10.2 Performance optimization and cleanup
    - Optimize HTTP client usage and connection pooling
    - Add any necessary caching for frequently requested data
    - Clean up any temporary code and ensure production readiness
    - _Requirements: 4.4, 5.3_