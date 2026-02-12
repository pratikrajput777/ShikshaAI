# Day 11: Mock Interview Interface - Troubleshooting Guide

---

## 🔌 WebSocket & Network

### Issue 1: Authentication Failed (403/1008)
**Symptoms**: WebSocket closes immediately after connecting with code 1008 or 403 error in console.

**Solution**:
1. Verify the JWT token is being passed correctly in the query string.
2. Check your Django `TokenAuthMiddleware` (from Day 07) to ensure it correctly extracts and validates the token from `scope['query_string']`.

### Issue 2: Laggy Transcript
**Symptoms**: Messages appear in chunks or with a delay of several seconds.

**Solution**: 
1. Check Celery task latency on the backend.
2. If using many messages, ensure you are not re-rendering the entire list on every update (use `React.memo` or specialized scrolling libraries).

---

## 🎙️ Audio & Voice issues

### Issue 3: Microphone Permission Denied
**Symptoms**: Visualizer doesn't move, and console shows `DOMException: Permission denied`.

**Solution**: 
1. Your application MUST run on HTTPS (or localhost) for the MediaDevices API to work.
2. Add a specific "Enable Microphone" button with a clear prompt if the user hasn't granted permission yet.

### Issue 4: Echo or Feedback
**Symptoms**: AI hears itself or user hears high-pitched noise.

**Solution**: 
1. Ensure the `audio` element has `echoCancellation: true` set in the constraints.
2. Recommend users use headphones during the mock interview.

---

## 📊 Evaluation Issues

### Issue 5: Evaluation Dashboard showing "N/A"
**Symptoms**: Points are 0 or no detailed feedback after interview ends.

**Solution**: 
1. Ensure the interview was formally ended (`completed: true` in DB).
2. Check Celery logs for `process_interview_evaluation` task failures.
3. Verify the Gemini API response followed the expected three-judge JSON format.
