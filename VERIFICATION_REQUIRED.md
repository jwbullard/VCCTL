# VERIFICATION REQUIREMENT

## CRITICAL RULE: NO CLAIMS WITHOUT PROOF

**BEFORE making ANY claim about fixes working:**

1. ❌ **NEVER say "should work" or "will work"** - this is meaningless
2. ❌ **NEVER claim UI fixes work** without actual UI testing
3. ✅ **ONLY state what was actually verified** through concrete testing
4. ✅ **Be explicit about what was NOT tested**

## VERIFICATION LEVELS:

- **Backend Component Test**: ✅ Can verify service/model changes work
- **UI Integration Test**: ❌ Cannot verify dialog behavior in real application
- **User Manual Test**: ✅ Only way to verify real UI functionality

## REQUIRED LANGUAGE:

Instead of: "The dialog should now work correctly!"
Say: "Backend tests show the service layer now handles these fields correctly. The UI integration still needs manual testing to verify the dialog works."

## USER'S EXPLICIT REQUEST:

The user has repeatedly asked for proof/verification before claims. This reminder exists because I cannot modify my core directives but need to remember this critical requirement.

**BOTTOM LINE: If I cannot prove it works in the actual UI, I must explicitly state that limitation.**