# Test Integrity

Never weaken a test to make it pass. If a test fails, fix the code, not the test.

Specifically, do not:
- Add `.skip`, `.only`, or `xit` to bypass a failing test
- Loosen assertions (changing `toBe` to `toBeTruthy`, widening expected ranges)
- Delete a failing test without explicit user approval
- Wrap failing assertions in try/catch to swallow errors

If a test is genuinely wrong (testing outdated behavior after a deliberate change), explain what changed and why the test should be updated. Then update the assertion to match the new correct behavior — don't remove it.
