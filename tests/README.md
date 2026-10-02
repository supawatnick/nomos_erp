# Cross-Service Tests

This directory is for tests that span application boundaries, such as:
- Web -> API critical user journeys
- LINE webhook -> API/application -> database behavior
- tenant isolation across exposed surfaces
- concurrency/load scenarios
- backup/restore verification harnesses when automated

Unit and service-local integration tests should live close to their application code.