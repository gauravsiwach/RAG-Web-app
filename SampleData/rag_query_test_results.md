# RAG Query Test Results

**PDF Tested:** React Quick Start Documentation  
**Date:** March 22, 2026  
**Pipeline:** Query Translation (Multi-Query + Step-Back + Sub-Query) + Relevance Threshold Filtering

---

## Test Results

| #  | Question                                       | Result                      |
|----|------------------------------------------------|-----------------------------|
| 1  | What is a React component?                     | ✅ Found                     |
| 2  | What is JSX in React?                          | ✅ Found                     |
| 3  | How does useState work?                        | ✅ Found                     |
| 4  | What is lifting state up?                      | ✅ Found                     |
| 5  | How to render lists in React?                  | ✅ Found                     |
| 6  | How can we reuse UI parts in React apps?       | 🔄 Found (with translation) |
| 7  | How do you show dynamic values in UI in React? | 🔄 Found (with translation) |
| 8  | How does clicking a button update UI?          | 🔄 Found (with translation) |
| 9  | How to keep multiple components in sync?       | 🔄 Found (with translation) |
| 10 | How to display multiple items dynamically?     | 🔄 Found (with translation) |
| 11 | What is Redux?                                 | ❌ Not found                 |
| 12 | What is React Router?                          | ❌ Not found                 |
| 13 | What is Next.js?                               | ❌ Not found                 |
| 14 | What is useEffect hook?                        | ❌ Not found                 |
| 15 | What is server-side rendering?                 | ❌ Not found                 |

---

## Result Legend

| Symbol | Meaning |
|--------|---------|
| ✅ Found | Directly matched without query translation |
| 🔄 Found (with translation) | Only found after multi-query / step-back / sub-query translation |
| ❌ Not found | Topic not covered in the PDF document |

---

## Summary

- **Direct matches:** 5 / 15 (33%)
- **Found via translation:** 5 / 15 (33%)
- **Not in document:** 5 / 15 (33%)
- **Total retrieval success:** 10 / 15 (67%)

---

## Notes

- Questions 11–15 are correctly returning "not found" — these topics (Redux, React Router, Next.js, useEffect, SSR) are not covered in the React Quick Start PDF.
- Questions 6–10 demonstrate the value of query translation — these would have failed without the Multi-Query / Step-Back / Sub-Query pipeline.
- The relevance threshold (0.4) is working correctly to filter out unrelated content.
