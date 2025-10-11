# Elastic Newsroom - Cleanup TODO List

## Overview

This document categorizes cleanup opportunities by confidence level, making it easy to identify safe-to-execute actions versus those requiring careful consideration.

**Created**: 2025-10-10
**Status**: Ready for review and execution

---

## HIGH CONFIDENCE - Safe to Execute

These items can be removed or cleaned up with minimal risk.

### 1. Remove Old Test File ✅ SAFE
**File**: `tests/old_test_newsroom_workflow.py`
**Reason**: Explicitly marked as "old" in filename, superseded by newer test files
**Action**: Delete file
**Risk**: None - not imported or referenced elsewhere
**Verification**: `grep -r "old_test_newsroom_workflow" . --include="*.py" --include="*.md"`

### 2. Remove Missing Documentation Reference ✅ SAFE
**Files**: 
- `README.md` (line references)
- `agents/news_chief.py` (documentation_url field)

**Issue**: References to `docs/news-chief-agent.md` which doesn't exist
**Action**: Remove references or create minimal placeholder
**Risk**: Low - broken links only
**Options**:
  - Option A: Remove from README and news_chief.py
  - Option B: Create minimal doc with basic info about News Chief

### 3. Remove Temporary/Summary Docs ⚠️ REVIEW FIRST
**Files**:
- `LIVE_TEST_SUMMARY.md` - Summary of test suite creation
- `DETAILED_TEST_SUMMARY.md` - Summary of detailed test creation
- `tests/README_detailed_test.md` - Test documentation

**Reason**: These are development summaries/notes, not operational docs
**Action**: Archive or remove after reviewing content
**Risk**: Low - informational only, not referenced by code
**Decision needed**: Keep as historical record or remove?

### 4. Consolidate UI Documentation 📝 MODERATE
**Issue**: Multiple UI planning documents that may overlap
**Files**:
- `docs/ui-integration-plan.md` (28KB, very detailed)
- `docs/ui-mvp-summary.md` (7.9KB, MVP details)
- `docs/ui-hot-reload.md` (4.7KB, specific feature)

**Observation**: 
- `ui-integration-plan.md` is a comprehensive planning doc
- Now that UI is built, much of it is historical
- `ui-mvp-summary.md` documents what was actually built

**Action**: Consider consolidating into:
- Keep `ui-mvp-summary.md` as "what we built"
- Archive `ui-integration-plan.md` or create `docs/archive/` folder
- Keep `ui-hot-reload.md` as it documents a specific feature

**Risk**: Low - these are docs only

### 5. JavaScript Test Files Status 🔍 NEEDS INVESTIGATION
**Files**:
- `tests/test_researcher_workflow.js`
- `tests/test_researcher_active_workflow.js`
- `tests/test_researcher_current_status.js`
- `tests/test_researcher_status.js`

**Issue**: 4 JS test files exist but unclear if they're actively used
**Action**: 
1. Check if `package.json` references them in test scripts
2. Verify if they're part of any CI/CD
3. Check if they test functionality not covered by Python tests

**Risk**: Medium - need to verify purpose before removing
**Investigation needed**: Are these for the React UI or legacy?

---

## MEDIUM CONFIDENCE - Requires Review

These items likely can be cleaned up but require verification of usage.

### 6. React UI vs Mesop UI 🎨 IMPORTANT DECISION
**Situation**: Two UI implementations exist
- `ui/` - Mesop-based UI (Python, Mesop framework)
- `react-ui/` - React-based UI (JavaScript, React framework)

**Questions**:
1. Which UI is actively used/preferred?
2. Are both maintained or is one deprecated?
3. Do they serve different purposes?

**Action**: Determine which UI is the "official" one
- If Mesop only: Archive or remove `react-ui/`
- If React only: Archive or remove `ui/`
- If both active: Document why and when to use each

**Risk**: High if wrong one removed - need clear answer from maintainer

### 7. Multiple Test Files - Consolidation Opportunity 🧪
**Files**:
- `tests/test_newsroom_workflow_detailed.py`
- `tests/test_newsroom_workflow_live.py`
- `tests/test_newsroom_workflow_advanced.py`
- `tests/test_newsroom_workflow_comprehensive.py`

**Issue**: Multiple workflow test files with overlapping functionality
**Action**: 
1. Review what each test covers
2. Identify redundancy
3. Consolidate or clearly document purpose of each

**Benefit**: Easier to maintain, faster test runs
**Risk**: Medium - need to ensure no test coverage is lost

### 8. Archivist Test Files 📚
**Files**:
- `tests/test_archivist.py`
- `tests/test_archivist_retry.py`

**Action**: Verify these are still relevant given current Archivist integration
**Risk**: Low - can keep if tests are passing and useful

### 9. Test Runner Scripts 🏃
**Files**:
- `run_detailed_test.py`
- `run_live_test.py`
- `demo_workflow.py`

