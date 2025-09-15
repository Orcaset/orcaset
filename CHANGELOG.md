# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2a1] - 2025-09-15

### Added
- `get_nodes` utility function to retrieve all descendant nodes recursively
- Additional tests for balance series average method lazy evaluation

## [0.2.1a1] - 2025-09-06

### Added
- Average method to balance series
- YF (Year Fraction) type alias

### Changed
- Updated README examples

## [0.2.0a1] - 2025-08-18

### Added
- Accrual series with rebase functionality and comprehensive tests
- Math operators for accrual series operations
- YF (Year Fraction) type with NotImplementedError for incompatible combinations
- Tests for Payment and Balance series
- Additional dunder operators to BalanceSeriesBase
- Comprehensive test coverage for Accrual lazy operations

### Changed
- Update Accrual, Balance, and Payment classes to accept thunks as values to delay execution in the case of circular event-driven models
- Updated the Accrual, Balance, and Payment base series classes to lazily handle items without executing the underlying `value`s
- Updated accrual series accrue method implementation
- Removed look aheads in series combinators

## [0.1.2] - 2025-07-25

### Added
- Support for Python 3.12

### Changed
- Migrated project structure and configuration

## [0.1.1] - Initial Release