**Question**: Are these used regularly or can test commands be simplified?
**Action**: Document purpose or consolidate into fewer scripts
**Risk**: Low - convenience scripts

---

## LOW CONFIDENCE - Careful Consideration Required

These items require deep understanding of the codebase.

### 10. Documentation Overlap Review 📖
**Files to review**:
- `docs/code-quality-improvements.md` - Documents past refactoring
- `docs/configuration-guide.md` - Environment setup
- `docs/elasticsearch-schema.md` - ES index details
- `docs/archivist-integration.md` - Archivist setup

**Question**: Is all information in these docs still current and accurate?
**Action**: 
1. Review each doc for accuracy
2. Update outdated information
3. Remove sections about deprecated features

**Risk**: Medium - these are reference docs

### 11. JSON Files Status 📋
**Files**:
- `docs/agent-relationships.json` (16KB)
- `docs/elasticsearch-index-mapping.json` (4.3KB)
- `archivist_agent_card.json` (root level)

**Action**: Verify these are used by code or just documentation
**Risk**: Low - if not referenced by code, likely safe to move to docs/

### 12. Root-Level Text Files 📄
**Files**:
- `archivist_test_response.txt`

**Action**: Check if this is a test fixture or temporary file
**Risk**: Low - likely can be moved to tests/ or removed

---

## SUMMARY BY ACTION TYPE

### Quick Wins (Can do now)
1. ✅ Delete `tests/old_test_newsroom_workflow.py`
2. ✅ Fix missing `docs/news-chief-agent.md` references
3. ✅ Remove or archive test summary docs (LIVE_TEST_SUMMARY.md, etc.)

### Requires Decision (Ask maintainer)
4. 🎨 UI Strategy: Keep react-ui, ui, or both?
5. 🔍 JavaScript tests: Still needed or legacy?

### Requires Analysis (Some investigation needed)
6. 🧪 Consolidate redundant test files
7. 📖 Update documentation accuracy
8. 📋 Verify JSON/text file usage

---

## EXECUTION CHECKLIST

### Phase 1: Immediate Safe Actions
- [ ] Delete `tests/old_test_newsroom_workflow.py`
- [ ] Fix `docs/news-chief-agent.md` references in:
  - [ ] README.md
  - [ ] agents/news_chief.py
- [ ] Move test summaries to archive or delete:
  - [ ] LIVE_TEST_SUMMARY.md
  - [ ] DETAILED_TEST_SUMMARY.md
  - [ ] tests/README_detailed_test.md

### Phase 2: Documentation Cleanup
- [ ] Review and consolidate UI docs:
  - [ ] Keep ui-mvp-summary.md
  - [ ] Archive ui-integration-plan.md
  - [ ] Keep ui-hot-reload.md
- [ ] Update code-quality-improvements.md if outdated
- [ ] Verify elasticsearch-schema.md is current

### Phase 3: Test Consolidation
- [ ] Analyze overlap in workflow test files
- [ ] Document purpose of each test file
- [ ] Consolidate where appropriate
- [ ] Verify JS test files usage

### Phase 4: UI Strategy
- [ ] Decide on UI approach (React vs Mesop)
- [ ] Archive/remove unused UI implementation
- [ ] Update README to reflect active UI

---

## ESTIMATED IMPACT

### Files to Delete (High Confidence)
- `tests/old_test_newsroom_workflow.py`
- `LIVE_TEST_SUMMARY.md`
- `DETAILED_TEST_SUMMARY.md`
- `tests/README_detailed_test.md`

**Lines saved**: ~1,000+ lines

### Files to Review/Consolidate (Medium Confidence)
- 4 JavaScript test files (if unused)
- Multiple Python workflow test files
- UI planning documentation

**Potential lines saved**: ~2,000+ lines

### Files to Update (Low Risk)
- README.md (fix broken links)
- agents/news_chief.py (fix documentation URL)
- Various docs (accuracy updates)

**Lines changed**: ~10-20 lines

---

## NOTES

### Why This Matters
- **Maintainability**: Less code = easier to maintain
- **Onboarding**: New contributors aren't confused by old/unused files
- **Performance**: Fewer files to search through
- **Clarity**: Clear what's active vs historical

### Best Practices Going Forward
1. Mark old files with `old_` or `deprecated_` prefix
2. Use `archive/` folders for historical docs
3. Delete test files when superseded, don't just rename
4. Keep documentation in sync with code
5. Regular cleanup every few months

---

## QUESTIONS FOR MAINTAINER

1. **UI Strategy**: Which UI should be the primary one (react-ui or ui)?
2. **Test Files**: Should we consolidate the multiple workflow test files?
3. **JS Tests**: Are the JavaScript test files still needed?
4. **Documentation**: Should we archive planning docs now that features are built?
5. **news-chief-agent.md**: Should we create this doc or just remove references?

---

## NEXT STEPS

1. Review this TODO list
2. Make decisions on "Requires Decision" items
3. Execute Phase 1 (safe actions)
4. Plan Phase 2-4 based on decisions

